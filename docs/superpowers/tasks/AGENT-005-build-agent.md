# AGENT-005 BuildAgent 实现

## 任务编号

AGENT-005

## 建议执行者

Claude Code + DeepSeek 或 Codex

## 任务目标

实现 `BuildAgent`，基于 evidence 和 match_analysis 生成 Markdown 输出。

## 允许修改文件

- `src/career_agent/agents/build_agent.py`
- `tests/agents/test_build_agent.py`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/career_agent/rag/`
- `src/career_agent/workflows/`
- `demo/`
- `outputs/`
- `frontend/`
- `backend/`
- `server/`

## 输入

- `retrieved_evidence`
- `match_analysis`
- 用户请求。

## 输出

- `generated_output` Markdown。

## 实现要求

- 不得编造经历。
- 无证据内容必须标记为建议或要求补充资料。
- 不修改 evidence 和 match_analysis。

## 测试命令

```bash
pytest tests/agents/test_build_agent.py -v
git status --short
```

## 验收标准

- 输出能用于简历或沟通初稿。
- 关键事实可追溯到 evidence。
- 资料不足时不强行生成。

## 建议 commit message

```text
feat: add build agent
```
