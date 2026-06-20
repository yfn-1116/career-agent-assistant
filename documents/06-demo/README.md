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

- **CLI Demo**：默认稳定展示方式
- **Streamlit Demo**：可选可视化展示方式

### CLI Demo

```bash
PYTHONPATH=src python demo/cli/run_job_match_demo.py
```

### Streamlit Demo

```bash
pip install streamlit
PYTHONPATH=src streamlit run demo/streamlit/app.py
```

两种 demo 都只调用 JobMatchWorkflow，不重写核心业务逻辑。

## 重要说明

- Demo 不等于生产部署，仅用于展示 RAG + Agent workflow
- 当前不调用外部大模型，保证可复现
- 所有 demo 输入为脱敏虚构样例
