from datetime import date

from src.agent import CampusAgent
from src.data_loader import load_records
from src.retriever import build_retriever
from src.tools import calculate_gpa, get_current_week


def test_data_count():
    assert len(load_records()) >= 20


def test_retrieve_leave():
    results = build_retriever().search("我发烧了怎么办？", top_k=1)
    assert results
    assert results[0][0].category == "请假"


def test_tools():
    assert "2.33" in calculate_gpa("85,90,78")
    assert "第2周" in get_current_week(date(2026, 3, 3))


def test_agent_routes_tools():
    agent = CampusAgent()
    assert "绩点" in agent.chat("绩点计算 85,90,78", use_llm=False)
    assert "前10%" in agent.chat("国家奖学金申请条件是什么？", use_llm=False)


def test_common_campus_aliases():
    agent = CampusAgent()

    dorm_answer = agent.chat("怎么选宿舍", use_llm=False)
    assert "没有收录" in dorm_answer
    assert "报修" not in dorm_answer

    lost_card_answer = agent.chat("饭卡丢了怎么办", use_llm=False)
    assert "校园卡" in lost_card_answer
    assert "挂失" in lost_card_answer
    assert "补办" in lost_card_answer

    recharge_answer = agent.chat("怎么充值饭卡", use_llm=False)
    assert "今日校园" in recharge_answer
    assert "充值" in recharge_answer

    scholarship_grant_answer = agent.chat("奖学金和助学金有什么区别", use_llm=False)
    assert "奖励优秀" in scholarship_grant_answer
    assert "帮扶困难" in scholarship_grant_answer
    assert "不能把助学金金额写死" in scholarship_grant_answer
