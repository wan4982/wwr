from .retriever import build_retriever


def search_knowledge(query: str) -> None:
    retriever = build_retriever()
    results = retriever.search(query, top_k=3)
    for record, score in results:
        print(f"相关度：{score:.3f}")
        print(f"分类：{record.category}")
        print(f"问题：{record.question}")
        print(f"内容：{record.answer}")
        print(f"来源：{record.source}\n")


if __name__ == "__main__":
    search_knowledge("我发烧了怎么办？")
