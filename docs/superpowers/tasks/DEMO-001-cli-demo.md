# DEMO-001 CLI Demo

## 任务编号

DEMO-001

## 建议执行者

Claude Code + DeepSeek 或 Codex

## 任务目标

实现第一阶段 CLI demo，只调用已有 workflow，输出 Markdown 结果。

## 允许修改文件

- `demo/cli/run_job_match_demo.py`
- `tests/workflows/test_demo_smoke.py`
- `documents/06-demo/01-demo-script.md`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/career_agent/rag/`
- `src/career_agent/agents/`
- `src/career_agent/workflows/`
- `demo/streamlit/`
- `frontend/`
- `backend/`
- `server/`
- `app/`

## 输入

- 示例用户资料。
- 示例 JD。
- 已有 workflow。

## 输出

- CLI 命令入口。
- Markdown demo 输出。
- smoke test。

## 实现要求

- 只调用 workflow。
- 不重新实现 RAG、Agent 或匹配逻辑。
- CLI demo 优先于 Streamlit。

## 测试命令

```bash
pytest tests/workflows/test_demo_smoke.py -v
git status --short
```

## 验收标准

- 本地命令能跑通。
- 输出包含 JD 解析、检索证据、匹配分析和最终内容。
- CLI demo 不依赖 Streamlit。

## 建议 commit message

```text
feat: add cli demo for job match workflow
```
