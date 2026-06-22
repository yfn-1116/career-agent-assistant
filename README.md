# Internship Copilot / 实习求职投递管家 Agent

面向大学生实习求职场景的证据约束型 Internship Copilot 原型。

## 项目定位

**不是**：GPT 包装壳、自动投递机器人、招聘平台爬虫、一次性 JD 分析工具。

**是**：
- 维护用户**长期求职资料库**，区分"已实现/设计/计划/证据不足"；
- 根据 JD **自动检索真实经历**，每条建议绑定 evidence/source；
- **Evidence Gate** 阻止把"设计了"写成"实现了"，阻止编造经历；
- 输出**可追溯 diagnostics 和 report**；
- **长期追踪能力缺口**，告诉用户该补什么项目；
- **批量岗位匹配和投递记录**；
- 通过 **CLI / Streamlit / FastAPI / Browser Extension** 演示完整求职辅助链路。

## 核心能力

| 模块 | 功能 |
|------|------|
| Profile Knowledge Base | 结构化用户资料 (implemented/designed/planned/uncertain) |
| Evidence Gate | 校验生成内容是否符合 evidence 状态，降级/阻止不合规 claims |
| Hybrid RAG | 关键词 + 语义并行检索 + Reranker + 评分 |
| Job Matching Scorer | 5 因子评分 (coverage + evidence + relevance + confidence + gap) |
| Agentic Retry | 低分自动 rewrite_query 重试，耗尽后 fallback |
| Tool Registry | 15 个注册工具，受控调用 |
| Application Memory | JSONL 持久化投递记录 |
| Capability Gap | 跨岗位技能缺口分析 |
| Faithfulness | 生成内容忠实度检查 |
| Diagnostics | JSON + Markdown 全链路可观测 |
| AgentRunService | UI / API / CLI 调用核心 Agent 能力的统一服务入口 |

当前已跑通以下演示链路：

```text
本地用户资料 Markdown
→ RAG 检索
→ JD 解析
→ 匹配分析
→ 简历项目描述 / 沟通话术生成
→ CLI / Streamlit / FastAPI / Browser Extension 展示
```

默认路径使用规则和模板实现，保证无外部大模型 API 时也可复现。可选 LLM / embedding provider 用于增强生成和检索，不作为演示稳定性的前提。

## 演示边界

- 不自动投递。
- 不自动向 HR 或招聘平台发送消息。
- 不自动爬取 BOSS 直聘、实习僧、LinkedIn 等平台。
- 浏览器插件只读取当前页面文本并辅助生成分析、话术和简历建议；复制、发送、投递动作必须由用户确认。
- 本地上传、投递记录、知识库索引、生成 PDF 和诊断报告属于运行产物，默认不提交到 Git。

## 可信生成与证据约束

项目默认把最终输出分成三类：

- 可以直接写进简历 / 沟通话术的内容：来自 `implemented` evidence，并带 evidence/source。
- 需要用户确认后才能使用的内容：来自 `designed` evidence，默认加入 warnings 和 `approval_required`。
- 只能作为学习计划或补强建议的内容：来自 `planned` / `uncertain` evidence，不能直接写成真实经历。

`FaithfulnessChecker` 会检查生成 bullet 是否有 evidence 绑定；如果检查不通过，`AgentRunResult` 会暴露 warnings 并要求用户确认。

## 当前状态

### 已完成

| 模块 | 内容 | 测试 |
|---|---|---|
| RAG MVP | schema / loader / chunker / vectorstore / retriever / hybrid retrieval / reranker / grading | 已覆盖测试 |
| Agent MVP | AgentTaskState / JDParserAgent / RAGRetrieveAgent / MatchAnalysisAgent / BuildAgent | 已覆盖测试 |
| Workflow | JobMatchWorkflow + LangGraph Agentic RAG workflow | 已覆盖测试 |
| AgentRunService | analyze_job / discover_jobs / generate_message / handle_hr_reply 统一入口 | 已覆盖测试 |
| CLI Demo | 命令行 demo，输出 Markdown 报告和 RAG 诊断 | 已覆盖测试 |
| Streamlit Demo | 本地可视化求职投递管家 | static checks |
| FastAPI / Browser Extension | 本地页面分析 API + Chrome side panel demo | 已覆盖基础测试 |
| 文档体系 | 设计文档 / 技术决策 / 任务卡 / 运行手册 / 部署文档 | — |
| 样例数据 | 5 份用户资料 + 4 份岗位 JD（脱敏虚构） | — |

测试数量以当前 `python -m pytest -q` 输出为准。

## Quick Start

```bash
git clone https://github.com/yfn-1116/career-agent-assistant.git
cd career-agent-assistant

# 安装项目依赖
python -m pip install -e ".[dev,demo]"

# 运行全部测试
python -m pytest -q

# 运行 CLI demo（默认稳定展示方式）
python demo/cli/run_job_match_demo.py

# 查看输出
cat outputs/demo/job_match_result.md

# 启动 Streamlit demo
streamlit run demo/streamlit/app.py
```

本地 API / 浏览器插件：

```bash
# 启动本地 FastAPI 服务
uvicorn career_agent.api.app:app --reload

# 查看 Swagger / OpenAPI 文档
# http://127.0.0.1:8000/docs

# Chrome 插件
# 1. 打开 chrome://extensions
# 2. 开启 Developer mode
# 3. Load unpacked -> 选择 browser_extension/
# 4. 在岗位详情、岗位列表或聊天页面点击 Analyze Current Page
```

评估 runner：

```bash
# 运行评估 runner（检查输出质量）
python demo/evaluation/run_evaluation.py
cat outputs/demo/evaluation_report.md
```

可选 LLM 增强：

```bash
export DEEPSEEK_API_KEY=你的key
export QWEN_API_KEY=你的key
```

## 项目结构

```text
src/career_agent/
├── rag/           # RAG pipeline（loader, chunker, vectorstore, retriever, pipeline）
├── agents/        # AgentTaskState + JDParser/RAGRetrieve/MatchAnalysis/Build
├── workflows/     # Python workflow + LangGraph workflow
├── service/       # AgentRunService 统一入口
├── api/           # FastAPI routes + Pydantic schemas
├── repository/    # Repository layer exports for runtime storage
└── models/        # ModelProvider / MockProvider / DeepSeekProvider / QwenProvider

demo/
├── cli/           # CLI demo 入口
└── streamlit/     # Streamlit 可视化 demo

browser_extension/ # Chrome side panel demo

data/samples/
├── profile/       # 脱敏示例用户资料（5 文件）
└── jobs/          # 脱敏示例岗位 JD（4 文件）

tests/
├── rag/           # 61 tests
├── agents/        # 68 tests
├── workflows/     # 11 tests
└── demo/          # 25 tests (10 CLI + 15 Streamlit static)

runtime/           # 本地运行数据（ignored）
outputs/           # 生成报告 / PDF / diagnostics（ignored，保留 demo/.gitkeep）
documents/         # 设计文档、技术决策、运行手册、部署文档、日志、规划
docs/superpowers/  # AI 协作规范与任务卡
```

## 后端分层

本项目后端使用 **FastAPI**，不使用 Flask 或 Django。

```text
FastAPI routes
-> Service
-> AgentRunService / ApplicationService / KnowledgeBaseService / BrowserAssistantService
-> Repository / LangGraph Workflow / RAG / Matching / Message Generation
-> Pydantic Response Schema
```

- FastAPI：负责路由、请求/响应 schema、CORS、Swagger / OpenAPI 文档。
- Service：负责编排业务流程，API 和 Streamlit 都应优先调用 service。
- Repository：负责本地 JSONL、runtime 上传文件和运行数据读写，后续可替换为数据库。
- LangGraph：负责编排 Agentic RAG 工作流。
- RAG + Evidence Gate：负责证据检索、检索质量诊断和可信生成约束，避免编造经历。

当前核心 API：

- `GET /api/health`
- `POST /api/jobs/analyze`
- `POST /api/messages/generate`
- `POST /api/applications`
- `GET /api/applications`
- `POST /api/knowledge/upload`
- `POST /api/browser/analyze-current-page`（浏览器插件兼容接口）

## GitHub 仓库资料读取

当前支持本地模拟 GitHub 仓库资料读取（不访问网络）：

- `data/samples/github_repos/career-agent-assistant/`
- `data/samples/github_repos/chem-auto-titration/`
- `data/samples/github_repos/polyu-internship-project/`

仓库 README/docs → ProfileDocument → RAG 检索。

后续可扩展远程 GitHub API 读取。

## 可选 Embedding 检索

当前默认 RAGPipeline 使用 MemoryVectorStore（关键词检索），保证稳定可复现。

项目已新增 **EmbeddingProvider** 抽象层：

- `HashEmbeddingProvider`：本地 hash 伪向量，不调用外部模型
- `EmbeddingVectorStore`：余弦相似度检索

当前用于验证 embedding → 检索的接口链路，**不是生产级语义检索**。后续可替换为 DeepSeek/OpenAI embedding 并接入 Chroma/FAISS。

## 后续开发计划

```text
✅ RAG schema → pipeline
✅ AgentTaskState → 核心 Agent
✅ Workflow 集成
✅ CLI demo
✅ Streamlit demo
✅ LangGraph workflow 原型
✅ FastAPI / Browser Extension demo
✅ 学校服务器部署文档
⏳ 收敛 Streamlit 为薄 UI
⏳ 加深 Evidence Gate / Faithfulness 对最终输出的约束
⏳ 增强端到端演示测试
```

## 协作规则

- **Codex** 负责核心架构、核心接口、RAG / Agent 集成和疑难修复。
- **Claude Code + DeepSeek** 负责边界清晰的文档补全、样例数据、局部模块、测试和 demo。
- **ChatGPT + User** 负责方案讨论、任务拆分和需求确认。
- 所有执行任务必须先有 `docs/superpowers/tasks/` 下的任务说明。
