from __future__ import annotations

import re

from .config import SCHOOL_TERM_START
from .rag import rag_answer
from .retriever import TfidfRetriever, build_retriever
from .tools import (
    calculate_gpa,
    calculate_gpa_detail,
    get_contact_info,
    get_current_week,
    get_service_link,
    get_term_progress,
    list_toolbox,
)


LOCAL_TOOL_META = {
    "provider": "本地工具",
    "model": None,
    "used": False,
    "ok": True,
    "error": None,
    "latency_ms": 0,
}


def greeting_answer() -> str:
    return (
        "你好，我是校园生活百事通助手。我主要帮你解决安徽交通职业技术学院的校园生活问题，例如：\n"
        "1. 请假、病假、事假、销假怎么操作。\n"
        "2. 奖学金、助学金申请条件和标准。\n"
        "3. 宿舍报修、一卡通挂失补办、选课退选等校园事务。\n"
        "4. 学校官网入口、招生电话、校区地址、校历和教务处入口。\n"
        "5. 绩点计算、当前教学周、学期进度等常用工具。\n\n"
        "你也可以先问“一卡通丢了怎么办？”，再继续追问“怎么挂失？”。"
    )


def week_challenge_answer() -> str:
    current_week = get_current_week()
    return (
        f"我这里按系统配置的本学期开始日期 {SCHOOL_TERM_START} 计算，{current_week}\n"
        "如果你看到班级通知或学校校历写的是第17周，可能是因为教学周起算规则、调休或校历安排和系统配置不一致。"
        "这种情况建议以学校官网校历、教务通知或辅导员通知为准。"
    )


class CampusAgent:
    def __init__(self, retriever: TfidfRetriever | None = None) -> None:
        self.retriever = retriever or build_retriever()
        self.conversation_history: list[dict[str, str]] = []
        self.last_topic: str | None = None

    def chat_detail(self, user_input: str, use_llm: bool = True) -> dict[str, object]:
        raw_question = user_input.strip()
        question = self._resolve_follow_up(raw_question)
        self.conversation_history.append({"role": "user", "content": question})

        if self._is_week_challenge_query(raw_question):
            payload = {
                "answer": week_challenge_answer(),
                "context": "",
                "results": [],
                "llm": LOCAL_TOOL_META,
            }
        elif self._is_greeting_query(question):
            payload = {
                "answer": greeting_answer(),
                "context": "",
                "results": [],
                "llm": LOCAL_TOOL_META,
            }
        elif self._is_toolbox_query(question):
            payload = {
                "answer": list_toolbox(),
                "context": "",
                "results": [],
                "llm": LOCAL_TOOL_META,
            }
        elif self._is_term_progress_query(question):
            payload = {
                "answer": get_term_progress(),
                "context": "",
                "results": [],
                "llm": LOCAL_TOOL_META,
            }
        elif self._is_week_query(question):
            payload = {
                "answer": get_current_week(),
                "context": "",
                "results": [],
                "llm": LOCAL_TOOL_META,
            }
        elif self._is_gpa_detail_query(question):
            payload = {
                "answer": calculate_gpa_detail(question),
                "context": "",
                "results": [],
                "llm": LOCAL_TOOL_META,
            }
        elif self._is_gpa_query(question):
            payload = {
                "answer": calculate_gpa(question),
                "context": "",
                "results": [],
                "llm": LOCAL_TOOL_META,
            }
        elif self._is_link_query(question):
            payload = {
                "answer": get_service_link(question),
                "context": "",
                "results": [],
                "llm": LOCAL_TOOL_META,
            }
        elif self._is_contact_query(question):
            payload = {
                "answer": get_contact_info(question),
                "context": "",
                "results": [],
                "llm": LOCAL_TOOL_META,
            }
        else:
            payload = rag_answer(question, self.retriever, use_llm=use_llm)

        response = str(payload["answer"])
        self._update_topic(question, response)
        self.conversation_history.append({"role": "assistant", "content": response})
        self.conversation_history = self.conversation_history[-10:]
        return payload

    def chat(self, user_input: str, use_llm: bool = True) -> str:
        return str(self.chat_detail(user_input, use_llm=use_llm)["answer"])

    @staticmethod
    def _is_week_query(text: str) -> bool:
        return bool(re.search(r"(第?几周|校历|教学周|当前周|现在.*周)", text))

    def _is_week_challenge_query(self, text: str) -> bool:
        if self.last_topic != "教学周":
            return False
        has_challenge = any(word in text for word in ["不是", "不对", "错", "算错", "应该", "不是第"])
        mentions_week = "周" in text or bool(re.search(r"第[一二三四五六七八九十0-9]+", text))
        return has_challenge and mentions_week

    @staticmethod
    def _is_term_progress_query(text: str) -> bool:
        return bool(re.search(r"(学期进度|第几天|本周第几天|今天.*学期)", text))

    @staticmethod
    def _is_gpa_query(text: str) -> bool:
        lower_text = text.lower()
        has_score = bool(re.search(r"\d{2,3}", text))
        return "gpa" in lower_text or "绩点计算" in text or ("绩点" in text and has_score)

    @staticmethod
    def _is_gpa_detail_query(text: str) -> bool:
        return "绩点明细" in text or "绩点详情" in text

    @staticmethod
    def _is_link_query(text: str) -> bool:
        return any(word in text for word in ["入口", "官网", "网址", "链接", "在哪里看", "哪里看"]) and any(
            word in text for word in ["教务", "校历", "财务", "缴费", "图书馆", "办事大厅", "AI平台", "官网"]
        )

    @staticmethod
    def _is_contact_query(text: str) -> bool:
        return any(word in text for word in ["电话", "联系方式", "地址", "校区", "联系"])

    @staticmethod
    def _is_toolbox_query(text: str) -> bool:
        return any(
            word in text
            for word in [
                "你会什么",
                "有哪些工具",
                "工具列表",
                "能做什么",
                "功能列表",
                "能帮我",
                "可以帮我",
                "解决什么问题",
                "有什么功能",
                "怎么使用",
                "使用说明",
            ]
        )

    @staticmethod
    def _is_greeting_query(text: str) -> bool:
        normalized = re.sub(r"[\s，。！？!?,.～~]", "", text.strip().lower())
        return normalized in {
            "你好",
            "你好啊",
            "您好",
            "您好啊",
            "hello",
            "hi",
            "嗨",
            "在吗",
            "在不在",
            "你是谁",
            "介绍一下",
        }

    def _resolve_follow_up(self, question: str) -> str:
        if not self.last_topic:
            return question
        has_topic = any(
            topic in question
            for topic in ["一卡通", "校园卡", "饭卡", "餐卡", "请假", "奖学金", "报修", "宿舍", "选课", "绩点", "校历", "教学周"]
        )
        if has_topic:
            return question

        follow_up_patterns = [
            "怎么挂失",
            "怎么补办",
            "需要什么材料",
            "在哪里办理",
            "怎么申请",
            "怎么退",
            "怎么销假",
            "具体怎么做",
            "那怎么办",
            "然后呢",
            "不是",
            "不对",
            "算错",
            "应该是",
        ]
        if any(pattern in question for pattern in follow_up_patterns):
            return f"{self.last_topic}，{question}"
        return question

    def _update_topic(self, question: str, response: str) -> None:
        if self._is_greeting_query(question) or self._is_toolbox_query(question):
            return
        if response.startswith(("可以聊", "不客气", "这个问题我可以", "听起来", "可以的。一般建议")):
            return
        topic_keywords = {
            "一卡通": ["一卡通", "校园卡", "饭卡", "餐卡", "挂失", "补办"],
            "请假": ["请假", "病假", "事假", "销假", "发烧", "生病", "感冒", "身体不适", "不舒服", "校医院"],
            "奖学金": ["奖学金", "励志奖学金", "资助"],
            "报修": ["报修", "设施", "电路", "空调"],
            "宿舍": ["宿舍", "熄灯", "大门"],
            "选课": ["选课", "退选", "退课"],
            "绩点": ["绩点", "GPA"],
            "教学周": ["第几周", "教学周", "本学期第", "校历", "当前周"],
        }
        text = f"{question}\n{response}"
        for topic, keywords in topic_keywords.items():
            if any(keyword in text for keyword in keywords):
                self.last_topic = topic
                return


def agent_chat(user_input: str, use_llm: bool = True) -> str:
    return CampusAgent().chat(user_input, use_llm=use_llm)
