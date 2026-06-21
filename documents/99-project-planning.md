# 项目规划

## 当前阶段

Phase 2：LangGraph 与标准 RAG 可观测性增强

## 阶段目标

在已完成 MVP 的基础上，引入 LangGraph workflow、标准化 RAG 检索诊断、CLI/Streamlit 可视化报告和 Python 依赖规范化。

## 任务状态说明

- DONE：已完成。
- NEXT：建议下一批优先执行。
- TODO：已规划，等待执行。
- BLOCKED：被前置任务阻塞。

## 任务看板

| Group | ID | 任务 | Owner | Status | Notes |
|---|---|---|---|---|---|
| DOC | DOC-INIT-001 | 初始化项目文档体系与 AI 协作规则 | Codex | DONE | Phase 0 完成 |
| ARCH | ARCH-001 | 核心架构边界与模块契约 | Codex | DONE | 本轮完成，不实现业务代码 |
| DOC | DOC-REQ-001 | 补充需求文档 | Claude Code + DeepSeek | DONE | 已形成第一阶段需求边界，可后续细化样例 |
| DOC | DOC-DESIGN-001 | 补充 RAG 与多 Agent 设计文档 | Claude Code + DeepSeek | DONE | 核心结论需 Codex 复核 |
| DOC | DOC-CHALLENGE-001 | 补充挑战与评估文档 | Claude Code + DeepSeek | DONE | 已建立风险与评估框架 |
| ARCH | ARCH-002 | 开源项目调研与参考架构沉淀 | Codex | DONE | 调研 LangGraph、Dify、RAGFlow、DeerFlow、OpenHands、Khoj、Flowise |
| DOC | DOC-REFERENCE-001 | 开源项目参考文档补全 | Claude Code + DeepSeek | DONE | 8 个项目深度分析，横向对比表，技术路线确认 |
| ARCH | ARCH-003 | 代码目录结构决策 | Codex | DONE | 采用 src/career_agent；ARCH-003 不创建 pyproject；demo 使用 demo/cli 与 demo/streamlit |
| DOC | DOC-RUNBOOK-001 | 补充 runbook 文档 | Claude Code + DeepSeek | DONE | 本地/GitHub/服务器/排查，5 文件 |
| SAMPLE | SAMPLE-001 | 示例用户资料与岗位 JD | Claude Code + DeepSeek | DONE | 4 份脱敏样例数据，覆盖 Agent 实习场景 |
| RAG | RAG-001 | 设计 RAG 核心数据结构 | Codex | DONE | 已实现 ProfileItem / ProfileDocument / DocumentChunk / RetrievedEvidence |
| RAG | RAG-002 | 实现 MarkdownProfileLoader | Claude Code + DeepSeek | DONE | 单文件/目录加载，title提取，item_type推断，20 tests |
| RAG | RAG-003 | 实现文本清洗与 chunk 切分 | Claude Code + DeepSeek | DONE | clean + 字符切分 + overlap，23 tests |
| RAG | RAG-004 | 设计并实现 VectorStore 接口 | Codex | DONE | VectorStore + MemoryVectorStore，7 tests |
| RAG | RAG-005 | 集成 RAGPipeline | Codex | DONE | Markdown loader + chunker + MemoryVectorStore + SimpleRetriever，5 tests |
| AGENT | AGENT-001 | 设计 AgentTaskState | Claude Code + DeepSeek | DONE | 4 dataclass，19 tests |
| AGENT | AGENT-002 | 实现 JDParserAgent | Claude Code + DeepSeek | DONE | 规则型，18 tests |
| AGENT | AGENT-003 | 实现 RAGRetrieveAgent | Claude Code + DeepSeek | DONE | 包装 RAGPipeline，12 tests |
| AGENT | AGENT-004 | 实现 MatchAnalysisAgent | Claude Code + DeepSeek | DONE | 规则型，10 tests |
| AGENT | AGENT-005 | 实现 BuildAgent | Claude Code + DeepSeek | DONE | 模板型，不编造，9 tests |
| WORKFLOW | WORKFLOW-001 | Agent workflow 集成 | Claude Code + DeepSeek | DONE | 串联 4 Agent，11 tests，140 total |
| DEMO | DEMO-001 | CLI demo | Claude Code + DeepSeek | DONE | CLI + Markdown 报告，10 smoke tests |
| DEMO | DEMO-002 | Streamlit demo | Claude Code + DeepSeek | DONE | 轻量可视化，15 static tests |
| DEPLOY | DEPLOY-001 | 学校服务器部署文档 | Claude Code + DeepSeek | DONE | CLI+Streamlit 部署，checklist |
| WORKFLOW | WORKFLOW-002 | LangGraph workflow 集成 | Codex | NEXT | 已完成 spec 与任务卡，等待实现 |
| RAG | RAG-006 | 检索评分与诊断报告 | Codex | DONE | RetrievalGradeReport 已实现，规则型评分 |
| DEMO | DEMO-003 | RAG 检索诊断展示 | Claude Code + DeepSeek | TODO | CLI + Streamlit 展示 query/grade/evidence |
| PACKAGING | PACKAGING-001 | pyproject 与依赖规范化 | Codex | TODO | langgraph dependency + pytest 配置 |

## 建议任务顺序

1. ~~ARCH-002 开源项目调研与参考架构沉淀。~~ ✅
2. ~~DOC-REFERENCE-001 补充参考项目文档。~~ ✅
3. ~~ARCH-003 代码目录结构决策。~~ ✅
4. ~~RAG-001 RAG schema 设计。~~ ✅
5. ~~SAMPLE-001 示例用户资料与岗位 JD。~~ ✅
6. ~~RAG-002 Markdown loader。~~ ✅
7. ~~RAG-003 chunking。~~ ✅
8. ~~RAG-004 VectorStore interface。~~ ✅
9. ~~RAG-005 RAG pipeline。~~ ✅
10. AGENT-001 AgentTaskState 设计。← 下一步，Codex
11. AGENT-002 JDParserAgent。
12. AGENT-003 RAGRetrieveAgent。
13. AGENT-004 MatchAnalysisAgent。
14. AGENT-005 BuildAgent。
15. WORKFLOW-001 workflow 集成。
16. DEMO-001 CLI demo。
17. DEMO-002 Streamlit demo。
18. DEPLOY-001 学校服务器部署文档。
19. WORKFLOW-002 LangGraph workflow 集成。← 下一步，Codex
20. RAG-006 检索评分与诊断报告。
21. DEMO-003 RAG 检索诊断展示。
22. PACKAGING-001 pyproject 与依赖规范化。

## 分工建议

### Codex

适合负责 RAG-001、RAG-004、RAG-005、AGENT-001、WORKFLOW-001，以及核心接口或疑难修复。

### Claude Code + DeepSeek

适合负责 DOC-REFERENCE-001、DOC-RUNBOOK-001、SAMPLE-001、RAG-002、RAG-003、AGENT-002、AGENT-003、AGENT-004、AGENT-005、DEMO-001、DEMO-002、DEPLOY-001 等边界清晰任务。

Claude Code + DeepSeek 可以承担工作量较大的实现任务，但必须严格基于任务卡边界执行，不得在一次任务中同时跨越 RAG、Agent、Workflow、Demo 多个大模块。

### ChatGPT + User

适合负责需求确认、投递场景选择、样例 JD 筛选、输出风格和展示讲稿确认。

## 后续维护规则

- 每个任务状态变更必须同步更新本文件。
- 新任务必须包含任务卡。
- 不允许一次任务同时跨越 RAG、Agent、Demo、部署多个大模块。
