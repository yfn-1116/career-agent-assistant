# RAG-005 RAGPipeline 集成

## 任务编号

RAG-005

## 建议执行者

Codex

## 任务目标

集成 loader、chunker、VectorStore、retriever，形成第一阶段 `RAGPipeline`。

## 允许修改文件

- `src/career_agent/rag/retrievers/__init__.py`
- `src/career_agent/rag/retrievers/simple_retriever.py`
- `src/career_agent/rag/pipeline.py`
- `tests/rag/test_rag_pipeline.py`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/career_agent/agents/`
- `src/career_agent/workflows/`
- `demo/`
- `outputs/`
- `pyproject.toml`
- `requirements.txt`

## 输入

- RAG-001 到 RAG-004 的实现。
- 本地 Markdown 资料路径。
- 检索 query。

## 输出

- `SimpleRetriever`
- `RAGPipeline`
- pipeline 集成测试。

## 实现要求

- 只集成 RAG，不解析 JD。
- 不生成简历。
- 不调用 Agent workflow。
- 检索结果返回 `RetrievedEvidence`。

## 测试命令

```bash
pytest tests/rag/test_rag_pipeline.py -v
git status --short
```

## 验收标准

- 固定 query 能返回相关 evidence。
- evidence 包含 source、quote、score、reason。
- 资料不足时返回空结果或清晰提示。

## 建议 commit message

```text
feat: integrate rag pipeline
```
