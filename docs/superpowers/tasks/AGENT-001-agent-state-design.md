# AGENT-001 AgentTaskState 设计与实现

## 任务编号

AGENT-001

## 建议执行者

Codex

## 任务目标

设计并实现 `AgentTaskState`，作为普通 Python workflow 和后续 LangGraph 迁移的共享状态契约。

## 允许修改文件

- `src/career_agent/agents/__init__.py`
- `src/career_agent/agents/state.py`
- `tests/agents/test_state.py`
- `documents/02-design/04-agent-state-design.md`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/career_agent/rag/`
- `src/career_agent/workflows/`
- `src/career_agent/agents/jd_parser.py`
- `src/career_agent/agents/rag_retrieve_agent.py`
- `src/career_agent/agents/match_analysis_agent.py`
- `src/career_agent/agents/build_agent.py`
- `demo/`
- `data/`
- `outputs/`

## 输入

- `documents/02-design/04-agent-state-design.md`
- ARCH-003 代码目录结构决策。

## 输出

- `AgentTaskState`
- 状态单元测试。

## 实现要求

- 支持 JD、parsed_jd、retrieved_evidence、match_analysis、generated_output、status、error_message 等字段。
- 不实现任何 Agent 行为。
- 不引入 LangGraph。

## 测试命令

```bash
pytest tests/agents/test_state.py -v
git status --short
```

## 验收标准

- 状态字段清晰稳定。
- 能支持四个核心 Agent 的固定流程。
- 保留后续 LangGraph 迁移空间。

## 建议 commit message

```text
feat: define agent task state
```
