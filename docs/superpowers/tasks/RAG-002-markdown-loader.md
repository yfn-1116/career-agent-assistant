# RAG-002 MarkdownProfileLoader 实现

## 任务编号

RAG-002

## 建议执行者

Claude Code + DeepSeek

## 任务目标

只实现 `MarkdownProfileLoader`，将本地 Markdown 用户资料加载为后续 schema 可消费的数据结构。

## 允许修改文件

- `src/rag/markdown_loader.py`
- `tests/rag/test_markdown_loader.py`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/rag/schemas.py`
- `src/agents/`
- `src/workflows/`
- `data/`
- `outputs/`
- 依赖配置文件

## 输入

- RAG schema 设计文档。
- `data/samples/` 中的示例 Markdown。

## 输出

- Markdown 加载器。
- 对应测试。

## 实现要求

- 不修改 schema。
- 不做 chunking。
- 不调用模型。
- 不调用向量库。

## 验收标准

- 能读取指定 Markdown 文件。
- 能保留来源路径和标题。
- 异常文件路径有清晰错误。

## 测试命令

```bash
pytest tests/rag/test_markdown_loader.py -v
git status --short
```

## 提交信息建议

```text
feat: add markdown profile loader
```
