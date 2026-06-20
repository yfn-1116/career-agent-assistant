# RAG-003 文本清洗与 Chunk 切分

## 任务编号

RAG-003

## 建议执行者

Claude Code + DeepSeek

## 任务目标

只实现文本清洗与 chunk 切分能力，为检索索引提供稳定 `DocumentChunk`。

## 允许修改文件

- `src/rag/text_chunker.py`
- `tests/rag/test_text_chunker.py`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/rag/schemas.py`
- `src/rag/vectorstore.py`
- `src/agents/`
- `src/workflows/`
- `data/`
- `outputs/`

## 输入

- `ProfileDocument` 或文本段落。
- chunk size 和 overlap 配置。

## 输出

- `DocumentChunk` 列表。
- chunk metadata。

## 实现要求

- 不调用模型。
- 不写向量库。
- 不做 RAG pipeline 集成。

## 验收标准

- chunk 长度受控。
- 保留 document_id、item_id、source_path 等 metadata。
- 空文本和短文本处理稳定。

## 测试命令

```bash
pytest tests/rag/test_text_chunker.py -v
git status --short
```

## 提交信息建议

```text
feat: add rag text chunker
```
