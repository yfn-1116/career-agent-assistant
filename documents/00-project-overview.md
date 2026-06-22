# 项目总览

## 用途

本文档记录 `career-agent-assistant` 的整体定位、阶段目标、核心模块、边界约束和协作分工。后续任何 Agent 执行任务前，都应先理解本文档中的项目范围。

## 项目定位

本项目是一个面向大学生实习求职场景的 Internship Copilot / 实习投递辅助 Agent 原型。项目关注的不是“做一个网页简历生成器”，而是验证个人资料知识库、RAG 检索、多 Agent / LangGraph 工作流和证据约束生成能否在求职投递场景中稳定产出可信材料。

## 当前核心链路

```text
本地用户资料 Markdown / 上传文件 / GitHub 摘要
-> RAG 检索
-> JD 解析
-> 匹配分析
-> 简历项目描述 / 沟通话术生成
-> 投递记录 / 诊断报告 / Markdown 或 Streamlit 展示
```

## 当前已实现范围

- 输入：本地 Markdown 用户资料、项目经历、GitHub 仓库摘要、技能材料、实习经历、示例岗位 JD。
- 处理：JD 解析、能力匹配、RAG 检索个人经历、检索评分、query rewrite / fallback、基于证据的输出生成。
- 输出：CLI Markdown 报告、Streamlit demo、FastAPI browser assistant API、Chrome Browser Extension demo、投递记录 JSONL。
- 工作流：保留普通 Python `JobMatchWorkflow`，同时提供 LangGraph / `AgentRunService` 原型作为 UI / API 的统一入口。
- 工程流程：本地开发、GitHub 同步、学校服务器复现、pytest 自动化测试。

## 演示边界

- 不做自动投递。
- 不自动向 HR 或招聘平台发送消息。
- 不自动爬取 BOSS、实习僧、LinkedIn 等岗位网站。
- 浏览器插件只读取当前页面文本并辅助生成分析、话术和简历建议，发送动作由用户确认。
- 不做复杂账号系统和多用户知识库。
- 不把本地上传文件、真实简历、投递记录、知识库索引提交到 Git。

## 可信生成边界

最终输出必须基于 evidence/source。当前实现会把生成内容分成：

- `can_write_claims`：来自 `implemented` evidence，可以作为简历 bullet 或沟通话术候选。
- `needs_confirmation_claims`：来自 `designed` evidence，需要用户确认后才能使用。
- `learning_plan_claims`：来自 `planned` / `uncertain` evidence，只能作为学习计划或补强建议。

如果 Faithfulness 检查失败或存在不可直接写入的内容，`AgentRunResult.approval_required` 会被置为 `true`，warnings 会暴露给 API / UI。

## 核心模块边界

### RAG 用户资料知识库

默认演示使用脱敏 Markdown 样例和手写 GitHub 仓库摘要。运行时上传的简历、PDF、投递记录和知识库索引写入 ignored runtime 路径，不作为可提交样例数据。RAG 相关核心概念包括 `ProfileItem`、`ProfileDocument`、`DocumentChunk`、`RetrievedEvidence`、`MarkdownProfileLoader`、`TextChunker`、`VectorStore interface`、`SimpleRetriever`、`HybridRetriever`、`RAGPipeline`、`RetrievalGradeReport`。

### 多 Agent 编排

核心 Agent 包括 `JDParserAgent`、`RAGRetrieveAgent`、`MatchAnalysisAgent`、`BuildAgent`，并配套 `MessageAgent`、`HRReplyAssistant`、`JobMatchScorer`、`ApplicationRepository` 等求职场景模块。编排层同时保留普通 Python workflow 和 LangGraph workflow；`AgentRunService` 是 UI / API / CLI 调用核心能力的收敛入口。

### 展示方式

当前展示方式包括 CLI + Markdown、Streamlit、本地 FastAPI API 和 Chrome Browser Extension。完整生产级前后端平台仍不在当前原型范围内。

## AI 分工边界

- Codex：主架构与核心实现 Agent，负责 RAG schema、VectorStore 接口、RAG pipeline、AgentTaskState、workflow 集成和疑难修复。
- Claude Code + DeepSeek：负责边界清晰的文档补全、样例数据、局部模块实现、测试补充、runbook 和 demo 展示层。
- ChatGPT + User：负责需求澄清、方案取舍、任务拆分和提示词设计，不直接作为仓库执行 Agent。

## 当前状态

Phase 0 / Phase 1 的文档和 MVP 已完成。当前项目处于 Phase 2：稳定可演示、结构清晰、文档一致的 Internship Copilot 原型整理阶段，重点是收敛运行数据边界、统一文档状态、薄化 Streamlit UI、强化 `AgentRunService` 和证据约束。

## 后续维护规则

- 全局定位变化必须同步更新 `README.md`、`documents/99-project-planning.md` 和相关任务卡。
- 核心 schema、workflow、技术选型只能由 Codex 或经明确授权的 Agent 修改。
- 不允许把一个任务同时扩展到 RAG、Agent、Demo、部署多个大模块。
