from .retriever import build_and_save_index


if __name__ == "__main__":
    output = build_and_save_index()
    print(f"已构建本地向量索引：{output}")
