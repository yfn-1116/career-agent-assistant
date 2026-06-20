# 系统架构

## 整体架构

三层分离：RAG 层 → Agent 层 → Workflow 层

## RAG 层

Markdown Loader → Text Chunker → VectorStore → Retriever → Pipeline

每层接口抽象，可替换后端实现。

## Agent 层

四个 Agent 基于 AgentTaskState 共享状态协作。默认规则型，可选 LLM 增强。

## Workflow 层

JobMatchWorkflow 串联全链路，状态管理、错误处理、可注入自定义 Agent。
