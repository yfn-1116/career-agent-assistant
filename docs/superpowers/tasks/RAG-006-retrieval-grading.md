# RAG-006 检索评分与诊断报告

## 任务编号

RAG-006

## 建议执行者

Codex

## 任务目标

实现规则型 RAG 检索质量评分，为每次 workflow 运行输出可解释的 `RetrievalGradeReport`。

## 允许修改文件

- `src/career_agent/rag/grading.py`
- `src/career_agent/rag/__init__.py`
- `src/career_agent/agents/state.py`
- `tests/rag/test_retrieval_grading.py`
- `documents/02-design/02-rag-module-design.md`
- `documents/05-evaluation/01-rag-evaluation.md`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/career_agent/rag/loaders/`
- `src/career_agent/rag/chunking/`
- `src/career_agent/rag/vectorstores/`
- `src/career_agent/rag/embeddings/`
- `src/career_agent/agents/` 单个 Agent 行为，除 `state.py` 状态字段外。
- `src/career_agent/workflows/`，除非由 WORKFLOW-002 调用。
- `demo/`
- `outputs/`

## 输入

- `ParsedJD`
- `RetrievedEvidence`
- retrieval query
- top_k

## 输出

- `RetrievalGradeItem`
- `RetrievalGradeReport`
- `grade_retrieval(...)`

## 实现要求

- 评分必须本地、确定性、无网络依赖。
- 检查项包括 `evidence_count`、`average_score`、`keyword_coverage`、`source_diversity`、`traceability`。
- 等级为 `excellent`、`good`、`weak`、`failed`。
- 每条 evidence summary 包含 title、score、source_path、matched_keywords、snippet。
- 不把该报告混入批量 `EvaluationReport`，但评估文档需要说明两者区别。

## 测试命令

```bash
pytest tests/rag/test_retrieval_grading.py -v
pytest tests/rag -q
git status --short
```

## 验收标准

- 无 evidence 时 grade 为 `failed`。
- evidence 充足且关键词覆盖较好时 grade 至少为 `good`。
- traceability 缺失时关键检查失败。
- 返回报告可直接用于 CLI 和 Streamlit 展示。

## 建议 commit message

```text
feat: add retrieval grading report
```
