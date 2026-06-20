# career-agent-assistant

## 项目定位

`career-agent-assistant` 是一个面向大学生实习求职场景的 RAG + 多 Agent MVP 原型。它不是完整求职平台，也不是普通简历生成器，而是用来验证个人能力知识库、岗位理解、匹配分析和求职材料生成这一条核心链路。

## 核心模块

- **RAG 用户资料知识库**：将本地 Markdown 简历、项目经历、GitHub 仓库摘要、课程项目、实习经历、技能材料等整理为可检索资料。
- **多 Agent 编排**：围绕 JD 解析、资料检索、匹配分析、简历项目描述生成、HR / mentor 沟通话术生成等任务拆分职责。
- **文档先行工程流程**：所有实现任务先进入 `documents/` 和 `docs/superpowers/`，再进入代码实现。
- **本地开发到服务器展示**：本地验证后推送 GitHub，再由学校服务器拉取并复现 demo。

## 第一阶段目标

第一阶段跑通以下链路：

```text
本地用户资料 Markdown
→ RAG 检索
→ JD 解析
→ 匹配分析
→ 简历项目描述 / 沟通话术生成
→ CLI / Streamlit 展示
```

第一阶段采用 CLI + Markdown 输出 + Streamlit 轻量可视化展示，暂不做完整 frontend/backend/server 分离架构。所有 Agent 使用规则和模板实现，不依赖外部大模型 API，保证可复现。

## 当前状态

### 已完成

| 模块 | 内容 | 测试 |
|---|---|---|
| RAG MVP | schema / loader / chunker / vectorstore / retriever / pipeline | 61 passed |
| Agent MVP | AgentTaskState / JDParserAgent / RAGRetrieveAgent / MatchAnalysisAgent / BuildAgent | 68 passed |
| Workflow MVP | JobMatchWorkflow（串联全部 Agent） | 11 passed |
| CLI Demo | 命令行 demo，输出 Markdown 报告 | 10 passed |
| Streamlit Demo | 轻量可视化展示页面 | 15 static checks |
| 文档体系 | 设计文档 / 技术决策 / 任务卡 / 运行手册 / 部署文档 | — |
| 样例数据 | 5 份用户资料 + 4 份岗位 JD（脱敏虚构） | — |

**总计：165 个测试全部通过，零外部依赖。**

### 快速运行

```bash
git clone https://github.com/yfn-1116/career-agent-assistant.git
cd career-agent-assistant

# 运行全部测试
PYTHONPATH=src pytest tests/rag tests/agents tests/workflows tests/demo -v

# 运行 CLI demo（默认稳定展示方式）
PYTHONPATH=src python demo/cli/run_job_match_demo.py

# 查看输出
cat outputs/demo/job_match_result.md

# 可选：Streamlit 可视化展示
pip install streamlit
PYTHONPATH=src streamlit run demo/streamlit/app.py

# 可选：启用 LLM 增强（需要 DeepSeek API Key）
export DEEPSEEK_API_KEY=你的key
# 代码中 BuildAgent(use_llm=True) 即可切换
```

## 项目结构

```text
src/career_agent/
├── rag/           # RAG pipeline（loader, chunker, vectorstore, retriever, pipeline）
├── agents/        # AgentTaskState + JDParser/RAGRetrieve/MatchAnalysis/Build
├── workflows/     # JobMatchWorkflow
└── models/        # ModelProvider / MockProvider / DeepSeekProvider

demo/
├── cli/           # CLI demo 入口
└── streamlit/     # Streamlit 可视化 demo

data/samples/
├── profile/       # 脱敏示例用户资料（5 文件）
└── jobs/          # 脱敏示例岗位 JD（4 文件）

tests/
├── rag/           # 61 tests
├── agents/        # 68 tests
├── workflows/     # 11 tests
└── demo/          # 25 tests (10 CLI + 15 Streamlit static)

documents/         # 设计文档、技术决策、运行手册、部署文档、日志、规划
docs/superpowers/  # AI 协作规范与任务卡
```

## 后续开发计划

```text
✅ RAG schema → pipeline
✅ AgentTaskState → 核心 Agent
✅ Workflow 集成
✅ CLI demo
✅ Streamlit demo
✅ 学校服务器部署文档
⏳ 接入 LLM API（DeepSeek / OpenAI）
⏳ LangGraph 状态图迁移（可选）
```

## 协作规则

- **Codex** 负责核心架构、核心接口、RAG / Agent 集成和疑难修复。
- **Claude Code + DeepSeek** 负责边界清晰的文档补全、样例数据、局部模块、测试和 demo。
- **ChatGPT + User** 负责方案讨论、任务拆分和需求确认。
- 所有执行任务必须先有 `docs/superpowers/tasks/` 下的任务说明。
