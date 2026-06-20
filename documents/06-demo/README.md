# Demo 文档目录

## 用途

本目录组织第一阶段 demo 的脚本、数据说明和展示流程。

## 文档索引

| 文件 | 用途 |
|---|---|
| `01-demo-script.md` | CLI demo 展示脚本与讲解要点 |
| `02-demo-data.md` | 示例数据说明与使用建议 |
| `03-presentation-flow.md` | 答辩 / 展示流程设计 |

## 当前阶段

Phase 1：**CLI Demo 已完成**。运行方式：

```bash
PYTHONPATH=src python demo/cli/run_job_match_demo.py
```

输出 `outputs/demo/job_match_result.md`。

后续将开发 Streamlit demo（Phase 2），届时只调用已有 workflow，不在页面内写核心逻辑。

## 重要说明

- Demo 不等于生产部署，仅用于展示 RAG + Agent workflow
- 当前不调用外部大模型，保证可复现
- 所有 demo 输入为脱敏虚构样例
