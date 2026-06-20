# Demo Case 评估

## 目标

确保 4 个示例 JD 的运行结果稳定、可对比、可复现。

## 当前 Demo JD

| JD 文件 | 方向 | 预期评估特点 |
|---|---|---|
| agent_intern_jd.md | agent | evidence 丰富，得分较高 |
| rag_engineer_intern_jd.md | rag | RAG 关键词覆盖好 |
| ai_application_intern_jd.md | ai_application | 香港岗位，部分技能覆盖 |
| backend_ai_intern_jd.md | backend | 后端技能覆盖 |

## 运行方式

```bash
PYTHONPATH=src python demo/evaluation/run_evaluation.py
cat outputs/demo/evaluation_report.md
```

## 稳定性要求

- 每次运行相同 JD，规则型 Agent 输出一致
- score 应稳定（因规则型无随机性）
- 后续接入 LLM 后，score 可能有波动，需记录

## 后续增强

- 增加更多 JD 类型
- 对比规则型 vs LLM 型的 score 差异
