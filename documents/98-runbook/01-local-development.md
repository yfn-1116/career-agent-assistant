# 本地开发环境

## 1. 克隆仓库

```bash
git clone https://github.com/yfn-1116/career-agent-assistant.git
cd career-agent-assistant
```

## 2. 环境要求

- Python 3.10 或以上
- pytest（用于运行测试）

安装 pytest：

```bash
pip install pytest
```

本项目**默认不依赖外部大模型**，第一阶段所有 Agent 使用规则和模板生成。无需配置 API Key。

### 可选：启用 LLM 增强

```bash
export DEEPSEEK_API_KEY=你的key
```

BuildAgent 支持可选 LLM 生成（`use_llm=True`），失败时自动回退规则型。详见 `documents/03-technical-decisions/07-model-provider-abstraction.md`。

## 3. 运行全部测试

```bash
PYTHONPATH=src pytest tests/rag tests/agents tests/workflows tests/demo -v
```

预期结果：约 150 个测试全部通过。

## 4. 运行 CLI demo

默认运行（使用示例 AI Agent 实习 JD）：

```bash
PYTHONPATH=src python demo/cli/run_job_match_demo.py
```

自定义参数：

```bash
PYTHONPATH=src python demo/cli/run_job_match_demo.py \
  --profile-dir data/samples/profile \
  --job-file data/samples/jobs/rag_engineer_intern_jd.md \
  --output-file outputs/demo/rag_engineer_result.md \
  --top-k 3
```

## 5. 查看输出

```bash
cat outputs/demo/job_match_result.md
```

或在编辑器中打开该文件。

## 6. 项目结构速览

```text
src/career_agent/
├── rag/           # RAG pipeline（loader, chunker, vectorstore, retriever）
├── agents/        # 四个 Agent + 共享状态
└── workflows/     # JobMatchWorkflow 编排

demo/cli/          # CLI demo 入口

data/samples/
├── profile/       # 示例用户资料
└── jobs/          # 示例岗位 JD

tests/
├── rag/           # RAG 单元测试
├── agents/        # Agent 单元测试
├── workflows/     # Workflow 集成测试
└── demo/          # Demo smoke test

documents/         # 设计文档、决策记录、运行手册
```

## 7. 常见问题

### ModuleNotFoundError: No module named 'career_agent'

需要设置 `PYTHONPATH=src`：

```bash
PYTHONPATH=src python demo/cli/run_job_match_demo.py
```

### pytest: command not found

```bash
pip install pytest
```

### outputs/demo 目录不存在

CLI demo 会自动创建输出目录。如果手动运行，可以先创建：

```bash
mkdir -p outputs/demo
```

### 路径错误

确保命令在项目根目录（`career-agent-assistant/`）下执行。
