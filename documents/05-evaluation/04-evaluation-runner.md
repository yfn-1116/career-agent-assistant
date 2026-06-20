# 评估 Runner 使用说明

## 快速运行

```bash
PYTHONPATH=src python demo/evaluation/run_evaluation.py
cat outputs/demo/evaluation_report.md
```

## 默认配置

| 参数 | 默认值 |
|---|---|
| profile_dir | data/samples/profile |
| jobs_dir | data/samples/jobs |
| output_file | outputs/demo/evaluation_report.md |
| top_k | 5 |

## 自定义运行

```bash
PYTHONPATH=src python demo/evaluation/run_evaluation.py \
  --profile-dir data/samples/profile \
  --jobs-dir data/samples/jobs \
  --output-file outputs/demo/my_eval.md \
  --top-k 3
```

## 报告结构

1. **评估说明**：轻量评估的边界
2. **评估样例**：使用了哪些 JD
3. **总览表**：每个 JD 的 score、status、evidence count
4. **单样例详情**：每个检查项的结果
5. **结论**：平均 score 和系统优劣势

## 如何解读 total_score

- `0.8-1.0`：大部分检查通过，输出质量好
- `0.5-0.8`：部分检查未通过，需关注
- `0.0-0.5`：多个检查失败，需排查

注意：score 只反映**规则检查**，不反映语义质量。

## 局限

1. 只做规则检查，不做语义判断
2. keyword_coverage 基于字符串匹配，不能判断语义相关性
3. 不评估 resume_bullets 的实际可用性
4. 不评估 communication_message 的自然度

## 后续增强

1. 接入 LLM-as-judge 做语义质量评估
2. 人工标注集做 precision/recall
3. 对比规则型 vs LLM 型的 score 差异
4. 增加更多评估维度（生成内容长度、重复度、可读性）
