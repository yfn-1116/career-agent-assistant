# RAG 评估

## 评估目标

检查 RAG pipeline 是否能根据岗位 JD 检索到正确的用户经历，并返回可追溯证据。

## 当前检查项

| 检查 | 规则 | 说明 |
|---|---|---|
| evidence_count | retrieved_evidence 非空 | 检索是否返回了至少一条证据 |
| keyword_coverage | JD 关键词在 evidence 中的覆盖率 | 检索方向和 JD 需求是否相关 |
| evidence_refs | 输出引用是否可追溯 | 生成的 bullet 是否关联到检索证据 |

## 运行方式

```bash
PYTHONPATH=src python demo/evaluation/run_evaluation.py
cat outputs/demo/evaluation_report.md
```

## 关键词检索 vs Embedding 检索

| 维度 | MemoryVectorStore | EmbeddingVectorStore |
|---|---|---|
| 匹配方式 | 关键词 Token 重叠 | Hash trigram 余弦相似度 |
| 语义理解 | 无 | 有限（trigram 共享子串） |
| 外部依赖 | 无 | 无 |
| 生产可用 | 否 | 否 |

当前默认使用 MemoryVectorStore。EmbeddingVectorStore 是可选验证路径，不等同于生产级语义检索。

## 后续增强方向

- 建立小型人工标注集（标注"这条 evidence 是否真的与 JD 相关"）
- 记录 query → 期望命中 → 实际命中
- 计算 precision / recall
- 接入 Embedding 检索后对比效果
