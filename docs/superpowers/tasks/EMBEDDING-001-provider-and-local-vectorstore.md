# EMBEDDING-001 Embedding Provider 抽象

## 任务编号

EMBEDDING-001

## 建议执行者

Claude Code + DeepSeek

## 任务目标

实现 EmbeddingProvider 抽象接口和 HashEmbeddingProvider，为语义检索预留结构。

## 允许修改

- src/career_agent/rag/embeddings/
- tests/rag/test_embedding_provider.py
- documents/97-journal.md
- documents/99-project-planning.md

## 禁止修改

- src/career_agent/rag/schemas.py
- src/career_agent/rag/vectorstores/
- src/career_agent/rag/pipeline.py
- src/career_agent/agents/

## 测试命令

```bash
PYTHONPATH=src pytest tests/rag/test_embedding_provider.py -v
PYTHONPATH=src pytest tests/rag tests/agents tests/workflows tests/demo tests/models tests/evaluation tests/github -v
```

## 验收标准

- EmbeddingProvider 接口可用
- HashEmbeddingProvider 确定性输出
- 不引入第三方依赖
- 现有 236 tests 全部通过

## 提交信息

```text
feat: add embedding provider abstraction with hash implementation
```
