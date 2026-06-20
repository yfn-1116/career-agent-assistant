# WORKFLOW-001 Agent Workflow 集成

## 任务编号

WORKFLOW-001

## 建议执行者

Codex

## 任务目标

实现第一阶段固定 `job_match_workflow.py`，串联 JDParserAgent、RAGRetrieveAgent、MatchAnalysisAgent、BuildAgent。

## 允许修改文件

- `src/career_agent/workflows/__init__.py`
- `src/career_agent/workflows/job_match_workflow.py`
- `tests/workflows/test_job_match_workflow.py`
- `documents/02-design/05-data-flow-design.md`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/career_agent/rag/` 底层实现，除非接口缺陷经授权。
- `src/career_agent/agents/` 单个 Agent 内部实现，除非接口缺陷经授权。
- `demo/`
- `outputs/`
- `frontend/`
- `backend/`
- `server/`
- LangGraph 依赖。

## 输入

- `AgentTaskState`
- 四个核心 Agent。
- RAG pipeline。

## 输出

- 可被 CLI 和 Streamlit demo 调用的 workflow 入口。

## 实现要求

- 第一阶段只做普通 Python workflow。
- 不引入 LangGraph。
- 每个 Agent 只读写规定状态字段。
- 错误写入状态，不吞异常。

## 测试命令

```bash
pytest tests/workflows/test_job_match_workflow.py -v
git status --short
```

## 验收标准

- 固定样例能跑完整链路。
- 状态字段按顺序更新。
- 任一节点失败时有清晰错误。

## 建议 commit message

```text
feat: integrate first phase job match workflow
```
