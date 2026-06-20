# career-agent-assistant

## 项目背景

找实习时手动匹配 JD 和自身经历效率很低。该项目将个人经历文档化，使用 RAG 检索 + 多 Agent 协作做 JD 匹配分析。

## 技术栈

Python, LangChain, Chroma, Streamlit, DeepSeek API

## 核心模块

- RAG Pipeline：Markdown Loader → Text Chunker → MemoryVectorStore → Retriever
- Agent 系统：JDParserAgent → RAGRetrieveAgent → MatchAnalysisAgent → BuildAgent
- Workflow 编排：JobMatchWorkflow
- 展示：CLI Demo + Streamlit Demo

## 当前完成状态

Phase 1 MVP 完成，216 个测试全部通过。

## 可匹配岗位方向

AI 应用开发、RAG 工程师、Python 后端

## 简历表达依据

独立开发基于 RAG + 多 Agent 的实习投递辅助原型，实现完整检索增强生成 pipeline 和 Agent 协作 workflow。
