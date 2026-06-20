# MODEL-001 模型 Provider 抽象与 DeepSeek 可选接入

## 任务编号

MODEL-001

## 建议执行者

Claude Code + DeepSeek

## 任务目标

在不破坏规则型 MVP 的前提下，增加可选 LLM Provider 能力。

## 允许修改文件

- src/career_agent/models/
- tests/models/
- src/career_agent/agents/build_agent.py
- tests/agents/test_build_agent.py
- demo/cli/run_job_match_demo.py
- demo/streamlit/app.py
- tests/demo/
- README.md
- documents/98-runbook/
- documents/03-technical-decisions/07-model-provider-abstraction.md
- documents/97-journal.md
- documents/99-project-planning.md

## 禁止修改文件

- src/career_agent/rag/
- src/career_agent/agents/jd_parser.py
- src/career_agent/agents/rag_retrieve_agent.py
- src/career_agent/agents/match_analysis_agent.py
- src/career_agent/workflows/
- tests/rag/
- tests/agents/test_jd_parser.py
- tests/agents/test_rag_retrieve_agent.py
- tests/agents/test_match_analysis_agent.py
- data/samples/
- .env

## 输入

- Phase 1 MVP 代码
- DeepSeek API 文档

## 输出

- ModelProvider 接口
- MockProvider
- DeepSeekProvider
- BuildAgent 可选 LLM 支持
- Demo 层 LLM 说明

## 验收标准

- 165+ 测试全部通过
- 默认不依赖外部 API
- 无 API Key 时所有功能可用
- 不引入第三方依赖
- API Key 不写入代码或提交

## 测试命令

```bash
PYTHONPATH=src pytest tests/models -v
PYTHONPATH=src pytest tests/rag tests/agents tests/workflows tests/demo tests/models -v
```

## 提交信息建议

```text
feat: add model provider abstraction with deepseek support
```
