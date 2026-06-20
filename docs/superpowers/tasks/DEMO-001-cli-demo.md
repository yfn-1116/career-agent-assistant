# DEMO-001 CLI Demo

## 任务编号

DEMO-001

## 建议执行者

Claude Code + DeepSeek 或 Codex

## 任务目标

实现第一阶段 CLI demo，只调用已有 workflow，输出 Markdown 结果。

## 允许修改文件

- `src/demo/cli_demo.py`
- `tests/demo/test_cli_demo.py`
- `outputs/demo/`
- `documents/06-demo/01-demo-script.md`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- RAG 底层实现
- Agent 核心逻辑
- workflow 核心逻辑
- Streamlit 页面
- frontend/backend/server 目录

## 输入

- 示例用户资料。
- 示例 JD。
- 已有 workflow。

## 输出

- Markdown demo 输出文件。
- 终端摘要。

## 实现要求

- 只调用已有 workflow。
- 不重新实现业务逻辑。
- 路径可配置或使用固定样例路径。

## 验收标准

- 本地命令能跑通。
- 输出包含 JD 解析、检索证据、匹配分析和最终内容。
- 模型不可用时有明确错误或兜底路径。

## 测试命令

```bash
pytest tests/demo/test_cli_demo.py -v
git status --short
```

## 提交信息建议

```text
feat: add cli demo for first phase workflow
```
