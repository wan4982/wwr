from __future__ import annotations

from datetime import date, datetime

from .config import SCHOOL_TERM_START


SERVICE_LINKS = {
    "官网": "https://www.acvtc.edu.cn/",
    "招生信息网": "https://www.acvtc.edu.cn/",
    "校历": "https://www.acvtc.edu.cn/ggfw/xl.htm",
    "教务处": "https://www.acvtc.edu.cn/jwc/",
    "网上办事大厅": "https://www.acvtc.edu.cn/",
    "财务处": "https://www.acvtc.edu.cn/cwc/",
    "图书馆": "https://ajtsg.mh.chaoxing.com/",
}

CONTACTS = {
    "学校官网": "https://www.acvtc.edu.cn/",
    "招生咨询": "招生办电话：0554-4021821、0554-4021857。也可在学校官网首页底部“联系电话”处核对最新信息。",
    "招生入口": "进入学校官网首页，点击导航栏“招生就业”下的“招生信息网”；也可以直接在官网首页底部查看招生办电话。",
    "校区地址": "新桥校区：安徽省新桥国际产业园寿州大道16号；青年路校区：安徽省合肥市包河区青年路114号。",
    "部门电话": "建议进入对应部门网站或学校官网“联系我们”栏目查询最新电话。",
}


def get_current_week(today: date | None = None, term_start: str = SCHOOL_TERM_START) -> str:
    """Calculate the teaching week from the configured semester start date."""
    current = today or date.today()
    start = datetime.strptime(term_start, "%Y-%m-%d").date()
    week_num = (current - start).days // 7 + 1
    if week_num < 1:
        return "当前还未到本学期第1周，请以学校校历通知为准。"
    return f"现在是本学期第{week_num}周。"


def get_term_progress(today: date | None = None, term_start: str = SCHOOL_TERM_START) -> str:
    current = today or date.today()
    start = datetime.strptime(term_start, "%Y-%m-%d").date()
    days = (current - start).days
    if days < 0:
        return "当前还未到本学期开始日期，请以学校官网校历为准。"
    week_num = days // 7 + 1
    weekday = current.isoweekday()
    return (
        f"按配置的学期开始日期 {term_start} 计算，今天是本学期第{week_num}周，"
        f"本周第{weekday}天。实际教学安排请以学校官网校历和教务通知为准。"
    )


def score_to_gpa(score: int) -> float:
    if score >= 90:
        return 4.0
    if score >= 80:
        return 3.0
    if score >= 70:
        return 2.0
    if score >= 60:
        return 1.0
    return 0.0


def calculate_gpa(scores_str: str) -> str:
    """Calculate GPA from comma-separated or space-separated scores."""
    import re

    scores = [int(item) for item in re.findall(r"\d+", scores_str)]
    if not scores:
        return "请告诉我各科分数，例如：绩点计算 85,90,78。"

    invalid_scores = [score for score in scores if score < 0 or score > 100]
    if invalid_scores:
        return "分数需要在0到100之间，请重新输入。"

    gpa = sum(score_to_gpa(score) for score in scores) / len(scores)
    return f"您的平均绩点是：{gpa:.2f}。"


def calculate_gpa_detail(scores_str: str) -> str:
    import re

    scores = [int(item) for item in re.findall(r"\d+", scores_str)]
    if not scores:
        return "请提供各科分数，例如：绩点明细 85,90,78。"
    invalid_scores = [score for score in scores if score < 0 or score > 100]
    if invalid_scores:
        return "分数需要在0到100之间，请重新输入。"

    lines = ["绩点明细如下："]
    total = 0.0
    for index, score in enumerate(scores, start=1):
        gpa = score_to_gpa(score)
        total += gpa
        lines.append(f"{index}. {score}分 → {gpa:.1f}绩点")
    lines.append(f"平均绩点：{total / len(scores):.2f}")
    return "\n".join(lines)


def get_service_link(query: str) -> str:
    matched = []
    for name, url in SERVICE_LINKS.items():
        if name in query:
            matched.append((name, url))

    if not matched:
        matched = list(SERVICE_LINKS.items())

    lines = ["常用官网服务入口："]
    for name, url in matched:
        lines.append(f"- {name}: {url}")
    lines.append("如入口地址调整，请以安徽交通职业技术学院官网首页导航为准。")
    return "\n".join(lines)


def get_contact_info(query: str) -> str:
    lines = ["学校联系方式查询建议："]
    if "招生" in query:
        lines.extend(
            [
                f"- 查询路径：{CONTACTS['招生入口']}",
                f"- 招生咨询：{CONTACTS['招生咨询']}",
                f"- 学校官网：{CONTACTS['学校官网']}",
                "- 提醒：招生政策、批次安排和电话如有调整，请以学校官网最新公布为准。",
            ]
        )
    if "地址" in query or "校区" in query:
        lines.append(f"- 校区地址：{CONTACTS['校区地址']}")
    if len(lines) == 1:
        lines.extend(
            [
                f"- 学校官网：{CONTACTS['学校官网']}",
                f"- 部门电话：{CONTACTS['部门电话']}",
            ]
        )
    return "\n".join(lines)


def list_toolbox() -> str:
    return (
        "我现在支持这些常用工具：\n"
        "1. 校历周次：例如“现在第几周？”\n"
        "2. 学期进度：例如“今天是本学期第几天？”\n"
        "3. 绩点计算：例如“绩点计算 85,90,78”\n"
        "4. 绩点明细：例如“绩点明细 85,90,78”\n"
        "5. 官网入口：例如“教务处入口在哪里？”“校历在哪里看？”\n"
        "6. 联系方式：例如“学校招生电话在哪里查？”\n"
        "7. 多轮追问：例如先问“一卡通丢了怎么办？”，再问“怎么挂失？”"
    )
