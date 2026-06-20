# DEMO-002 Streamlit 轻量展示

## 任务编号

DEMO-002

## 建议执行者

Claude Code + DeepSeek

## 任务目标

实现 Streamlit 轻量展示层，调用已有 workflow 展示输入、证据、匹配分析和最终输出。

## 允许修改文件

- `demo/streamlit/app.py`
- `documents/06-demo/`
- `documents/98-runbook/03-school-server-deploy.md`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/career_agent/rag/`
- `src/career_agent/agents/`
- `src/career_agent/workflows/`
- `demo/cli/`
- `frontend/`
- `backend/`
- `server/`
- `app/`

## 输入

- 已有 workflow。
- 示例资料和 JD。
- CLI demo 的稳定输出格式。

## 输出

- `demo/streamlit/app.py`
- Streamlit 展示文档。

## 实现要求

- 只做展示层。
- 不在 Streamlit 中写 RAG、Agent 或 workflow 核心逻辑。
- 不创建 `app/streamlit_app.py`。

## 测试命令

```bash
git status --short
```

## 验收标准

- 页面能展示固定 demo 输入和输出。
- 核心逻辑来自 workflow。
- CLI demo 仍可独立运行。

## 建议 commit message

```text
feat: add streamlit demo for workflow output
```
