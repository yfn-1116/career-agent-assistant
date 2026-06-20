# 项目文档体系初始化规格

## 用途

本规格定义 Phase 0 初始化任务的交付范围，用于约束执行 Agent 只创建文档体系、协作规范和基础目录骨架。

## 当前状态

本规格对应任务 `DOC-INIT-001`，执行者为 Codex。

## 目标

- 创建中文 `documents/` 项目文档体系。
- 创建 `docs/superpowers/` Agent 执行规范体系。
- 创建 `AGENTS.md` 多 AI 协作规则。
- 创建 `README.md`、`.gitignore`、`.env.example` 和基础目录占位。

## 非目标

- 不实现 RAG 代码。
- 不实现 Agent 代码。
- 不创建 Streamlit 页面。
- 不创建 frontend、backend、server 目录。
- 不引入 LangChain、LangGraph、Chroma、FAISS 等依赖。

## 后续维护规则

- 任何新增实现任务必须先写入 `plans/` 或 `tasks/`。
- 本规格若发生变化，需要同步更新初始化计划和项目日志。
