# 校园生活百事通助手

这是《人工智能应用技术开发》课程实训案例 A 的项目实现。系统围绕校园请假、奖学金、宿舍报修、一卡通、选课、宿舍管理等场景，提供本地知识库检索、RAG 问答、校历周次查询、绩点计算和 Streamlit Web 界面。

## 功能

- 校园规则问答：根据 `data/campus_data.csv` 中的 48 条校园生活问答数据回答问题。
- 本地检索：使用 TF-IDF 构建轻量检索索引，支持无网络环境演示。
- RAG 问答：先检索校园知识库，再生成带来源的回答。
- GLM 增强：配置智谱 AI Key 后，可调用 GLM 生成更自然的回答；失败时自动回退本地 RAG。
- 智能体工具：支持“现在第几周”和“绩点计算 85,90,78”等工具调用。
- Web 界面：支持智能问答、服务导航、检索审计、知识库管理和对话导出。

## 项目结构

```text
campus_assistant/
├── data/campus_data.csv
├── src/
│   ├── app.py
│   ├── agent.py
│   ├── rag.py
│   ├── retriever.py
│   ├── tools.py
│   └── build_vector_db.py
├── vector_db/
├── docs/
├── scripts/
├── main.py
├── requirements.txt
└── README.md
```

## 运行方式

安装依赖：

```bash
pip install -r requirements.txt
```

命令行演示：

```bash
python main.py
```

启动 Web 应用：

```bash
streamlit run src/app.py
```

## 配置智谱 AI（GLM）

在项目根目录创建 `.env`：

```env
ZHIPUAI_API_KEY=你的智谱AI密钥
GLM_MODEL=glm-4-flash
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
```

检查 Key 是否读取成功：

```bash
python scripts/check_glm_key.py
```

测试 GLM API 是否连通：

```bash
python scripts/test_glm_api.py
```

## 测试问题

- 怎么请病假？
- 怎么请假？
- 国家奖学金申请条件是什么？
- 宿舍设施坏了怎么报修？
- 一卡通丢了怎么办？
- 选错了课能退吗？
- 宿舍熄灯时间是什么时候？
- 现在第几周？
- 绩点计算 85,90,78
