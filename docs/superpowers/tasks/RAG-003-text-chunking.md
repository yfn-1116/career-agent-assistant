# RAG-003 文本清洗与 Chunk 切分

## 任务编号

RAG-003

## 建议执行者

Claude Code + DeepSeek

## 任务目标

实现文本清洗与 chunk 切分，将 `ProfileDocument` 或 `ProfileItem` 转换为 `DocumentChunk`。

## 允许修改文件

- `src/career_agent/rag/chunking/__init__.py`
- `src/career_agent/rag/chunking/text_chunker.py`
- `tests/rag/test_text_chunker.py`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/career_agent/rag/schemas.py`
- `src/career_agent/rag/loaders/`
- `src/career_agent/rag/vectorstores/`
- `src/career_agent/agents/`
- `src/career_agent/workflows/`
- `data/`
- `outputs/`

## 输入

- RAG-001 schema。
- RAG-002 loader 输出。

## 输出

- TextChunker。
- chunking 单元测试。

## 实现要求

- 不调用模型。
- 不写向量库。
- 不做 pipeline 集成。
- chunk 必须保留 source、item_id、document_id 等 metadata。

## 测试命令

```bash
pytest tests/rag/test_text_chunker.py -v
git status --short
```

## 验收标准

- chunk 长度受控。
- metadata 不丢失。
- 空文本和短文本处理稳定。

## 建议 commit message

```text
feat: add rag text chunker
```
