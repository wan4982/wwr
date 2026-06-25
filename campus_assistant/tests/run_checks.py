from datetime import date
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agent import CampusAgent
from src.data_loader import load_records
from src.retriever import build_retriever
from src.tools import calculate_gpa, get_current_week


def check(name: str, passed: bool) -> None:
    status = "PASS" if passed else "FAIL"
    print(f"{status} {name}")
    if not passed:
        raise SystemExit(1)


def main() -> None:
    records = load_records()
    check("knowledge base has at least 20 records", len(records) >= 20)

    retriever = build_retriever()
    leave_results = retriever.search("怎么请病假？", top_k=1)
    check("leave query retrieves leave policy", leave_results[0][0].category == "请假")

    scholarship_results = retriever.search("国家奖学金申请条件是什么？", top_k=1)
    check("scholarship query retrieves scholarship policy", scholarship_results[0][0].category == "奖学金")

    repair_results = retriever.search("宿舍设施坏了怎么报修？", top_k=1)
    check("repair query retrieves repair policy", repair_results[0][0].category == "报修")

    check("gpa calculator works", "3.00" in calculate_gpa("85,90,78"))
    check("week calculator works", "第2周" in get_current_week(date(2026, 3, 3)))

    agent = CampusAgent(retriever)
    check("agent answers scholarship via RAG", "前10%" in agent.chat("国家奖学金申请条件是什么？", use_llm=False))
    check("agent routes gpa tool", "3.00" in agent.chat("绩点计算 85,90,78", use_llm=False))
    check("agent does not confuse dorm assignment with repair", "没有收录" in agent.chat("怎么选宿舍", use_llm=False))
    lost_card_answer = agent.chat("饭卡丢了怎么办", use_llm=False)
    check("agent maps meal card to campus card", "挂失" in lost_card_answer and "补办" in lost_card_answer)
    check("agent maps meal card recharge", "今日校园" in agent.chat("怎么充值饭卡", use_llm=False))
    scholarship_grant_answer = agent.chat("奖学金和助学金有什么区别", use_llm=False)
    check(
        "agent compares scholarship and grant",
        "奖励优秀" in scholarship_grant_answer and "帮扶困难" in scholarship_grant_answer,
    )


if __name__ == "__main__":
    main()
