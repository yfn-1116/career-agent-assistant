# AGENT-003 RAGRetrieveAgent 实现

## 任务编号

AGENT-003

## 建议执行者

Claude Code + DeepSeek

## 任务目标

只实现调用 RAG pipeline 的检索 Agent，返回 `RetrievedEvidence`。

## 允许修改文件

- `src/agents/rag_retrieve.py`
- `tests/agents/test_rag_retrieve.py`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/rag/pipeline.py`
- `src/rag/schemas.py`
- `src/workflows/`
- demo 文件

## 输入

- `parsed_jd`
- RAG pipeline 实例或接口

## 输出

- `retrieved_evidence`

## 实现要求

- 不改 RAG pipeline。
- 不做匹配分析。
- 不生成最终输出。

## 验收标准

- 能根据 `parsed_jd` 发起检索。
- 返回 evidence 列表。
- RAG 无结果时状态清晰。

## 测试命令

```bash
pytest tests/agents/test_rag_retrieve.py -v
git status --short
```

## 提交信息建议

```text
feat: add rag retrieve agent
```
