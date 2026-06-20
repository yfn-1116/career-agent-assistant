# RAG-002 MarkdownProfileLoader 实现

## 任务编号

RAG-002

## 建议执行者

Claude Code + DeepSeek

## 任务目标

实现 `MarkdownProfileLoader`，只负责读取本地 Markdown 用户资料并转换为 RAG-001 已定义的 schema。

## 允许修改文件

- `src/career_agent/rag/loaders/__init__.py`
- `src/career_agent/rag/loaders/markdown_loader.py`
- `tests/rag/test_markdown_loader.py`
- `data/samples/profile/`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/career_agent/rag/schemas.py`，除非 RAG-001 已完成且仅使用已有 schema。
- `src/career_agent/agents/`
- `src/career_agent/workflows/`
- `src/career_agent/rag/chunking/`
- `src/career_agent/rag/vectorstores/`
- `demo/`
- `outputs/`

## 输入

- RAG-001 schema。
- `data/samples/profile/` 中的 Markdown 样例。

## 输出

- Markdown loader。
- loader 单元测试。
- 脱敏 profile 样例。

## 实现要求

- 不做 chunking。
- 不调用模型。
- 不写向量库。
- 不做 Agent 集成。

## 测试命令

```bash
pytest tests/rag/test_markdown_loader.py -v
git status --short
```

## 验收标准

- 能读取 Markdown 文件并保留来源路径。
- 能识别标题、分区和条目。
- 空文件、缺失文件有清晰错误。

## 建议 commit message

```text
feat: add markdown profile loader
```
