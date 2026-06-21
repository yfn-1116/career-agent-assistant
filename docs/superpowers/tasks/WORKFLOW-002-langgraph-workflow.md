# WORKFLOW-002 LangGraph Workflow 集成

## 任务编号

WORKFLOW-002

## 建议执行者

Codex

## 任务目标

新增 LangGraph 版本的 job match workflow，将现有 Agent 编排成显式状态图，并保留当前 `JobMatchWorkflow` 兼容入口。

## 允许修改文件

- `src/career_agent/agents/state.py`
- `src/career_agent/workflows/__init__.py`
- `src/career_agent/workflows/langgraph_job_match_workflow.py`
- `tests/workflows/test_langgraph_job_match_workflow.py`
- `documents/02-design/05-data-flow-design.md`
- `documents/03-technical-decisions/02-langgraph-selection.md`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/career_agent/rag/`，除非调用已完成的 RAG grading 接口。
- `src/career_agent/agents/` 单个 Agent 行为，除 `state.py` 扩展状态字段外。
- `demo/`
- `outputs/`
- `frontend/`
- `backend/`
- `server/`

## 输入

- 已批准 spec：`docs/superpowers/specs/2026-06-21-langgraph-rag-standardization-design.md`
- 现有 `JobMatchWorkflow`
- 现有 `AgentTaskState`
- 现有四个核心 Agent

## 输出

- `LangGraphJobMatchWorkflow`
- LangGraph 节点顺序 trace
- 可通过测试验证的完整 job match 状态图

## 实现要求

- 使用 `langgraph.graph.StateGraph`、`START`、`END`、`compile`、`invoke`。
- 节点顺序为 `parse_jd -> build_retrieval_query -> retrieve_evidence -> grade_retrieval -> analyze_match -> build_output -> finalize_report`。
- 不删除现有 `JobMatchWorkflow`。
- 每个节点只写入自己负责的状态字段。
- 节点失败时写入 `status=failed` 与 `error_message`。

## 测试命令

```bash
pytest tests/workflows/test_langgraph_job_match_workflow.py -v
pytest tests/workflows/test_job_match_workflow.py -v
git status --short
```

## 验收标准

- LangGraph workflow 能跑通 4 个示例 JD。
- `workflow_trace` 能反映节点执行顺序。
- `retrieval_query` 被写入状态。
- 旧 `JobMatchWorkflow` 测试不回归。

## 建议 commit message

```text
feat: add langgraph job match workflow
```
