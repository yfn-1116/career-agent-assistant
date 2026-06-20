# 项目规划

## 当前阶段

Phase 1：文档补强与架构边界定义

## 阶段目标

明确第一阶段 RAG + 多 Agent 原型系统的边界、模块契约、任务拆分和后续执行顺序。当前阶段仍然不实现业务代码。

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
| DOC | DOC-RUNBOOK-001 | 补充 runbook 文档 | Claude Code + DeepSeek | TODO | 本地、GitHub、学校服务器流程 |
| SAMPLE | SAMPLE-001 | 示例用户资料与岗位 JD | Claude Code + DeepSeek | NEXT | 只写 data/samples/ 示例资料 |
| RAG | RAG-001 | 设计 RAG 核心数据结构 | Codex | NEXT | ProfileItem / ProfileDocument / DocumentChunk / RetrievedEvidence |
| RAG | RAG-002 | 实现 MarkdownProfileLoader | Claude Code + DeepSeek | TODO | 依赖 RAG-001 |
| RAG | RAG-003 | 实现文本清洗与 chunk 切分 | Claude Code + DeepSeek | TODO | 依赖 RAG-001 |
| RAG | RAG-004 | 设计并实现 VectorStore 接口 | Codex | TODO | 核心接口任务 |
| RAG | RAG-005 | 集成 RAGPipeline | Codex | TODO | 依赖 RAG-002/003/004 |
| AGENT | AGENT-001 | 设计 AgentTaskState | Codex | NEXT | 多 Agent 状态核心 |
| AGENT | AGENT-002 | 实现 JDParserAgent | Claude Code + DeepSeek | TODO | 只解析 JD |
| AGENT | AGENT-003 | 实现 RAGRetrieveAgent | Claude Code + DeepSeek | TODO | 只调用 RAG pipeline |
| AGENT | AGENT-004 | 实现 MatchAnalysisAgent | Claude Code + DeepSeek | TODO | 只做匹配分析 |
| AGENT | AGENT-005 | 实现 BuildAgent | Claude Code + DeepSeek 或 Codex | TODO | 不得编造经历 |
| WORKFLOW | WORKFLOW-001 | Agent workflow 集成 | Codex | TODO | 核心复杂任务 |
| DEMO | DEMO-001 | CLI demo | Claude Code + DeepSeek 或 Codex | TODO | 只调用已有 workflow |
| DEMO | DEMO-002 | Streamlit demo | Claude Code + DeepSeek | TODO | 只做展示层 |
| DEPLOY | DEPLOY-001 | 学校服务器部署文档 | Claude Code + DeepSeek | TODO | 不写部署脚本 |

## 建议任务顺序

1. ~~ARCH-002 开源项目调研与参考架构沉淀。~~ ✅
2. ~~DOC-REFERENCE-001 补充参考项目文档。~~ ✅
3. ~~ARCH-003 代码目录结构决策。~~ ✅
4. RAG-001 RAG schema 设计。← 下一步，Codex
5. SAMPLE-001 示例用户资料与岗位 JD。← 下一步，Claude Code + DeepSeek
6. RAG-002 Markdown loader。Claude Code + DeepSeek
7. RAG-003 chunking。Claude Code + DeepSeek
8. RAG-004 VectorStore interface。Codex
9. RAG-005 RAG pipeline。Codex
10. AGENT-001 AgentTaskState 设计。Codex
11. AGENT-002 JDParserAgent。
12. AGENT-003 RAGRetrieveAgent。
13. AGENT-004 MatchAnalysisAgent。
14. AGENT-005 BuildAgent。
15. WORKFLOW-001 workflow 集成。
16. DEMO-001 CLI demo。
17. DEMO-002 Streamlit demo。
18. DEPLOY-001 学校服务器部署文档。

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
