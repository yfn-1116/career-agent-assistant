# 参考架构选择决策

## 1. 背景

ARCH-002 调研了 LangGraph、LangGraph RAG examples、Dify、RAGFlow、DeerFlow、OpenHands、Khoj、Flowise 八个项目。它们分别代表状态化 Agent workflow、Agentic RAG 示例、AI 应用平台、RAG 引擎、Super Agent harness、软件工程 Agent 平台、个人知识库和低代码可视化平台。

本项目目标是大学生实习求职辅助，不是通用 AI 平台。因此参考成熟项目时必须裁剪——取架构思想，不取平台形态。

## 2. 候选参考项目

| 项目 | 类型 | 参考优先级 | 核心参考点 |
|---|---|---|---|
| LangGraph | Agent 框架 | ⭐⭐⭐ | 状态化 workflow、State/Node/Edge、checkpoint 持久化 |
| LangGraph RAG examples | Agentic RAG 示例 | ⭐⭐⭐ | query analysis、document grading、evidence→answer 一致性 |
| Dify | AI 应用平台 | ⭐⭐ | 知识库生命周期、workflow 可视化思维、模型 provider 抽象 |
| RAGFlow | RAG 引擎 | ⭐⭐⭐ | RAG pipeline 分层、chunk 策略、citation/source grounding |
| DeerFlow | Super Agent | ⭐⭐ | Agent 边界、memory 分层、sub-agent 工具隔离 |
| OpenHands | 软件工程 Agent | ⭐⭐⭐ | 执行边界声明、event log、workspace 隔离、权限控制 |
| Khoj | 个人知识库 | ⭐⭐ | 个人数据优先、自托管部署、本地 Markdown 知识库 |
| Flowise | 低代码平台 | ⭐ | 流程可视化思想、Document Store 节点化、模板化 demo |

## 3. 决策原则

### 3.1 服务当前项目目标

所有架构选择必须服务"实习求职 RAG + 多 Agent 原型"，不为平台化而平台化。

### 3.2 保持第一阶段可实现

第一阶段要能在本地和学校服务器复现，不能被复杂部署、重型依赖和前后端系统拖慢。

### 3.3 保持文档先行

任何实现前必须先有设计文档和任务卡。

### 3.4 保持模块边界清晰

RAG、Agent、Workflow、Demo、Evaluation 应分层，避免一个任务同时修改多个大模块。

### 3.5 为后续升级预留接口

当前选择应为后续引入 LangGraph、更多 Agent、复杂检索策略保留扩展点，不把路走死。

### 3.6 支持多 AI 分工

核心接口和集成由 Codex 负责；边界清晰的局部实现、样例、测试、demo 可交给 Claude Code + DeepSeek。

## 4. 采用的设计（逐项决策）

### 4.1 状态化 workflow 思想

**来源**：LangGraph

**决策**：采用 LangGraph 的状态、节点和边思想，但第一阶段先用普通 Python workflow 实现。

**具体做法**：
- `AgentTaskState` 设计为 TypedDict 或 dataclass，结构对齐 LangGraph State 概念。
- 每个 Agent 作为 workflow 中的一个步骤，接收 State 并返回部分更新。
- 工作流按固定顺序编排：`JDParser → RAGRetrieve → MatchAnalysis → Build`。
- 后续如需条件路由、checkpoint、human-in-the-loop，可迁移到 LangGraph。

**为什么不直接用 LangGraph**：
- 第一阶段流程固定，不需要条件边、并行 fan-out、复杂图路由。
- LangGraph 依赖 LangChain 生态，增加不必要的依赖和理解成本。
- 普通 Python workflow 更易调试，团队成员无需学习 StateGraph API。

### 4.2 RAG pipeline 分层

**来源**：RAGFlow / Flowise / Dify

**决策**：将 RAG 拆为 Loader → Chunker → VectorStore → Retriever → Pipeline 五个独立层。

**具体做法**：
- `rag/loaders/`：MarkdownProfileLoader，只读本地 Markdown。
- `rag/chunking/`：按 section 分块（基本信息/教育/技能/项目/实习），保留 section metadata。
- `rag/vectorstores/`：VectorStore 接口 + memory/lightweight 第一版实现。
- `rag/retrievers/`：封装检索策略，输出 `RetrievedEvidence`。
- `rag/pipeline.py`：组合四层，提供统一检索入口。

**为什么不直接用 RAGFlow**：
- RAGFlow 面向复杂文档（PDF、OCR、表格），部署依赖 Elasticsearch、MySQL、Redis。
- 本项目第一阶段只处理本地 Markdown，不需要深度文档解析。

### 4.3 证据追溯

**来源**：RAGFlow / LangGraph RAG examples

**决策**：检索结果必须保留 source、quote、score、reason 四个字段。

**具体做法**：
- `RetrievedEvidence` schema 包含：`source`（来源文件）、`quote`（原文引用）、`score`（相关性评分）、`reason`（评分理由）。
- 生成输出时必须引用 evidence，不能编造经历。
- 评估模块检查输出是否基于检索证据。

**设计考量**：
- RAGFlow 的 citation 机制启发 source + quote 字段。
- LangGraph RAG 的 document grading 启发 score + reason 字段。
- 四个字段组合可以有效防止幻觉和追溯生成质量。

### 4.4 Agent 执行边界

**来源**：OpenHands / DeerFlow

**决策**：每个 Agent 只读取必要字段，输出写入指定状态字段；每个任务卡声明允许和禁止修改的文件。

**具体做法**：
- JDParserAgent：只读 `jd_text`，只写 `parsed_jd`。
- RAGRetrieveAgent：只读 `parsed_jd`，只写 `retrieved_evidence`。
- MatchAnalysisAgent：只读 `parsed_jd` + `retrieved_evidence`，只写 `match_analysis`。
- BuildAgent：只读 `match_analysis` + `retrieved_evidence`，只写 `final_output`。
- 任何 Agent 不得直接读取/写入文件系统或调用其他 Agent 的私有方法。

**设计考量**：
- OpenHands 的 "Agent 权限声明" 启发字段级隔离。
- DeerFlow 的 "sub-agent 工具边界" 启发 Agent 只能调用授权能力。
- 边界清晰后，每个 Agent 可独立测试和替换。

### 4.5 个人知识库定位

**来源**：Khoj

**决策**：采用 "个人能力知识库" 定位，聚焦求职投递场景，不做通用 second brain。

**具体做法**：
- 用户维护一份 Markdown 格式的个人能力资料（技能、项目、实习、教育）。
- RAG 基于这份资料做检索和匹配分析。
- 数据完全在本地，不上传云端。
- 不引入日程、自动化、deep research 等泛化功能。

**设计考量**：
- Khoj 的 "个人数据优先" 理念是本项目定位的核心参考。
- Khoj 功能过宽（搜索、日程、自动化、research），本项目裁剪为求职单一场景。
- 自托管展示思路与学校服务器部署需求一致。

### 4.6 轻量 demo 展示

**来源**：Flowise / Dify

**决策**：通过 CLI + Streamlit 展示流程，不做拖拽式可视化编辑器。

**具体做法**：
- CLI demo：最稳定路径，调用 workflow，输出 Markdown 格式结果。
- Streamlit demo：逐步展示 "JD 解析 → 检索证据 → 匹配分析 → 最终输出"。
- 每步可展开查看详细数据（如检索到的原文段落、相关性评分）。
- Demo 层只调用 workflow，不重写业务逻辑。

**设计考量**：
- Flowise 的可视化流程思想启发 "逐步展示"。
- Dify 的应用发布思想启发 "配置 → 展示" 模式。
- 但两者都需要完整前端，本项目用 Streamlit 即可满足展示需求。

### 4.7 模型 Provider 抽象

**来源**：Dify / RAGFlow

**决策**：通过 `models/provider.py` 接口抽象模型调用，不绑定具体模型。

**具体做法**：
- 定义 `ModelProvider` 接口（`generate()` 方法）。
- 实现 `DeepSeekProvider` 作为默认 provider。
- 提供 `MockProvider` 用于测试和 demo 兜底。
- 后续可接入 OpenAI、Claude 等模型而不改业务代码。

### 4.8 Memory 分层

**来源**：DeerFlow

**决策**：将记忆分为长期记忆（知识库）、工作记忆（AgentTaskState）、短期记忆（对话历史）三层。

**具体做法**：
- **长期记忆**：用户 Markdown 资料，通过 RAG pipeline 检索，不进入每次 LLM 调用。
- **工作记忆**：`AgentTaskState`，当前任务的状态和中间结果。
- **短期记忆**：对话历史（如果后续支持多轮交互），在第一阶段可暂不实现。

## 5. 暂不采用的设计（逐项决策 + 原因）

### 5.1 为什么不直接照搬 Dify

**Dify 的能力**：RAG pipeline、Agent workflow、Prompt IDE、应用发布、权限管理、多租户、监控日志、Marketplace。

**不采用原因**：
1. **平台规模**：Dify 包含 Web 前端（React）、后端 API（Python）、异步任务（Celery）、数据库（PostgreSQL）、缓存（Redis）、向量数据库。这些组件对第一阶段都是负担。
2. **部署复杂度**：需要 Docker Compose 部署，学校服务器可能不支持。
3. **概念重**：知识库、应用、Agent、工具、工作流等概念在 Dify 中有完整 UI 和管理，搬用会让第一阶段失焦。
4. **用户群不同**：Dify 面向"应用构建者"，本项目面向"求职者"，交互模式不同。

**能借鉴什么**：
- 知识库生命周期管理（产品化思维）。
- 模型 provider 抽象（不绑定具体模型）。
- 调用日志与追踪（用于 demo 展示和评估）。

### 5.2 为什么不直接照搬 RAGFlow

**RAGFlow 的能力**：深度文档解析（PDF、OCR、版面分析）、Chunk 模板、Citation、Dataset 管理、Rerank。

**不采用原因**：
1. **文档类型不匹配**：RAGFlow 核心投入在复杂文档解析，本项目只处理 Markdown 纯文本。
2. **部署依赖重**：需要 Elasticsearch、MySQL、Redis。
3. **过度能力**：版面分析、视觉模型、表格提取对 Markdown 无价值。

**能借鉴什么**：
- RAG pipeline 分层架构。
- Chunk 策略与文档结构对齐。
- Citation / Source Grounding（证据可追溯）。

### 5.3 为什么不直接照搬 Flowise

**Flowise 的能力**：低代码可视化编辑器、拖拽节点构建 LLM workflow、Tracing & Analytics、Evaluations、Marketplace 模板、Multi-Agent Agentflow。

**不采用原因**：
1. **技术栈不匹配**：Node.js + React monorepo，与 Python 工具不一致。
2. **核心价值不匹配**：Flowise 核心是"不用写代码搭 AI 应用"，本项目使用者是开发者。
3. **编辑器开发成本**：可视化编辑器开发工作量巨大，不是本项目核心需求。
4. **平台化倾向**：Flowise 正向多用户、团队协作发展，与个人工具定位不符。

**能借鉴什么**：
- "流程可见"的 demo 展示思路（但用 Streamlit 实现）。
- Document Store 节点化思维（对应 RAG pipeline 分层）。
- 模板化 demo 组合。

### 5.4 为什么不直接使用 DeerFlow 作为框架

**DeerFlow 的能力**：Supervisor + Sub-agent 路由、Sandbox 执行、Skills marketplace、Persistent memory、LangGraph backend。

**不采用原因**：
1. **过度设计**：Supervisor 动态路由、sandbox、skills marketplace 对四个固定 Agent 是过度设计。
2. **部署门槛**：Sandbox 需要 Docker，memory 需要持久化存储。
3. **定位不同**：DeerFlow 面向"长周期通用任务"，本项目面向"特定求职场景"。

**能借鉴什么**：
- Agent 角色与工具边界。
- Memory 与上下文分离（长期/工作/短期）。
- 状态可恢复（中断后继续）。

### 5.5 为什么不直接使用 OpenHands / SDK

**OpenHands 的能力**：Agent 在隔离环境中编写代码、执行命令、修改文件、Event Stream、Sandbox。

**不采用原因**：
1. **核心能力不匹配**：OpenHands 面向代码工程自动化（写代码、改文件、跑命令），本项目是求职资料 RAG。
2. **安全风险**：代码执行能力不是本项目需求，引入反而增加安全风险。
3. **Docker/K8s 依赖**：Sandbox 需要容器环境，学校服务器不支持。

**能借鉴什么**：
- Agent 执行边界和权限声明（适用于任务卡设计）。
- Event 日志和回放（适用于 demo 的逐步展示）。
- "何时不该写代码"的思维（适用于 BuildAgent 防止编造经历）。

### 5.6 为什么第一阶段不引入 LangGraph 框架

**LangGraph 的优势**：StateGraph、条件边、checkpoint、persistence、human-in-the-loop、并行 fan-out。

**不引入原因**：
1. **流程固定**：第一阶段是线性流程（JD→检索→匹配→生成），不需要条件路由。
2. **学习成本**：StateGraph API、reducer、checkpoint 等概念对初期原型是额外负担。
3. **LangChain 依赖**：LangGraph 与 LangChain 生态绑定，增加依赖链。
4. **调试成本**：图执行调试比线性代码更复杂。

**什么时候引入**：
- 需要条件路由（如"检索质量不足→重试"）。
- 需要 human-in-the-loop（如"匹配分析是否合理→人工确认"）。
- 需要并行 fan-out（如同时对多个 JD 做匹配）。
- 需要 checkpoint 回放（如 demo 复现和问题定位）。

### 5.7 为什么不一开始做完整前后端

第一阶段核心不是 Web CRUD，而是 RAG、Agent 状态、证据追溯和 demo 可复现。完整前后端会增加：
- 接口设计（REST / WebSocket）。
- 前后端状态同步。
- UI 组件开发。
- 部署脚本编写。

这些会推迟核心链路验证。

### 5.8 为什么第一阶段保持 CLI + Streamlit

- **CLI**：最稳定，便于本地调试和服务器复现。输出 Markdown 文本，可直接阅读和 review。
- **Streamlit**：能低成本展示输入、证据、分析和结果。无需前端开发技能，Python 即可完成。
- 二者结合足以支撑第一阶段演示，后续如需更丰富的 UI 再考虑扩展。

## 6. 最终结论

本项目第一阶段采用轻量参考组合：

```text
输入层：本地 Markdown 个人能力知识库
    ↓
RAG 层：Loader → Chunker → VectorStore → Retriever → Pipeline
    ↓
状态层：AgentTaskState（LangGraph 风格，普通 Python 实现）
    ↓
Agent 层：四个核心 Agent（JD Parser / RAG Retrieve / Match Analysis / Build）
    ↓
Workflow 层：普通 Python workflow（固定顺序编排）
    ↓
输出层：CLI + Markdown 文本 + Streamlit 轻量展示
    ↓
评估层：独立的 RAG eval + output eval 模块
```

**不采用**：Dify 的平台架构、RAGFlow 的复杂文档解析、Flowise 的低代码编辑器、DeerFlow 的 supervisor/sandbox、OpenHands 的代码执行能力、Khoj 的泛化功能、LangGraph 的框架依赖。

**后续**：ARCH-003 将基于本决策，最终确定代码目录结构和第一批创建的文件。

## 7. ARCH-003 最终目录决策

ARCH-003 最终确认：

- 第一阶段采用 `src/career_agent/` 作为 Python package。
- 第一阶段保留 `models/` provider 抽象和 `evaluation/` 评估模块。
- 第一阶段 demo 采用 `demo/cli/` 和 `demo/streamlit/`。
- 第一阶段不创建 `app/streamlit_app.py`。
- 第一阶段不创建 `frontend/`、`backend/`、`server/`。
- ARCH-003 不引入 `pyproject.toml` 或 `requirements.txt`。
- 第一阶段不引入 LangGraph；普通 Python workflow 先行。
- 第一阶段不引入 Chroma / FAISS；先定义 `VectorStore` 接口和 Memory 实现。

这些决策服务于一个目标：先把本地 Markdown 资料、RAG pipeline、四个核心 Agent、固定 workflow 和可复现 demo 跑通。
