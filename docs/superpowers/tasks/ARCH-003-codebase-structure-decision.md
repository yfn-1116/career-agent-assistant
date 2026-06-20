# ARCH-003 代码目录结构决策

## 任务编号

ARCH-003

## 建议执行者

Codex

## 任务目标

最终确定第一阶段代码目录结构、Python package 方式、demo 入口、provider / evaluation 边界和后续实现任务路径。本任务只做文档决策，不创建代码目录。

## 允许修改文件

- `documents/02-design/01-overall-architecture.md`
- `documents/02-design/02-rag-module-design.md`
- `documents/02-design/03-multi-agent-orchestration.md`
- `documents/02-design/04-agent-state-design.md`
- `documents/02-design/05-data-flow-design.md`
- `documents/02-design/07-reference-inspired-architecture.md`
- `documents/03-technical-decisions/01-display-mode-selection.md`
- `documents/03-technical-decisions/02-langgraph-selection.md`
- `documents/03-technical-decisions/03-vector-store-selection.md`
- `documents/03-technical-decisions/04-model-provider-selection.md`
- `documents/03-technical-decisions/05-frontend-backend-decision.md`
- `documents/03-technical-decisions/06-reference-architecture-selection.md`
- `documents/99-project-planning.md`
- `documents/97-journal.md`
- `docs/superpowers/tasks/ARCH-003-codebase-structure-decision.md`

## 禁止修改文件

- `src/`
- `tests/`
- `data/`
- `outputs/`
- `README.md`
- `AGENTS.md`
- `.gitignore`
- `.env.example`
- `pyproject.toml`
- `requirements.txt`
- frontend/backend/server/app/scripts 目录。

## 输入

- ARCH-002 开源项目参考文档。
- 第一阶段 RAG + Agent 架构边界。
- 后续 RAG、Agent、Workflow、Demo 任务卡。

## 输出

- 第一阶段采用 `src/career_agent/` package 的结论。
- RAG、Agent、Workflow、Models、Evaluation、Demo 的最终目录建议。
- 第一阶段和第二阶段目录创建边界。
- 更新后的实现任务卡。

## 实现要求

- 不创建代码目录。
- 不写业务代码。
- 不引入依赖。
- 明确允许创建哪些代码目录、禁止创建哪些目录。
- 明确不创建 `app/streamlit_app.py`。
- 明确 ARCH-003 不创建 `pyproject.toml`。

## 测试命令

```bash
git status --short
find documents docs/superpowers/tasks -name '*.md' -type f -empty -print
find . -path './.git' -prune -o -type d \( -name frontend -o -name backend -o -name server -o -name app -o -name scripts \) -print
find . -maxdepth 4 -type f \( -name '*.py' -o -name 'pyproject.toml' -o -name 'requirements.txt' \) -print
```

## 验收标准

- 明确采用 `src/career_agent` package。
- 明确 demo 使用 `demo/cli/` 和 `demo/streamlit/`。
- 明确第一阶段不引入 LangGraph、Chroma / FAISS、完整前后端。
- 明确后续任务的允许文件和禁止文件。
- 未修改禁改目录。

## 建议 commit message

```text
docs: finalize codebase structure plan for first implementation phase
```
