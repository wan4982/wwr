from src.agent import CampusAgent
from src.retriever import build_and_save_index


def main() -> None:
    build_and_save_index()
    agent = CampusAgent()
    examples = [
        "怎么请病假？",
        "国家奖学金申请条件是什么？",
        "宿舍设施坏了怎么报修？",
        "一卡通丢了怎么办？",
        "选错了课能退吗？",
        "宿舍熄灯时间是什么时候？",
        "现在第几周？",
        "绩点计算 85,90,78",
    ]
    for question in examples:
        print(f"学生：{question}")
        print(f"助手：{agent.chat(question, use_llm=False)}")
        print("-" * 60)


if __name__ == "__main__":
    main()
