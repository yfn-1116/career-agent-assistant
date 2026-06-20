# RAG-005 RAGPipeline 集成

## 任务编号

RAG-005

## 建议执行者

Codex

## 任务目标

集成 loader、chunker、vector store 和 retriever，形成第一阶段 RAG pipeline。

## 允许修改文件

- `src/rag/pipeline.py`
- `src/rag/retriever.py`
- `tests/rag/test_rag_pipeline.py`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/agents/`
- `src/workflows/`
- Streamlit demo
- 部署脚本
- 依赖配置文件，除非任务另有授权

## 输入

- 本地 Markdown 资料路径。
- 检索 query。

## 输出

- `RetrievedEvidence` 列表。

## 实现要求

- 使用既有 schema、loader、chunker 和 vector store。
- 不生成简历。
- 不解析 JD。

## 验收标准

- 固定样例 query 能返回相关 evidence。
- evidence 包含来源路径、quote 和 score。
- 资料不足时返回空结果或清晰提示。

## 测试命令

```bash
pytest tests/rag/test_rag_pipeline.py -v
git status --short
```

## 提交信息建议

```text
feat: integrate rag pipeline
```
