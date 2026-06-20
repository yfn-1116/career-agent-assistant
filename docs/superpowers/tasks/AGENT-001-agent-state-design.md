# AGENT-001 AgentTaskState 设计

## 任务编号

AGENT-001

## 建议执行者

Codex

## 任务目标

设计 `AgentTaskState` 的字段、生命周期、错误状态和 Agent 间传递边界，为普通 workflow 和后续 LangGraph 迁移提供基础。

## 允许修改文件

- `documents/02-design/03-multi-agent-orchestration.md`
- `documents/02-design/04-agent-state-design.md`
- `documents/02-design/05-data-flow-design.md`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/`
- `tests/`
- `data/`
- `outputs/`
- RAG pipeline 实现
- Demo 实现
- 部署配置

## 输入

- `documents/02-design/04-agent-state-design.md`
- `documents/03-technical-decisions/02-langgraph-selection.md`

## 输出

- `AgentTaskState` 字段清单：`task_id`、`user_request`、`job_description`、`parsed_jd`、`retrieved_evidence`、`match_analysis`、`generated_output`、`review_result`、`status`、`error_message`、`created_at`、`updated_at`。
- 第一阶段字段和后续扩展字段划分。

## 实现要求

- 不写业务代码。
- 说明状态如何服务 LangGraph、日志追踪和上下文控制。
- 明确每个核心 Agent 读写哪些字段。

## 验收标准

- 字段含义清楚。
- 状态生命周期清楚。
- 能支持四个核心 Agent 的固定流程。

## 测试命令

```bash
git status --short
find documents docs/superpowers/tasks -name '*.md' -type f -empty -print
```

## 提交信息建议

```text
docs: define agent task state contract
```
