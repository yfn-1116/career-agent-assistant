# DEMO-002 Streamlit 轻量展示

## 任务编号

DEMO-002

## 建议执行者

Claude Code + DeepSeek

## 任务目标

实现 Streamlit 轻量展示层，调用已有 workflow 展示输入、证据、匹配分析和输出。

## 允许修改文件

- `src/demo/streamlit_app.py`
- `documents/06-demo/03-presentation-flow.md`
- `documents/98-runbook/03-school-server-deploy.md`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/rag/`
- `src/agents/`
- `src/workflows/`
- frontend/backend/server 目录
- 核心业务逻辑

## 输入

- 已有 workflow。
- 示例资料和 JD。

## 输出

- Streamlit 展示页面。

## 实现要求

- 只做展示层。
- 不在 Streamlit 中写 RAG、Agent 或 workflow 核心逻辑。
- 提供学校服务器运行说明。

## 验收标准

- 页面能展示固定 demo 输入和输出。
- 核心逻辑来自 workflow。
- CLI demo 仍然可独立运行。

## 测试命令

```bash
git status --short
```

## 提交信息建议

```text
feat: add streamlit demo shell
```
