# RAG-004 VectorStore 接口与 Memory 实现

## 任务编号

RAG-004

## 建议执行者

Codex

## 任务目标

设计并实现 `VectorStore` 接口和第一阶段 `MemoryVectorStore`，为后续 Chroma / FAISS 替换预留边界。

## 允许修改文件

- `src/career_agent/rag/vectorstores/__init__.py`
- `src/career_agent/rag/vectorstores/base.py`
- `src/career_agent/rag/vectorstores/memory_store.py`
- `tests/rag/test_vectorstore_interface.py`
- `documents/03-technical-decisions/03-vector-store-selection.md`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/career_agent/agents/`
- `src/career_agent/workflows/`
- `src/career_agent/rag/loaders/`
- `src/career_agent/rag/chunking/`
- `demo/`
- `data/`
- `outputs/`
- Chroma / FAISS 依赖配置。

## 输入

- `DocumentChunk`
- 查询文本或向量。
- top_k 参数。

## 输出

- `VectorStore` 接口。
- `MemoryVectorStore`。
- 接口测试。

## 实现要求

- 不绑定 Chroma / FAISS。
- 不调用 Agent。
- 不生成最终输出。
- 返回结果必须能转换为 `RetrievedEvidence`。

## 测试命令

```bash
pytest tests/rag/test_vectorstore_interface.py -v
git status --short
```

## 验收标准

- 接口方法清晰。
- Memory 实现可新增和查询 chunk。
- 后续可替换具体向量库。

## 建议 commit message

```text
feat: add vector store interface
```
