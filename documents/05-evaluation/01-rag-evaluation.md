# RAG 评估

## 评估目标

检查 RAG pipeline 是否能根据岗位 JD 检索到正确的用户经历，并返回可追溯证据。

## 当前检查项

### 批量评估检查（EvaluationReport）

| 检查 | 规则 | 说明 |
|---|---|---|
| evidence_count | retrieved_evidence 非空 | 检索是否返回了至少一条证据 |
| keyword_coverage | JD 关键词在 evidence 中的覆盖率 | 检索方向和 JD 需求是否相关 |
| evidence_refs | 输出引用是否可追溯 | 生成的 bullet 是否关联到检索证据 |

### 单次检索诊断（RetrievalGradeReport）

| 指标 | 规则 | 说明 |
|---|---|---|
| evidence_count | evidence 非空 | 单次检索是否返回证据 |
| average_score | evidence score 平均值达到阈值 | 检索结果整体相关性是否足够 |
| keyword_coverage | JD hard_skills / bonus_skills / keywords 在 matched_keywords 或 evidence content 中覆盖 | 检索结果是否覆盖关键岗位要求 |
| source_diversity | evidence 来源数量达到目标 | 结果是否过度集中于单一来源 |
| traceability | 每条 evidence 有 source_path、chunk_id 和 finite normalized score `0.0-1.0` | 诊断结果是否可追溯到原始证据 |

## RetrievalGradeReport 与 EvaluationReport

`RetrievalGradeReport` 是单次 RAG 检索诊断报告，用于检查一次 query 的 evidence 数量、平均分、关键词覆盖、来源多样性和可追溯性。

`EvaluationReport` 是批量 / 多 JD 评估报告，用于汇总多个测试用例的整体结果。

二者互补：`RetrievalGradeReport` 帮助定位单次检索质量问题，`EvaluationReport` 帮助观察整体评估表现，彼此不替代。

## 运行方式

```bash
PYTHONPATH=src python demo/evaluation/run_evaluation.py
cat outputs/demo/evaluation_report.md
```

## 关键词检索 vs Embedding 检索

| 维度 | MemoryVectorStore | EmbeddingVectorStore |
|---|---|---|
| 匹配方式 | 关键词 Token 重叠 | Hash trigram 余弦相似度 |
| 语义理解 | 无 | 无；仅提供 lexical / fuzzy substring similarity |
| 外部依赖 | 无 | 无 |
| 生产可用 | 否 | 否 |

当前默认使用 MemoryVectorStore。EmbeddingVectorStore 是可选验证路径，不等同于生产级语义检索。

## 后续增强方向

- 建立小型人工标注集（标注"这条 evidence 是否真的与 JD 相关"）
- 记录 query → 期望命中 → 实际命中
- 计算 precision / recall
- 接入 Embedding 检索后对比效果
