# PACKAGING-001 pyproject 与依赖规范化

## 任务编号

PACKAGING-001

## 建议执行者

Codex

## 任务目标

新增 `pyproject.toml`，声明项目包、LangGraph 依赖、可选 demo 依赖和 pytest 配置，使项目运行方式标准化。

## 允许修改文件

- `pyproject.toml`
- `README.md`
- `documents/98-runbook/01-local-development.md`
- `documents/98-runbook/03-school-server-deploy.md`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/career_agent/`
- `demo/`
- `tests/`
- `outputs/`
- `frontend/`
- `backend/`
- `server/`

## 输入

- 当前 `src/` layout。
- LangGraph workflow 对 `langgraph` 的依赖。
- 现有 CLI / Streamlit 运行方式。

## 输出

- `pyproject.toml`
- 更新后的本地运行说明。

## 实现要求

- 使用 `src` layout。
- 声明核心依赖 `langgraph`。
- 将 `streamlit` 放入 optional dependencies，例如 `demo` extra。
- 配置 pytest 使用 `src` 作为 pythonpath。
- 不加入真实 API key 或私有配置。

## 测试命令

```bash
python -m pip install -e .
pytest tests -q
python demo/cli/run_job_match_demo.py
git status --short
```

## 验收标准

- `pip install -e .` 后可以直接运行测试。
- `pytest tests -q` 不再依赖手动 `PYTHONPATH=src`。
- README 和 runbook 中的新命令一致。

## 建议 commit message

```text
chore: add pyproject for langgraph workflow
```
