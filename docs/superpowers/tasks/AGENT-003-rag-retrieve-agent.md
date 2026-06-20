# AGENT-003 RAGRetrieveAgent 实现

## 任务编号

AGENT-003

## 建议执行者

Claude Code + DeepSeek

## 任务目标

实现 `RAGRetrieveAgent`，只负责根据 `parsed_jd` 调用 RAG pipeline 并返回 `RetrievedEvidence`。

## 允许修改文件

- `src/career_agent/agents/rag_retrieve_agent.py`
- `tests/agents/test_rag_retrieve_agent.py`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/career_agent/rag/pipeline.py`
- `src/career_agent/rag/schemas.py`
- `src/career_agent/workflows/`
- `src/career_agent/agents/jd_parser.py`
- `src/career_agent/agents/match_analysis_agent.py`
- `src/career_agent/agents/build_agent.py`
- `demo/`

## 输入

- `parsed_jd`
- RAG pipeline 实例或接口。

## 输出

- `retrieved_evidence`

## 实现要求

- 不修改 RAG pipeline。
- 不做匹配分析。
- 不生成最终输出。

## 测试命令

```bash
pytest tests/agents/test_rag_retrieve_agent.py -v
git status --short
```

## 验收标准

- 能根据 `parsed_jd` 发起检索。
- 返回 evidence 列表。
- RAG 无结果时状态清晰。

## 建议 commit message

```text
feat: add rag retrieve agent
```
