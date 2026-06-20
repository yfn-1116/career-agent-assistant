# RAG-004 VectorStore 接口设计与实现

## 任务编号

RAG-004

## 建议执行者

Codex

## 任务目标

设计并实现 `VectorStore` 接口，使后续 memory、Chroma、FAISS 实现可以替换。

## 允许修改文件

- `src/rag/vectorstore.py`
- `tests/rag/test_vectorstore.py`
- `documents/03-technical-decisions/03-vector-store-selection.md`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/agents/`
- `src/workflows/`
- `data/`
- `outputs/`
- Streamlit 或 demo 文件

## 输入

- `DocumentChunk`
- 查询文本
- metadata 过滤条件

## 输出

- 检索结果和 score。

## 实现要求

- 接口不能绑定 Chroma 或 FAISS。
- 第一版可包含 memory 实现。
- 返回结果必须能转换为 `RetrievedEvidence`。

## 验收标准

- 接口方法清晰。
- memory store 可通过单元测试。
- 后续可扩展本地持久化。

## 测试命令

```bash
pytest tests/rag/test_vectorstore.py -v
git status --short
```

## 提交信息建议

```text
feat: add vector store interface
```
