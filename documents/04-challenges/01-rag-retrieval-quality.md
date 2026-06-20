# RAG 检索质量

## 问题描述

RAG 可能检索不到正确经历，或者返回与 JD 关系弱的资料，导致后续匹配分析和生成内容偏离真实背景。

## 风险影响

- 简历描述无法突出岗位相关能力。
- 生成内容引用错误证据。
- 用户误判岗位匹配程度。

## 初步解决策略

- 为 `ProfileItem` 增加类型、技术栈、岗位方向等 metadata。
- chunk 保留来源路径和资料项 ID。
- 检索结果返回 `RetrievedEvidence`，包含 quote、score 和 reason。
- 准备固定 demo case 评估检索命中。

## 第一阶段处理方式

第一阶段先使用小规模本地 Markdown 样例，重点验证“能否找到正确经历”，不追求大规模语义检索性能。

## 后续优化方向

- 引入 Chroma / FAISS。
- 优化 chunk 策略。
- 增加混合检索。
- 增加人工标注评估集。

## 后续维护规则

检索策略变化必须同步更新 `documents/05-evaluation/01-rag-evaluation.md`。
