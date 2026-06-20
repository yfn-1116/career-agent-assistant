# ARCH-003 代码目录结构决策

## 任务编号

ARCH-003

## 建议执行者

Codex

## 任务目标

在开源项目调研基础上，最终确定本项目第一阶段代码目录结构、Python package 方式、demo 入口和配置边界。本任务只做决策，不创建代码目录。

## 允许修改文件

- `documents/02-design/07-reference-inspired-architecture.md`
- `documents/03-technical-decisions/06-reference-architecture-selection.md`
- `documents/99-project-planning.md`
- `documents/97-journal.md`
- `docs/superpowers/tasks/ARCH-003-codebase-structure-decision.md`

## 禁止修改文件

- `src/`
- `tests/`
- `data/`
- `outputs/`
- frontend/backend/server/app/scripts 目录
- `pyproject.toml`
- `requirements.txt`
- 业务代码文件

## 输入

- ARCH-002 开源项目参考文档。
- 第一阶段 RAG + Agent 架构边界。
- 后续 RAG、Agent、Workflow、Demo 任务卡。

## 输出

- 第一阶段代码目录结构决策。
- 是否采用 `src/career_agent/` package 的结论。
- 是否引入 `pyproject.toml` 的结论。
- demo 入口放置位置的结论。
- 后续 IMPLEMENT 任务需要创建哪些目录的清单。

## 实现要求

- 不创建代码目录。
- 不写业务代码。
- 不引入依赖。
- 必须说明允许创建哪些代码目录、禁止创建哪些目录。

## 验收标准

- 明确是否采用 `src/career_agent` package。
- 明确是否创建 `app/streamlit_app.py`。
- 明确是否引入 `pyproject.toml`。
- 明确第一批实现任务的目录创建范围。

## 测试命令

```bash
git status --short
find documents docs/superpowers/tasks -name '*.md' -type f -empty -print
find . -path './.git' -prune -o -type d \( -name frontend -o -name backend -o -name server -o -name app -o -name scripts \) -print
```

## 提交信息建议

```text
docs: decide first phase codebase structure
```
