# 项目总览

## 用途

本文档记录 `career-agent-assistant` 的整体定位、阶段目标、核心模块、边界约束和协作分工。后续任何 Agent 执行任务前，都应先理解本文档中的项目范围。

## 项目定位

本项目是一个面向大学生实习求职场景的 RAG + 多 Agent 原型系统。项目关注的不是“做一个网页简历生成器”，而是验证个人资料知识库和多 Agent 编排能否在求职投递场景中稳定产出可信材料。

## 第一阶段核心链路

```text
本地用户资料 Markdown
-> RAG 检索
-> JD 解析
-> 匹配分析
-> 简历项目描述 / 沟通话术生成
-> Markdown 或 Streamlit 展示
```

## 第一阶段范围

- 输入：本地 Markdown 用户资料、项目经历、GitHub 仓库摘要、技能材料、实习经历、示例岗位 JD。
- 处理：JD 解析、资料检索、匹配分析、基于证据的输出生成。
- 输出：Markdown 报告优先，Streamlit 轻量展示作为后续 demo 展示方式。
- 工程流程：本地开发、GitHub 同步、学校服务器复现。

## 第一阶段不做

- 不做自动投递。
- 不爬取 BOSS、实习僧等岗位网站。
- 不做复杂账号系统和多用户知识库。
- 不做完整前后端分离。
- 不做大规模 GitHub 源码分析。
- 不生成 PDF 简历作为核心目标。

## 核心模块边界

### RAG 用户资料知识库

第一阶段只处理本地 Markdown 和手写 GitHub 仓库摘要，不直接读取完整 GitHub 源码。RAG 相关核心概念包括 `ProfileItem`、`ProfileDocument`、`DocumentChunk`、`RetrievedEvidence`、`MarkdownProfileLoader`、`TextChunker`、`VectorStore interface`、`SimpleRetriever`、`RAGPipeline`。

### 多 Agent 编排

第一阶段只做四个核心 Agent：`JDParserAgent`、`RAGRetrieveAgent`、`MatchAnalysisAgent`、`BuildAgent`。Orchestrator 可以先用普通 Python workflow 或轻量状态流实现，后续再考虑 LangGraph。

### 展示方式

第一阶段优先 CLI + Markdown 输出，再扩展 Streamlit。FastAPI + 前端分离作为第二阶段服务化扩展，不进入当前阶段。

## AI 分工边界

- Codex：主架构与核心实现 Agent，负责 RAG schema、VectorStore 接口、RAG pipeline、AgentTaskState、workflow 集成和疑难修复。
- Claude Code + DeepSeek：负责边界清晰的文档补全、样例数据、局部模块实现、测试补充、runbook 和 demo 展示层。
- ChatGPT + User：负责需求澄清、方案取舍、任务拆分和提示词设计，不直接作为仓库执行 Agent。

## 当前状态

Phase 0 已完成。当前是 Phase 1：补强核心架构边界、模块契约和后续任务卡。本轮仍然不实现业务代码。

## 后续维护规则

- 全局定位变化必须同步更新 `README.md`、`documents/99-project-planning.md` 和相关任务卡。
- 核心 schema、workflow、技术选型只能由 Codex 或经明确授权的 Agent 修改。
- 不允许把一个任务同时扩展到 RAG、Agent、Demo、部署多个大模块。
