from __future__ import annotations

import os
import time

from dotenv import load_dotenv

from .config import BASE_DIR
from .prompt_templates import RAG_PROMPT
from .retriever import TfidfRetriever, build_retriever


load_dotenv(BASE_DIR / ".env")


LOCAL_RAG_META: dict[str, object] = {
    "provider": "本地RAG",
    "model": None,
    "used": False,
    "ok": False,
    "error": None,
    "latency_ms": 0,
}

MIN_RELIABLE_SCORE = 0.5


def _format_context(results: list[tuple[object, float]]) -> str:
    lines = []
    for record, score in results:
        lines.append(
            f"- 分类：{record.category}\n"
            f"  问题：{record.question}\n"
            f"  规则：{record.answer}\n"
            f"  来源：{record.source}\n"
            f"  相似度：{score:.3f}"
        )
    return "\n".join(lines)


def _is_general_leave_question(question: str) -> bool:
    return "请假" in question and not any(
        keyword in question for keyword in ["病假", "事假", "销假", "报到", "缺课"]
    )


def _is_campus_scope_question(question: str) -> bool:
    campus_keywords = [
        "学校",
        "学院",
        "校园",
        "官网",
        "校历",
        "教务",
        "选课",
        "退选",
        "退课",
        "选错",
        "错课",
        "课程",
        "成绩",
        "绩点",
        "gpa",
        "请假",
        "病假",
        "事假",
        "销假",
        "发烧",
        "生病",
        "感冒",
        "身体不适",
        "不舒服",
        "头疼",
        "咳嗽",
        "肚子疼",
        "校医院",
        "辅导员",
        "奖学金",
        "助学金",
        "资助",
        "宿舍",
        "寝室",
        "熄灯",
        "报修",
        "空调",
        "电路",
        "一卡通",
        "校园卡",
        "饭卡",
        "餐卡",
        "挂失",
        "补办",
        "招生",
        "电话",
        "地址",
        "校区",
        "图书馆",
        "食堂",
        "餐厅",
        "吃饭",
        "就餐",
        "超市",
        "便利店",
        "快递",
        "取件",
        "打印",
        "复印",
        "医务室",
        "财务",
        "缴费",
        "办事大厅",
        "社团",
        "百团大战",
        "第二课堂",
        "素质拓展",
        "安全",
        "诈骗",
        "防骗",
        "推销",
        "陌生人",
        "交通事故",
        "收费通知",
        "体测",
        "体育课",
        "四六级",
        "英语四级",
        "英语六级",
        "空教室",
        "自习",
        "培养方案",
        "专业培养",
        "选修课",
        "补选",
        "宠物",
        "电煮锅",
        "热得快",
        "电暖器",
        "大功率",
        "插排",
        "水管",
        "漏水",
        "走廊",
        "室友",
        "遥控器",
        "窗纱",
        "学生证",
        "公交卡",
        "银行",
        "充值",
        "校医院",
        "医保卡",
        "安徽交通职业技术学院",
    ]
    return any(keyword.lower() in question.lower() for keyword in campus_keywords)


def _general_question_answer(question: str) -> str:
    normalized = question.strip()
    if any(word in normalized for word in ["安慰", "陪我", "难受", "委屈", "崩溃", "想哭", "不开心", "心累"]):
        return (
            "当然可以。先别急着把自己撑得很满，你现在愿意说出来，已经是在照顾自己了。\n"
            "可以先做两件很小的事：慢慢呼吸几次，喝点水，或者把让你难受的事情写成一两句话。"
            "如果你愿意，也可以继续跟我说发生了什么，我会先听你说；如果这件事和请假、宿舍、课程或找辅导员有关，我也可以帮你整理下一步怎么处理。"
        )
    if any(word in normalized for word in ["学习", "复习", "考试", "计划", "时间管理", "效率"]):
        return (
            "可以的。一般建议先把目标拆成小任务，再按轻重缓急安排时间。"
            "比如每天固定一段时间复习课堂内容，临近考试前整理错题和重点。"
            "我更擅长校园事务查询；如果你想结合学校安排，也可以问我校历、教学周、选课或成绩相关问题。"
        )
    if any(word in normalized for word in ["心情", "压力", "焦虑", "难过", "烦"]):
        return (
            "听起来你可能有点累。先允许自己缓一缓，不用马上把所有事情都处理好。"
            "可以把具体困扰写下来，区分哪些能马上处理、哪些需要找人帮忙。"
            "如果压力持续影响学习和生活，建议及时和辅导员、家人或学校心理健康相关老师沟通。"
            "校园事务方面，我也可以继续帮你查请假、宿舍、选课等问题。"
        )
    if any(word in normalized for word in ["谢谢", "感谢", "好的", "好滴", "明白", "知道了"]):
        return "不客气。后面有请假、选课、宿舍、一卡通这些校园问题，也可以继续问我。"
    if any(word in normalized for word in ["为什么", "怎么回事", "不对", "不是", "真的吗"]):
        return "你可以把具体是哪一条信息、哪个办理事项或哪次回答不对告诉我，我会按知识库和已有规则再帮你核对一遍。"
    if any(word in normalized for word in ["月球", "月亮"]):
        return "月球是地球唯一的天然卫星，离地球平均约38.4万公里。这个问题不属于校园事务，但简单科普我也可以回答；如果你是想问学校天文、社团或课程相关内容，可以再具体说一下。"
    return "可以聊。这个问题不属于校园事务，我可以先简单回应；如果你想办具体校园事项，我对请假、选课、宿舍、一卡通、奖学金、校历这些问题最有把握。"


def _campus_unknown_answer() -> str:
    return (
        "这个学校相关问题在当前知识库里没有找到明确依据。"
        "为了避免误导你，建议咨询辅导员或对应业务部门确认。"
        "你也可以把问题说得更具体一些，例如说明事项类型、办理入口、材料或时间要求，我会再帮你查一遍。"
    )


def _find_by_question(retriever: TfidfRetriever, question: str):
    for record in retriever.records:
        if record.question == question:
            return record
    return None


def _is_health_leave_question(question: str) -> bool:
    return any(
        keyword in question
        for keyword in [
            "发烧",
            "生病",
            "感冒",
            "身体不适",
            "不舒服",
            "头疼",
            "头痛",
            "咳嗽",
            "肚子疼",
            "肚子痛",
            "校医院",
            "看病",
            "去医院",
        ]
    )


def _health_leave_answer(retriever: TfidfRetriever) -> tuple[str, list[tuple[object, float]]]:
    wanted = ["怎么请病假？", "请假结束后需要做什么？", "特殊情况如何请假？"]
    records = [record for item in wanted if (record := _find_by_question(retriever, item))]
    if not records:
        records = [record for record, _score in retriever.search("发烧 生病 病假 请假 校医院 辅导员", top_k=3, category="请假")]

    answer = (
        "如果你发烧或身体不舒服，建议先按“生病/病假”的方向处理：\n"
        "1. 先关注身体情况，必要时及时去校医院或正规医院就医；症状明显、持续高烧或身体很难受时，不要硬撑。\n"
        "2. 如果会影响上课、晚自习、返校或离校，需要尽快联系辅导员说明情况。\n"
        "3. 需要请假时，在“今日校园”APP进入学生服务，提交学生请假申请，请假类型选择病假，填写起止时间和病假原因。\n"
        "4. 按辅导员要求上传证明材料，例如校医院或医院证明；3天以上病假通常需要附证明材料。\n"
        "5. 如果情况比较急，可以先电话联系辅导员说明，后续再按要求补办请假手续。\n"
        "6. 请假结束后，记得在“今日校园”APP进入已通过的请假记录完成销假。\n\n"
        "如果你只是想表达“我好像发烧了”，我会优先建议你先就医、联系辅导员，再按病假流程处理。"
    )

    sources = []
    for record in records:
        source = str(record.source).split("[reference")[0].strip()
        if source and source not in sources:
            sources.append(source)
    if sources:
        answer += f"\n\n参考来源：{'；'.join(sources)}"
    return answer, [(record, 1.0) for record in records]


def _is_course_drop_question(question: str) -> bool:
    return any(keyword in question for keyword in ["选错", "错课", "退选", "退课"]) and any(
        keyword in question for keyword in ["课", "课程", "选课", "能退", "可以退"]
    )


def _is_dorm_assignment_question(question: str) -> bool:
    return any(keyword in question for keyword in ["选宿舍", "选寝室", "分宿舍", "分寝室", "宿舍怎么选", "寝室怎么选"])


def _dorm_assignment_answer() -> tuple[str, list[tuple[object, float]]]:
    return (
        "当前知识库没有收录“宿舍选择/分配”的明确规则，所以不能直接说可以线上选宿舍或给出固定入口。"
        "这类安排通常以学院迎新通知、辅导员通知或宿管部门安排为准。建议你先查看班级群/迎新通知，"
        "如果没有说明，再咨询辅导员确认是否可以自选、是否按专业班级统一分配，以及需要在什么时间办理。",
        [],
    )


def _is_card_question(question: str) -> bool:
    return any(keyword in question for keyword in ["一卡通", "校园卡", "饭卡", "餐卡"]) and any(
        keyword in question for keyword in ["丢", "丢了", "挂失", "补办", "充值", "余额", "怎么办"]
    )


def _card_answer(question: str, retriever: TfidfRetriever) -> tuple[str, list[tuple[object, float]]] | None:
    if any(keyword in question for keyword in ["充值", "余额", "充钱"]):
        wanted_question = "校园卡怎么充值？"
    elif any(keyword in question for keyword in ["挂失", "丢", "丢了", "不见"]):
        wanted_question = "一卡通丢了怎么办？"
    elif "补办" in question:
        wanted_question = "一卡通补办需要什么材料？"
    else:
        wanted_question = "一卡通丢了怎么办？"

    record = _find_by_question(retriever, wanted_question)
    if not record:
        return None

    results = [(record, 1.0)]
    if wanted_question == "一卡通丢了怎么办？":
        extra_questions = ["一卡通怎么挂失？", "一卡通补办需要什么材料？"]
        results.extend(
            (extra_record, 1.0)
            for item in extra_questions
            if (extra_record := _find_by_question(retriever, item))
        )
        answer = (
            "饭卡一般就是校园卡/一卡通。丢了建议先挂失再补办：\n"
            "1. 先在“今日校园”APP的校园卡界面办理卡挂失，避免余额被他人使用。\n"
            "2. 也可以前往一卡通服务中心办理挂失和补办。\n"
            "3. 补办时携带本人有效身份证件，例如身份证或学生证；若学校有自助补卡机，也可按机器提示办理。\n"
            "4. 如果卡里有余额或交易异常，补办时一并向服务中心确认余额转移和消费记录。\n\n"
            "参考来源：一卡通-校园卡管理规定；一卡通-校园一卡通使用指南；一卡通-校园卡补办流程"
        )
        return answer, results

    answer = f"{record.answer}\n\n参考来源：一卡通-{record.source}"
    return answer, results


def _is_scholarship_review_question(question: str) -> bool:
    return "奖学金" in question and any(
        keyword in question for keyword in ["怎么评", "如何评", "评定", "评审", "条件", "申请", "要求"]
    )


def _is_scholarship_grant_comparison_question(question: str) -> bool:
    return "奖学金" in question and "助学金" in question and any(
        keyword in question for keyword in ["区别", "不同", "一样", "差别", "有什么"]
    )


def _scholarship_grant_comparison_answer(retriever: TfidfRetriever) -> tuple[str, list[tuple[object, float]]]:
    wanted = [
        "国家励志奖学金奖励标准是多少？",
        "国家励志奖学金申请条件是什么？",
        "国家励志奖学金如何申请？",
        "学院有哪些校内资助形式？",
    ]
    records = [record for item in wanted if (record := _find_by_question(retriever, item))]
    if not records:
        records = [
            record
            for record, _score in retriever.search("国家励志奖学金 助学金 资助 家庭经济困难", top_k=4, category="奖学金")
        ]

    answer = (
        "奖学金和助学金的侧重点不一样：\n"
        "1. 奖学金偏“奖励优秀”。例如国家奖学金主要面向特别优秀学生；国家励志奖学金则同时看家庭经济困难和学习、综合表现。\n"
        "2. 助学金偏“帮扶困难”。它通常更侧重家庭经济困难认定和资助需求，用来支持学生基本学习生活。\n"
        "3. 从知识库已有资料看，国家励志奖学金标准为每人每年5000元，要求二年级以上（含二年级）、品学兼优、家庭经济困难，且必修课程没有不及格科目。\n"
        "4. 当前知识库没有收录“国家助学金”的具体等级、金额和申请条件，所以不能把助学金金额写死；这部分应以学生处或学院当年资助通知为准。\n\n"
        "简单说：奖学金主要奖励成绩和综合表现，助学金主要资助经济困难；国家励志奖学金介于两者之间，既要求家庭经济困难，也要求品学表现。"
    )

    sources = []
    for record in records:
        source = f"{record.category}-{record.source}"
        if source and source not in sources:
            sources.append(source)
    if sources:
        answer += f"\n\n参考来源：{'；'.join(sources)}"
    return answer, [(record, 1.0) for record in records]


def _scholarship_review_answer(retriever: TfidfRetriever) -> tuple[str, list[tuple[object, float]]]:
    wanted = [
        "奖学金看绩点吗？",
        "奖学金要多少绩点？",
        "国家奖学金申请条件是什么？",
        "国家励志奖学金申请条件是什么？",
        "国家励志奖学金如何申请？",
        "国家奖学金和国家励志奖学金能同时获得吗？",
    ]
    records = [record for item in wanted if (record := _find_by_question(retriever, item))]
    if not records:
        records = [
            record
            for record, _score in retriever.search("奖学金 评定 绩点 综合测评 申请条件", top_k=6, category="奖学金")
        ]

    answer = (
        "奖学金评定不能只看一个固定金额，通常要看奖项类型和当年通知：\n"
        "1. 平均学分绩点是学校选拔优秀学生、评定奖学金的重要依据之一；公开资料没有给出统一固定的“最低绩点线”。\n"
        "2. 国家奖学金面向二年级以上（含二年级）特别优秀学生，学习成绩排名和综合考评成绩排名均需位于前10%（含10%）。\n"
        "3. 国家励志奖学金面向二年级以上（含二年级）品学兼优的家庭经济困难学生，必修课程不能有不及格科目。\n"
        "4. 国家励志奖学金一般需在每年9月30日前向班级递交申请表，经班级推选、系部公示、院级审核后上报。\n"
        "5. 同一学年内，获得国家奖学金的学生不能同时获得国家励志奖学金。\n\n"
        "所以你可以先看自己要评的是国家奖学金、国家励志奖学金还是校内奖学金，再按学生处或所在学院当年评定通知确认名额、比例、综合测评和材料要求。"
    )

    sources = []
    for record in records:
        source = f"{record.category}-{record.source}"
        if source and source not in sources:
            sources.append(source)
    if sources:
        answer += f"\n\n参考来源：{'；'.join(sources)}"
    return answer, [(record, 1.0) for record in records]


def _is_life_facility_question(question: str) -> bool:
    return any(
        keyword in question
        for keyword in [
            "食堂",
            "餐厅",
            "吃饭",
            "就餐",
            "超市",
            "便利店",
            "快递",
            "取件",
            "打印",
            "复印",
            "医务室",
        ]
    )


def _life_facility_answer(
    question: str,
    retriever: TfidfRetriever,
) -> tuple[str, list[tuple[object, float]]] | None:
    preferred_questions = [
        (["食堂"], "学校食堂在哪里？"),
        (["餐厅"], "学校有餐厅吗？"),
        (["吃饭", "就餐"], "学校哪里可以吃饭？"),
        (["超市", "便利店"], "学校超市在哪里？"),
        (["快递", "取件"], "学校快递在哪里取？"),
        (["打印", "复印"], "学校哪里可以打印？"),
        (["医务室"], "校医院或医务室在哪里？"),
    ]
    for keywords, wanted_question in preferred_questions:
        if any(keyword in question for keyword in keywords):
            record = _find_by_question(retriever, wanted_question)
            if record:
                results = [(record, 1.0)]
                break
    else:
        results = retriever.search(question, top_k=3, category="校园生活")

    if not results:
        return None
    best_record, _score = results[0]
    references = []
    for record, _ in results[:3]:
        reference = f"{record.category}-{record.source}"
        if reference not in references:
            references.append(reference)
    answer = (
        f"{best_record.answer}\n\n"
        "这类位置问题最好补充一下你所在的校区或宿舍区域，我可以继续帮你按校区方向整理问法和查询建议。\n\n"
        f"参考来源：{'；'.join(references)}"
    )
    return answer, results


def _course_drop_answer(retriever: TfidfRetriever) -> tuple[str, list[tuple[object, float]]] | None:
    record = _find_by_question(retriever, "选错了课能退吗？")
    if not record:
        return None
    answer = (
        "选错了课一般可以在规定时间内退选：\n"
        "1. 登录教务管理系统。\n"
        "2. 进入“选课结果”页面。\n"
        "3. 找到需要退选的课程，点击“退选”。\n"
        "4. 注意要在学校规定的选课/退选时间内操作；如果已经超过时间，建议咨询辅导员或教务处确认是否还能处理。\n\n"
        f"参考来源：选课-{record.source}"
    )
    return answer, [(record, 1.0)]


def _specific_leave_answer(
    question: str,
    retriever: TfidfRetriever,
) -> tuple[str, list[tuple[object, float]]] | None:
    direct_results = retriever.search(question, top_k=3, category="请假")
    if direct_results and direct_results[0][1] >= 0.75:
        best_record, _score = direct_results[0]
        generic_leave_questions = {
            "怎么请病假？",
            "怎么请事假？",
            "请假结束后需要做什么？",
            "特殊情况如何请假？",
        }
        if best_record.question not in generic_leave_questions:
            references = "；".join(
                f"{record.category}-{record.source}" for record, _score in direct_results[:3]
            )
            answer = f"{best_record.answer}\n\n参考来源：{references}"
            return answer, direct_results

    if "病假" in question:
        wanted = ["怎么请病假？", "怎么请事假？", "请假结束后需要做什么？"]
        records = [record for item in wanted if (record := _find_by_question(retriever, item))]
        if not records:
            return None
        answer = (
            "病假申请流程：\n"
            "1. 在“今日校园”APP进入学生服务，选择学生请假并提交申请。\n"
            "2. 请假类型选择病假，填写起止时间和请假事由。\n"
            "3. 上传辅导员要求的证明材料，例如校医院证明；3天以上病假需附证明材料。\n"
            "4. 提交后等待审批，审批通过后按请假时间执行。\n"
            "5. 请假结束后，在“今日校园”APP进入已通过的请假记录进行销假，销假后方可继续请假。\n\n"
            f"参考来源：{'; '.join(f'请假-{record.source}' for record in records)}"
        )
        return answer, [(record, 1.0) for record in records]

    if "事假" in question:
        wanted = ["怎么请事假？", "请假结束后需要做什么？", "特殊情况如何请假？"]
        records = [record for item in wanted if (record := _find_by_question(retriever, item))]
        if not records:
            return None
        answer = (
            "事假申请流程：\n"
            "1. 在“今日校园”APP进入学生服务，选择学生请假并提交申请。\n"
            "2. 请假类型选择事假，填写起止时间和事由。\n"
            "3. 按辅导员要求上传附件材料后提交，等待审批。\n"
            "4. 特殊情况可先电话请假，回校后及时补办请假手续。\n"
            "5. 请假结束后，在已通过的请假记录中完成销假。\n\n"
            f"参考来源：{'; '.join(f'请假-{record.source}' for record in records)}"
        )
        return answer, [(record, 1.0) for record in records]

    if "销假" in question or "结束" in question:
        record = _find_by_question(retriever, "请假结束后需要做什么？")
        if not record:
            return None
        answer = (
            "请假结束后，需要在“今日校园”APP中进入已通过的请假记录进行销假。"
            "销假完成后，才可以继续发起新的请假申请。\n\n"
            f"参考来源：请假-{record.source}"
        )
        return answer, [(record, 1.0)]

    return None


def _leave_summary(retriever: TfidfRetriever) -> tuple[str, list[tuple[object, float]]]:
    keywords = ["病假", "事假", "销假", "特殊情况", "报到"]
    selected = []
    seen_ids = set()

    for keyword in keywords:
        for record, score in retriever.search(keyword, top_k=3, category="请假"):
            if record.id not in seen_ids:
                selected.append((record, score))
                seen_ids.add(record.id)
                break

    if not selected:
        selected = retriever.search("请假", top_k=5, category="请假")

    lines = [
        "学生请假一般可以这样提交：",
        "1. 打开“今日校园”APP，进入学生服务中的学生请假功能。",
        "2. 按实际情况选择病假、事假等请假类型，填写起止时间和请假事由。",
        "3. 按辅导员要求上传证明或附件材料；病假、3天以上请假通常需要补充证明材料。",
        "4. 提交后等待审批，审批通过后按请假时间执行。",
        "5. 请假结束后要在已通过的请假记录中完成销假。",
        "",
        "特殊情况可以先联系辅导员说明，返校后及时补办手续；涉及报到、学籍等事项，以招生办、教务处或辅导员通知为准。",
    ]

    sources = []
    for record, _score in selected[:4]:
        source = str(record.source).split("[reference")[0].strip()
        if source and source not in sources:
            sources.append(source)
    if sources:
        lines.append("")
        lines.append(f"参考来源：{'；'.join(sources)}")
    return "\n".join(lines), selected


def _local_answer(question: str, results: list[tuple[object, float]]) -> str:
    if not results or results[0][1] < MIN_RELIABLE_SCORE:
        return _campus_unknown_answer()

    best_record, _ = results[0]
    references = "；".join(
        f"{record.category}-{record.source}" for record, _score in results[:3]
    )
    return (
        f"根据校园规则，{best_record.answer}\n\n"
        f"参考来源：{references}"
    )


def _glm_answer(question: str, context: str) -> tuple[str | None, dict[str, object]]:
    started = time.perf_counter()
    model = os.getenv("GLM_MODEL", "glm-4-flash")
    meta: dict[str, object] = {
        "provider": "智谱GLM",
        "model": model,
        "used": False,
        "ok": False,
        "error": None,
        "latency_ms": 0,
    }
    api_key = os.getenv("ZHIPUAI_API_KEY") or os.getenv("ZHIPU_API_KEY") or os.getenv("GLM_API_KEY")
    if not api_key:
        meta["error"] = "未配置API Key"
        return None, meta

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            base_url=os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/"),
        )
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": RAG_PROMPT.format(context=context, question=question),
                }
            ],
            temperature=0.3,
            timeout=25,
        )
        meta["used"] = True
        meta["ok"] = True
        meta["latency_ms"] = int((time.perf_counter() - started) * 1000)
        return response.choices[0].message.content, meta
    except Exception as exc:
        meta["used"] = True
        meta["ok"] = False
        meta["error"] = f"{type(exc).__name__}: {exc}"
        meta["latency_ms"] = int((time.perf_counter() - started) * 1000)
        return None, meta


def rag_answer(
    question: str,
    retriever: TfidfRetriever | None = None,
    use_llm: bool = True,
) -> dict[str, object]:
    active_retriever = retriever or build_retriever()

    if _is_health_leave_question(question):
        answer, results = _health_leave_answer(active_retriever)
        return {
            "answer": answer,
            "context": _format_context(results),
            "results": results,
            "llm": LOCAL_RAG_META,
        }

    course_drop = _course_drop_answer(active_retriever) if _is_course_drop_question(question) else None
    if course_drop:
        answer, results = course_drop
        return {
            "answer": answer,
            "context": _format_context(results),
            "results": results,
            "llm": LOCAL_RAG_META,
        }

    if _is_dorm_assignment_question(question):
        answer, results = _dorm_assignment_answer()
        return {
            "answer": answer,
            "context": "",
            "results": results,
            "llm": LOCAL_RAG_META,
        }

    card = _card_answer(question, active_retriever) if _is_card_question(question) else None
    if card:
        answer, results = card
        return {
            "answer": answer,
            "context": _format_context(results),
            "results": results,
            "llm": LOCAL_RAG_META,
        }

    scholarship_grant_comparison = (
        _scholarship_grant_comparison_answer(active_retriever)
        if _is_scholarship_grant_comparison_question(question)
        else None
    )
    if scholarship_grant_comparison:
        answer, results = scholarship_grant_comparison
        return {
            "answer": answer,
            "context": _format_context(results),
            "results": results,
            "llm": LOCAL_RAG_META,
        }

    scholarship_review = (
        _scholarship_review_answer(active_retriever) if _is_scholarship_review_question(question) else None
    )
    if scholarship_review:
        answer, results = scholarship_review
        return {
            "answer": answer,
            "context": _format_context(results),
            "results": results,
            "llm": LOCAL_RAG_META,
        }

    life_facility = _life_facility_answer(question, active_retriever) if _is_life_facility_question(question) else None
    if life_facility:
        answer, results = life_facility
        return {
            "answer": answer,
            "context": _format_context(results),
            "results": results,
            "llm": LOCAL_RAG_META,
        }

    specific_leave = _specific_leave_answer(question, active_retriever)
    if specific_leave:
        answer, results = specific_leave
        return {
            "answer": answer,
            "context": _format_context(results),
            "results": results,
            "llm": LOCAL_RAG_META,
        }

    if _is_general_leave_question(question):
        answer, results = _leave_summary(active_retriever)
        return {
            "answer": answer,
            "context": _format_context(results),
            "results": results,
            "llm": LOCAL_RAG_META,
        }

    if not _is_campus_scope_question(question):
        return {
            "answer": _general_question_answer(question),
            "context": "",
            "results": [],
            "llm": LOCAL_RAG_META,
        }

    results = active_retriever.search(question, top_k=3)
    context = _format_context(results)

    answer = None
    llm_meta = LOCAL_RAG_META.copy()
    has_reliable_context = bool(results and results[0][1] >= MIN_RELIABLE_SCORE)
    if use_llm and has_reliable_context:
        answer, llm_meta = _glm_answer(question, context)
    if not answer:
        answer = _local_answer(question, results)

    return {
        "answer": answer,
        "context": context,
        "results": results,
        "llm": llm_meta,
    }
