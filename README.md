# Evidence-grounded Job Matching Agent

基于证据约束的智能求职匹配 Agent。

## 项目定位

**不是**：GPT 包装壳、简历生成器、自动投递机器人、一次性 JD 分析工具。

**是**：
- 维护用户**长期求职资料库**，区分"已实现/设计/计划/证据不足"；
- 根据 JD **自动检索真实经历**，每条建议绑定 evidence/source；
- **Evidence Gate** 阻止把"设计了"写成"实现了"，阻止编造经历；
- 输出**可追溯 diagnostics 和 report**；
- **长期追踪能力缺口**，告诉用户该补什么项目；
- **批量岗位匹配和投递记录**。

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

# 安装项目依赖
python -m pip install -e .

# 运行全部测试
pytest tests -q

# 运行 CLI demo（默认稳定展示方式）
python demo/cli/run_job_match_demo.py

# 查看输出
cat outputs/demo/job_match_result.md

# 可选：Streamlit 可视化展示
python -m pip install -e ".[demo]"
streamlit run demo/streamlit/app.py

# 运行评估 runner（检查输出质量）
python demo/evaluation/run_evaluation.py
cat outputs/demo/evaluation_report.md

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
✅ 学校服务器部署文档
⏳ 接入 LLM API（DeepSeek / OpenAI）
⏳ LangGraph 状态图迁移（可选）
```

## 协作规则

- **Codex** 负责核心架构、核心接口、RAG / Agent 集成和疑难修复。
- **Claude Code + DeepSeek** 负责边界清晰的文档补全、样例数据、局部模块、测试和 demo。
- **ChatGPT + User** 负责方案讨论、任务拆分和需求确认。
- 所有执行任务必须先有 `docs/superpowers/tasks/` 下的任务说明。
