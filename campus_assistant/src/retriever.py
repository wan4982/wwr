from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from .config import DATA_FILE, DEFAULT_TOP_K, VECTOR_DIR
from .data_loader import CampusRecord, load_records


TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fff]|[a-zA-Z0-9]+")

QUERY_EXPANSIONS = {
    "发烧": "生病 病假 请假 医院 校医院 证明",
    "生病": "病假 请假 医院 校医院 证明",
    "感冒": "生病 病假 请假 医院",
    "请假": "病假 事假 销假 特殊情况 今日校园 证明",
    "病假": "请假 校医院 证明 今日校园",
    "事假": "请假 今日校园 事由 附件",
    "销假": "请假结束 请假记录 继续请假",
    "灯坏": "宿舍 报修 宿管 后勤 设施",
    "灯": "宿舍 熄灯 关灯 23:30 06:00",
    "熄灯": "宿舍 熄灯 23:30 06:00 安静",
    "大门": "宿舍 大门 开门 关门 6:30 23:30",
    "报修": "宿舍 设施 电路 空调 网上办事大厅 后勤服务",
    "设施": "宿舍 报修 后勤服务",
    "空调": "宿舍 报修 后勤",
    "丢": "丢失 挂失 补办 一卡通 校园卡",
    "一卡通": "校园卡 挂失 补办 今日校园",
    "校园卡": "一卡通 挂失 补办 今日校园",
    "饭卡": "一卡通 校园卡 挂失 补办 充值 今日校园",
    "餐卡": "一卡通 校园卡 挂失 补办 充值 今日校园",
    "绩点": "奖学金 GPA 平均绩点 条件",
    "奖学金": "国家奖学金 国家励志奖学金 申请条件 奖励标准",
    "退课": "退选 选课 教务管理系统",
    "退选": "退课 选课 教务管理系统",
    "食堂": "餐厅 吃饭 就餐 校园生活 校区 后勤",
    "餐厅": "食堂 吃饭 就餐 校园生活 校区 后勤",
    "吃饭": "食堂 餐厅 就餐 校园生活 校区 后勤",
    "超市": "便利店 校园生活 宿舍区 后勤",
    "快递": "取件 驿站 快递点 校园生活 宿舍区",
    "打印": "复印 图文店 校园生活 教学楼",
    "医务室": "校医院 就医 身体不适 校区 辅导员",
    "社团": "百团大战 社团招新 第二课堂 素质拓展 学分",
    "百团": "社团 招新 百团大战 报名",
    "第二课堂": "社团 活动 素质拓展 学分",
    "体测": "体育测试 评优评奖 奖学金 毕业 800米 立定跳远",
    "四六级": "英语四级 英语六级 报名 教务处 通知 3月 9月",
    "四级": "四六级 英语四级 报名 教务处",
    "六级": "四六级 英语六级 报名 教务处",
    "空教室": "自习 教务系统 图书馆 研讨室 教学楼",
    "培养方案": "专业培养方案 教务处 学分 必修课 毕业",
    "诈骗": "网络诈骗 防骗 刷单 校园贷 保卫处 报警",
    "收费通知": "辅导员 收费 转账 缴费 官方渠道 防骗",
    "推销": "陌生人 宿舍 推销 宿管 保卫处 个人信息",
    "交通事故": "报警 受伤 就医 辅导员 现场 交警",
    "宠物": "宿舍 饲养 携带 宠物 禁止",
    "电煮锅": "宿舍 大功率 违规电器 热得快 电暖器 火灾",
    "热得快": "宿舍 大功率 违规电器 电煮锅 电暖器",
    "插排": "宿舍 用电安全 合格插排 私拉乱接 电源",
    "漏水": "水管 宿舍 报修 后勤服务 宿管",
    "水管": "漏水 宿舍 报修 后勤服务 宿管",
    "室友": "宿舍 作息 宿舍公约 辅导员 调换宿舍",
    "遥控器": "宿舍 空调 遥控器 宿管 备用遥控器",
    "窗纱": "宿舍 报修 后勤 维修",
    "学生证": "办理 补办 学生处 教务处 工本费",
    "公交卡": "学生公交卡 办理 辅导员 学工处",
    "充值": "校园卡 一卡通 今日校园 充值 服务中心",
}


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


def expand_query(query: str) -> str:
    additions = [words for key, words in QUERY_EXPANSIONS.items() if key in query]
    if not additions:
        return query
    return f"{query} {' '.join(additions)}"


class TfidfRetriever:
    """A lightweight local vector retriever that works without network access."""

    def __init__(self, records: list[CampusRecord]) -> None:
        self.records = records
        self.doc_tokens = [tokenize(record.searchable_text) for record in records]
        self.idf = self._build_idf(self.doc_tokens)
        self.doc_vectors = [self._vectorize(tokens) for tokens in self.doc_tokens]

    @staticmethod
    def _build_idf(doc_tokens: list[list[str]]) -> dict[str, float]:
        doc_count = len(doc_tokens)
        document_frequency: Counter[str] = Counter()
        for tokens in doc_tokens:
            document_frequency.update(set(tokens))
        return {
            token: math.log((doc_count + 1) / (frequency + 1)) + 1
            for token, frequency in document_frequency.items()
        }

    def _vectorize(self, tokens: list[str]) -> dict[str, float]:
        counts = Counter(tokens)
        total = max(len(tokens), 1)
        return {
            token: (count / total) * self.idf.get(token, 0.0)
            for token, count in counts.items()
        }

    @staticmethod
    def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
        if not left or not right:
            return 0.0
        common = set(left) & set(right)
        numerator = sum(left[token] * right[token] for token in common)
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return numerator / (left_norm * right_norm)

    def search(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        category: str | None = None,
    ) -> list[tuple[CampusRecord, float]]:
        query_vector = self._vectorize(tokenize(expand_query(query)))
        query_tokens = set(tokenize(query))
        scored: list[tuple[CampusRecord, float]] = []

        for record, doc_vector in zip(self.records, self.doc_vectors):
            if category and record.category != category:
                continue

            score = self._cosine(query_vector, doc_vector)
            question_tokens = set(tokenize(record.question))
            answer_tokens = set(tokenize(record.answer))

            if query_tokens and question_tokens:
                score += 0.35 * (len(query_tokens & question_tokens) / len(query_tokens))
            if query_tokens and answer_tokens:
                score += 0.12 * (len(query_tokens & answer_tokens) / len(query_tokens))
            if query.strip() == record.question.strip():
                score += 1.0
            if category and record.category == category:
                score += 0.2

            scored.append((record, score))

        scored.sort(key=lambda item: item[1], reverse=True)
        return [item for item in scored[:top_k] if item[1] > 0]

    def category_records(self, category: str) -> list[CampusRecord]:
        return [record for record in self.records if record.category == category]

    def persist(self, directory: Path = VECTOR_DIR) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        payload = {
            "data_file": str(DATA_FILE),
            "record_count": len(self.records),
            "idf": self.idf,
            "records": [asdict(record) for record in self.records],
        }
        output = directory / "tfidf_index.json"
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output


def build_retriever() -> TfidfRetriever:
    return TfidfRetriever(load_records())


def build_and_save_index() -> Path:
    return build_retriever().persist()
