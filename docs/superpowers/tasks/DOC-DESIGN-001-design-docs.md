# DOC-DESIGN-001 设计文档补强

## 任务编号

DOC-DESIGN-001

## 建议执行者

Claude Code + DeepSeek，关键结论需 Codex 复核。

## 任务目标

补充 RAG、多 Agent、状态、数据流和 GitHub 仓库摘要设计文档。

## 允许修改文件

- `documents/02-design/`
- `documents/04-challenges/`
- `documents/05-evaluation/`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/`
- `tests/`
- `data/`
- `outputs/`
- `.env.example`
- 依赖配置文件

## 输入

- `documents/00-project-overview.md`
- `documents/01-requirements/`
- ChatGPT + User 已确认的方案。

## 输出

- 模块边界、输入输出、数据流、风险和评估框架。

## 实现要求

- 只写中文 Markdown。
- 不实现 RAG 或 Agent。
- 核心 schema 只描述方向，具体设计交给 Codex 任务。

## 验收标准

- 明确第一阶段四个核心 Agent。
- 明确 RAG 只处理本地 Markdown 和 GitHub 摘要。
- 明确 CLI + Streamlit 展示边界。

## 测试命令

```bash
git status --short
find documents/02-design documents/04-challenges documents/05-evaluation -name '*.md' -type f -empty -print
```

## 提交信息建议

```text
docs: expand rag and agent design documents
```
