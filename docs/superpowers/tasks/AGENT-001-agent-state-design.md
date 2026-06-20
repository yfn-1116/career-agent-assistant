# AGENT-001 设计 AgentTaskState

## 用途

本任务用于设计多 Agent 编排中的核心状态对象 AgentTaskState。

## 当前状态

状态：TODO。

## 建议 Executor

Codex。

## 允许修改

- `documents/02-design/03-multi-agent-orchestration.md`
- `documents/02-design/04-agent-state-design.md`
- `documents/02-design/05-data-flow-design.md`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改

- RAG 实现代码。
- Demo 实现。
- 部署配置。
- 未授权技术选型。

## 验收标准

- 明确状态字段、生命周期、错误状态和 Agent 间传递边界。
- 不实现 workflow 代码。

## 后续维护规则

该任务完成后才能规划 Agent workflow 的最小实现。
