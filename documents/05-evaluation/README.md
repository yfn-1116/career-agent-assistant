# 评估文档目录

## 用途

本目录定义 RAG、Agent 输出和 demo case 的评估方式，确保项目输出可信、可复现、可解释。

## 文档索引

| 文件 | 用途 |
|---|---|
| `01-rag-evaluation.md` | RAG 检索质量评估 |
| `02-agent-output-evaluation.md` | Agent 输出质量评估 |
| `03-demo-case-evaluation.md` | Demo case 评估 |
| `04-evaluation-runner.md` | 评估 runner 使用说明 |

## 当前状态

已实现轻量评估模块（`src/career_agent/evaluation/`）：

- 5 条评估规则：status / evidence count / output non-empty / evidence refs / keyword coverage
- 评估 runner：`demo/evaluation/run_evaluation.py`，对 4 个示例 JD 批量评估
- 输出：`outputs/demo/evaluation_report.md`

运行方式：

```bash
PYTHONPATH=src python demo/evaluation/run_evaluation.py
```

## 评估边界

- 当前为**第一阶段轻量评估**，使用规则检查，不依赖外部模型
- 不替代人工检查，不声称是严格学术 benchmark
- 后续可接入 LLM-as-judge 或人工标注集做更深度评估

## 后续维护规则

- 评估标准必须能人工检查或自动化验证
- 不允许只用"效果不错"作为验收结论
- RAG / Agent 逻辑变更后重新运行评估 runner
