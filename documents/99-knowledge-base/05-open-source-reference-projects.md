# 开源项目参考调研

## 1. 调研目的

本项目后续要实现 RAG 用户资料知识库、多 Agent 编排、CLI / Streamlit demo 和学校服务器展示。调研成熟开源项目的目的不是照搬它们的代码或平台形态，而是识别哪些架构思想值得吸收，哪些复杂度需要裁剪，避免第一阶段过早膨胀。

本轮调研主要基于公开 GitHub README、官方文档、示例页面和项目说明。GitHub API 目录接口本轮触发 rate limit，因此目录结构部分以公开页面、文档和仓库说明为主，不编造无法确认的细节。

## 2. 调研项目概览

本轮深入调研 8 个开源项目，按类型分为四类：

| 类型 | 项目 | 一句话定位 |
|---|---|---|
| Agent 框架 | LangGraph | 状态化多 Agent workflow 框架 |
| Agent 示例 | LangGraph RAG examples | Agentic RAG / 自适应 RAG 参考实现 |
| AI 应用平台 | Dify | 生产级 AI 应用开发平台 |
| RAG 引擎 | RAGFlow | 深度文档理解 RAG 引擎 |
| Super Agent | DeerFlow | 长周期 super agent harness |
| 软件工程 Agent | OpenHands / Software Agent SDK | 软件工程 Agent 平台与 SDK |
| 个人知识库 | Khoj | 自托管个人 AI / second brain |
| 低代码平台 | Flowise | 低代码 LLM workflow 可视化构建器 |

## 3. 调研结论摘要

| 项目 | 类型 | 主要参考点 | 不适合照搬点 | 对本项目启发 |
|---|---|---|---|---|
| LangGraph | Agent workflow / state graph 框架 | 状态、节点、边、checkpoint、human-in-the-loop、RAG 自校正流程 | 第一阶段直接上复杂图会增加成本；示例依赖较多外部组件 | 先设计 `AgentTaskState`，普通 workflow 起步，后续迁移 LangGraph |
| LangGraph RAG examples | Agentic RAG 示例 | query analysis、文档相关性判断、query rewrite、自校正循环 | 第一阶段不需要多轮自校正和外部搜索 | 先把 RAG pipeline 和评估字段设计好，为后续自校正预留接口 |
| Dify | AI 应用平台 / workflow builder | RAG pipeline、workflow、Prompt IDE、应用发布、可视化编排 | 平台太重，前后端、队列、插件、权限等不适合第一阶段 | 借鉴"知识库处理"和"workflow 可视化思维"，不复制平台架构 |
| RAGFlow | RAG 引擎 / 文档理解平台 | 文档解析、chunk 模板、引用、dataset、chat 组合 | 面向复杂文档和企业级 RAG，部署和依赖较重 | 借鉴 RAG 分层：loader、parser、chunker、vectorstore、retriever、evidence |
| DeerFlow | Long-horizon super agent harness | sub-agent、memory、sandbox、skills、tools、LangGraph backend | 目标是长任务通用 Agent，远超实习求职 MVP | 借鉴 Agent 边界、工具隔离和 memory 概念，裁剪为四个核心 Agent |
| OpenHands / Software Agent SDK | 软件工程 Agent / SDK | workspace 隔离、agent 执行边界、事件日志、可控任务执行 | 面向代码修改和工程自动化，不是求职 RAG 应用 | 借鉴"任务边界、沙箱、日志、权限控制"，用于多 AI 协作规范 |
| Khoj | 个人知识库 / AI second brain | personal AI、self-host、文档搜索、个人资料问答 | 功能范围包含日程、自动化、deep research，可能过宽 | 本项目个人能力知识库定位可参考 Khoj，但聚焦求职投递 |
| Flowise | 低代码 / 可视化 LLM workflow builder | 可视化节点、Document Stores、Agentflow、模板和 demo | Node / React monorepo 和低代码平台路线不适合当前项目 | 借鉴展示和流程可视化思路，但第一阶段仍保持 CLI + Streamlit |

---

## 4. LangGraph

参考来源：
- https://github.com/langchain-ai/langgraph
- https://docs.langchain.com/oss/python/langgraph/graph-api
- https://docs.langchain.com/oss/python/langgraph/persistence

### 4.1 项目定位

LangGraph 是 LangChain 生态中用于构建**状态化、多步骤、多 Agent workflow** 的框架。其核心思想是将 Agent 交互建模为有向图：State（共享状态）、Node（处理节点）、Edge（流程转移）。LangGraph 不是应用平台，而是一个**底层框架**，开发者在其上构建自定义 workflow。

### 4.2 典型目录与概念结构

LangGraph 仓库以框架核心 + SDK + 示例 + 文档组织。对本项目而言，关键不是复制其目录，而是理解其概念分层：

```text
langgraph/
├── libs/
│   ├── langgraph/          # Python 核心库
│   │   ├── graph/          # StateGraph, MessageGraph
│   │   ├── channels/       # 状态通道（用于 reducer）
│   │   ├── checkpoint/     # 持久化与 checkpoint
│   │   ├── prebuilt/       # 预置 Agent 模式
│   │   └── utils/
│   ├── sdk/                # 多语言 SDK
│   └── cli/                # LangGraph CLI / Studio
├── examples/               # 示例（RAG、chatbot、multi-agent 等）
└── docs/                   # 官方文档
```

核心概念分层：

| 概念层 | 说明 | 本项目映射 |
|---|---|---|
| State | 图中所有节点共享的 TypedDict，节点读取并返回部分更新 | `AgentTaskState` |
| Node | 接收 State 并返回 State 更新的处理单元 | 各 Agent |
| Edge | 定义节点间控制流（普通边 / 条件边） | workflow 中的步骤顺序 |
| Checkpoint | 每个 super-step 后的状态快照，支持持久化 | 日志 / trace |
| Persistence | 基于 checkpoint 的线程级持久化 | 任务卡保存 |
| Human-in-the-loop | 在特定节点暂停等待人工确认 | 第一阶段不需要 |

### 4.3 RAG 设计参考点

- LangGraph 本身不提供 RAG 实现，但提供了**将 RAG 建模为状态流**的框架。
- 典型 agentic RAG 图结构：`query_analysis -> retrieve -> grade_documents -> generate -> (decide: rewrite / answer)`。
- 检索结果作为 State 字段在节点间传递，每个节点可修改检索策略或重写查询。

### 4.4 Agent 编排参考点

- **Supervisor 模式**：一个 supervisor agent 根据状态决定路由到哪个 sub-agent。
- **Hierarchical agent**：agent 可以嵌套另一个 agent graph 作为节点。
- **并行节点**：Send API 支持 fan-out，多个节点并行执行后收集结果。
- **条件边**：根据 State 字段动态决定下一步（如：检索质量不足 → rewrite；质量足够 → generate）。

### 4.5 工程化和 Demo 展示参考点

- LangGraph Studio 提供可视化调试能力，可单步执行、查看状态、回放。
- Checkpoint 机制天然支持 demo 复现——保存关键步骤状态，展示时可回放。
- CLI 和 API 均可运行 graph，适合本地开发和服务器部署。

### 4.6 不适合本项目照搬的原因

1. **框架耦合**：第一阶段直接引入 LangGraph 会增加依赖和理解成本。
2. **过度抽象**：第一阶段流程固定（JD → 检索 → 匹配 → 生成），不需要条件路由和并行 fan-out。
3. **学习曲线**：StateGraph API、reducer、checkpoint 等概念对初期原型是额外负担。
4. **LangChain 依赖**：LangGraph 与 LangChain 生态深度绑定，而本项目第一阶段追求最小依赖。

### 4.7 对 career-agent-assistant 的具体启发

1. **先设计 State，再设计 Agent**：`AgentTaskState` 应包含 `jd_text`、`retrieved_evidence`、`match_analysis`、`final_output` 等字段，每个 Agent 只更新自己负责的部分。
2. **为后续迁移预留接口**：State 结构设计成 TypedDict 或 dataclass，后续可直接作为 LangGraph State。
3. **条件边的概念可暂不实现，但可预留字段**：如 `retrieval_quality` 字段可在 State 中预留，后续支持 "若质量不足则重试" 的逻辑。
4. **日志格式对齐 checkpoint**：每步输出包含 step_name、input_summary、output_summary、timestamp，方便 demo 展示和问题定位。

---

## 5. LangGraph RAG Examples

参考来源：
- https://docs.langchain.com/oss/python/langgraph/agentic-rag
- https://github.com/langchain-ai/langgraph/blob/main/examples/rag/langgraph_adaptive_rag.ipynb
- https://www.langchain.com/blog/agentic-rag-with-langgraph

### 5.1 项目定位

LangGraph RAG 示例是 LangGraph 官方提供的 **Agentic RAG 参考实现**，展示如何用 LangGraph 构建具备自适应检索、自校正和路由能力的 RAG 系统。核心示例包括：

- **Agentic RAG**：LLM 自主决定是否需要检索、检索什么。
- **Adaptive RAG**：根据查询类型路由到不同检索策略（向量检索 / web 搜索）。
- **Self-corrective RAG**：检索后评估文档相关性，不相关则重写查询或回退到 web 搜索。
- **Self-RAG**：生成后自省，检查答案是否有据可查、是否相关。

### 5.2 典型流程结构

```text
query_analysis
    ├── (需检索) → retrieve → grade_documents
    │                           ├── (相关) → generate
    │                           └── (不相关) → rewrite_query → retrieve
    └── (不需检索) → generate
                              ↓
                          grade_answer
                              ├── (有据) → output
                              └── (无据) → rewrite_query → retrieve
```

### 5.3 RAG 设计参考点

1. **Query Analysis 前置**：在检索前分析查询意图，决定检索策略。这对本项目意味着：JD 解析后应判断哪些技能和经历需要检索，而非直接全文检索。
2. **Document Grading 后置**：检索后对每份文档做相关性判断，过滤不相关结果。对应本项目的 `RetrievedEvidence.score` 和 `RetrievedEvidence.reason`。
3. **Query Rewrite**：检索质量不足时重写查询（如扩展同义词、调整关键词权重）。第一阶段可不实现，但 `AgentTaskState` 应预留 `rewritten_query` 字段。
4. **Evidence → Answer 一致性检查**：生成后验证答案是否来自检索证据，防止幻觉。对应本项目的 output evaluator。

### 5.4 Agent 编排参考点

- 每个步骤（query_analysis、retrieve、grade_documents、generate）可作为独立节点。
- 条件边实现"质量不足→重试"的闭环。
- 整个流程可包装为一个 `agentic_rag` 图，对外暴露统一接口。

### 5.5 工程化和 Demo 展示参考点

- 示例以 Jupyter Notebook 形式发布，便于交互式演示和讲解。
- 每步输出可视化展示（如检索结果表格、相关性评分条形图）。
- 流程图（Graphviz / Mermaid）直观展示决策分支。

### 5.6 不适合本项目照搬的原因

1. **多轮自校正开销**：第一阶段数据量小（个人 Markdown 资料），不需要多轮检索和自校正循环。
2. **外部搜索依赖**：Adaptive RAG 的 web 搜索回退不适合本地/离线场景。
3. **复杂路由**：第一阶段查询类型单一（JD → 用户资料匹配），不需要多路由分支。

### 5.7 对 career-agent-assistant 的具体启发

1. **RAG 评估字段前置设计**：`RetrievedEvidence` 必须包含 `score`、`reason`、`source`、`quote`，为后续文档分级预留接口。
2. **pipeline 不是线性的**：虽然第一阶段实现线性 pipeline，但架构上应允许多个评估点插入（如检索后评估、生成后评估）。
3. **ReviewAgent 预留**：可在 Workflow 末尾预留 `ReviewAgent` 位置，后续实现对输出的自检。
4. **Demo 展示思想**：Streamlit demo 可以逐步展示 "JD 解析 → 检索了什么 → 证据相关性 → 匹配分析 → 最终输出"，让流程透明。

---

## 6. Dify

参考来源：
- https://github.com/langgenius/dify
- https://dify.ai/

### 6.1 项目定位

Dify 是**生产级 AI 应用开发平台**，提供从 Prompt 编排、RAG pipeline、Agent workflow、模型管理到应用发布和监控的完整能力。其目标用户是需要快速构建和部署 AI 应用的团队，而非开发底层框架的工程师。

Dify 的核心能力矩阵：

| 能力域 | 说明 |
|---|---|
| Studio | 可视化编排 Prompt、RAG pipeline、Agent workflow |
| Knowledge Base | 文档摄入、解析、向量化、检索管理 |
| Agent | 基于工具的自主 Agent，支持推理和行动循环 |
| Application | 将编排好的 workflow 发布为 API 或 Web 应用 |
| Operations | 日志、监控、标注、模型使用统计 |

### 6.2 典型目录结构

Dify 是典型的分层平台架构（基于公开文档推断，非直接从仓库复制）：

```text
dify/
├── api/                    # 后端 API 服务
│   ├── controllers/        # 路由控制器
│   ├── services/           # 业务逻辑层
│   ├── core/               # 核心抽象（模型、工具、RAG 等）
│   │   ├── rag/            # RAG pipeline
│   │   ├── agent/          # Agent 策略
│   │   └── model/          # 模型 provider 抽象
│   └── tasks/              # 异步任务（Celery）
├── web/                    # 前端 Web 应用（Next.js）
├── docker/                 # Docker 部署配置
└── docs/                   # 官方文档
```

### 6.3 RAG 设计参考点

1. **知识库生命周期管理**：创建知识库 → 上传文档 → 选择分块策略 → 选择索引方式 → 检索设置 → 召回测试。这种清晰的生命周期值得本项目借鉴，但实现上用更轻量的方式。
2. **分块策略可配置**：支持自定义 chunk size、overlap、分隔符。本项目第一阶段可以简单配置，但应保留扩展点。
3. **检索模式分层**：支持关键词检索、向量检索、混合检索。第一阶段用向量检索即可，但接口应支持后续扩展。
4. **RAG pipeline 与对话分离**：检索是独立模块，对话 Agent 通过工具调用检索。本项目 RAG pipeline 也应独立于 Agent。

### 6.4 Agent 编排参考点

1. **Workflow Builder 的可视化思想**：虽然本项目不做拖拽 builder，但 workflow 的节点 + 边概念可用于 Streamlit 展示。
2. **Prompt IDE**：提示词版本管理和调试。本项目第一阶段可用 `.md` 文件管理 prompt 模板，后续再考虑版本化。
3. **工具调用封装**：Dify Agent 通过工具接口调用外部能力。本项目 Agent 调用 RAG pipeline 和模型 provider 也是类似模式。

### 6.5 工程化和 Demo 展示参考点

1. **应用发布**：编排好的 workflow 一键发布为可访问的 Web 应用。本项目后续 Streamlit demo 可参考这种"配置 → 展示"的思路。
2. **日志与追踪**：每次调用的输入、输出、延迟、token 消耗可追踪。本项目 CLI demo 也应输出这些信息。
3. **标注与反馈**：用户可对输出标注好坏，用于优化。本项目评估模块应预留人工标注接口。

### 6.6 不适合本项目照搬的原因

1. **平台规模远超需求**：Dify 包含 Web 前端、后端 API、异步任务队列、数据库、插件系统、权限管理、多租户——这些都是生产级平台才需要的。
2. **部署复杂度**：需要 PostgreSQL、Redis、向量数据库、Worker 进程。学校服务器部署不友好。
3. **概念重量级**：知识库、应用、Agent、工具、工作流等概念在 Dify 中有明确 UI 和管理界面，直接搬用会让第一阶段失焦。
4. **前后端分离**：Dify 是完整的 Web 平台，而本项目第一阶段只需要 CLI + Streamlit。
5. **许可证考量**：Dify 采用 Apache 2.0 + 额外限制，直接集成需关注合规。

### 6.7 对 career-agent-assistant 的具体启发

1. **"知识库处理"的产品化思维**：用户资料（Markdown）→ 加载 → 解析 → 分块 → 入库 → 检索，这种清晰的用户心智模型值得在 demo 中展示。
2. **Workflow 可视化展示**：虽然不做拖拽 builder，但 Streamlit 可以展示 "当前 workflow 执行到哪一步，每步的输入输出是什么"。
3. **模型 provider 抽象**：Dify 支持多种模型 provider，本项目也应通过 `models/provider.py` 抽象，不绑定 DeepSeek。
4. **追踪与日志**：借鉴 Dify 的调用日志设计，CLI demo 输出中记录每步的耗时和关键数据。
5. **不做平台，做工具**：核心区别——Dify 面向"搭建应用的人"，本项目面向"使用工具的人"。

---

## 7. RAGFlow

参考来源：
- https://github.com/infiniflow/ragflow
- https://ragflow.io/docs/

### 7.1 项目定位

RAGFlow 是**开源 RAG 引擎**，核心卖点是 **Deep Document Understanding**——基于深度学习的文档解析和理解，而非简单的文本切分。它面向需要从复杂格式（PDF、扫描件、表格、图片）中提取结构化信息的场景，提供带引用的可信问答。

### 7.2 典型目录结构

基于公开文档推断的概念结构：

```text
ragflow/
├── api/                    # REST API 服务
├── rag/
│   ├── app/                # 应用层（dataset、chat、agent）
│   ├── nlp/                # NLP 处理（分词、NER）
│   ├── llm/                # LLM 集成
│   ├── deepdoc/            # 深度文档解析（PDF、OCR、表格）
│   │   ├── parser/         # 各类文档解析器
│   │   └── vision/         # 视觉模型（OCR、版面分析）
│   └── utils/
├── web/                    # 前端
├── docker/                 # 部署
└── docs/
```

### 7.3 RAG 设计参考点

1. **文档解析分层**：Parser → Chunker → Embedder → Indexer → Retriever。每层职责清晰，可独立替换。
2. **Chunk 模板机制**：不同文档类型使用不同 chunk 策略（如 FAQ 按 Q&A 切分，论文按章节切分）。本项目 Markdown 用户资料也应设计合理的 chunk 策略（按技能块、项目经历、教育背景分块）。
3. **Citation / Source Grounding**：检索结果必须保留原文引用和来源页面。对应本项目的 `RetrievedEvidence.source` 和 `RetrievedEvidence.quote`。
4. **Dataset 概念**：将文档组织为 dataset，可对 dataset 做检索。对应本项目的 "用户资料知识库"。

### 7.4 Agent 编排参考点

- RAGFlow 的 Agent 能力相对轻量，主要围绕 Chat + Retrieval 组合。
- Agent 可调用多个 dataset 的检索结果，组合后生成回答。
- 对话历史管理作为独立组件，不混入检索逻辑。

### 7.5 工程化和 Demo 展示参考点

1. **检索结果可视化**：展示检索命中的 chunk、相似度分数和原文引用。
2. **文档解析预览**：上传文档后可预览解析结果和分块效果。
3. **召回测试**：内置数据集检索效果测试，支持查看 hit/miss。

### 7.6 不适合本项目照搬的原因

1. **复杂文档解析能力**：RAGFlow 的核心投入在 PDF、OCR、表格解析，而本项目第一阶段只处理 Markdown 纯文本。
2. **部署依赖重**：需要 Elasticsearch、MySQL、Redis 等基础组件。
3. **企业级定位**：面向企业知识库场景，不是个人轻量原型。
4. **不必要的能力**：版面分析、视觉模型、多格式解析对 Markdown 用户资料无价值。

### 7.7 对 career-agent-assistant 的具体启发

1. **RAG pipeline 分层是核心启发**：即使只处理 Markdown，也应将 pipeline 拆成 `MarkdownProfileLoader → TextChunker → VectorStore → SimpleRetriever → RAGPipeline`。
2. **Chunk 策略与文档结构对齐**：用户资料按 "基本信息 / 教育 / 技能 / 项目 / 实习" 分块，每个 chunk 保留 section 元信息。
3. **证据可追溯**：输出中每条匹配分析都应能回溯到原始 Markdown 段落。
4. **Evaluator 独立**：检索效果评估应独立于 pipeline，可单独运行和查看指标。

---

## 8. DeerFlow

参考来源：
- https://github.com/bytedance/deer-flow
- https://github.com/bytedance/deer-flow/blob/main/backend/README.md

### 8.1 项目定位

DeerFlow 是字节跳动开源的 **Long-Horizon Super Agent Harness**，目标是为长周期、多步骤的复杂任务提供一个完整的 Agent 运行框架。它基于 LangGraph 构建，整合了 sub-agent、memory、sandbox、skills、tools 等能力，试图解决单个 LLM 在处理长任务时的上下文膨胀、记忆丢失和执行失控问题。

### 8.2 典型目录结构

基于公开 README 和仓库结构推断：

```text
deer-flow/
├── backend/                # 后端核心
│   ├── agent/              # Agent 定义与执行
│   │   ├── supervisor/     # Supervisor agent（主控）
│   │   └── sub_agents/     # 子 Agent 定义
│   ├── tools/              # 工具注册与调用
│   ├── memory/             # 长期记忆管理
│   ├── sandbox/            # 沙箱执行环境
│   ├── skills/             # 技能市场（可复用能力）
│   ├── workflow/           # LangGraph workflow 定义
│   └── server/             # API 服务
├── frontend/               # 前端展示
├── examples/               # 示例用例
└── docs/
```

### 8.3 RAG 设计参考点

- DeerFlow 的 RAG 不是核心，而是作为 memory 和 skills 的支撑。
- memory 模块可能包含基于检索的长期记忆，类似 "记忆 RAG"。
- 工具中可能包含文档检索工具，供 sub-agent 调用。

### 8.4 Agent 编排参考点

1. **Supervisor + Sub-agent 架构**：Supervisor 负责任务分解、路由和状态管理；Sub-agent 专注执行具体子任务。本项目可借鉴这种模式：Workflow 充当 supervisor，四个核心 Agent 充当 sub-agent。
2. **Agent 角色与工具边界**：每个 sub-agent 只能访问授权工具，不能越界调用。本项目 Agent 也应只访问自己需要的模块（如 RAGRetrieveAgent 只能调用 RAG pipeline）。
3. **Memory 与上下文分离**：即时上下文（当前任务状态）与长期记忆（用户资料、历史会话）分开管理，避免上下文窗口膨胀。
4. **Sandbox 隔离**：Agent 的执行环境与宿主环境隔离，防止意外修改。本项目的 Agent 不能直接写文件，只能通过任务卡声明的接口修改状态。

### 8.5 工程化和 Demo 展示参考点

1. **任务分解可视化**：展示 supervisor 如何将大任务拆成子任务。
2. **执行日志**：每步执行的输入、输出、耗时、工具调用记录。
3. **状态追踪**：当前执行到哪个 sub-agent，状态是什么，是否出错。

### 8.6 不适合本项目照搬的原因

1. **定位完全不同**：DeerFlow 目标是通用长周期 Agent，本项目是特定领域的求职辅助工具。
2. **复杂度过高**：Supervisor、sandbox、skills marketplace、memory backend 等模块远超第一阶段需求。
3. **部署门槛**：sandbox 需要 Docker 环境，memory 需要持久化存储。学校服务器部署不友好。
4. **过度设计**：本项目四个 Agent 的固定流程不需要动态 supervisor 路由。

### 8.7 对 career-agent-assistant 的具体启发

1. **Agent 角色边界是核心原则**：每个 Agent 只做一件事，输入输出通过 State 传递。
2. **Memory 分层思想**：
   - **长期记忆**：用户知识库（Markdown 资料），不进入每次 LLM 调用。
   - **工作记忆**：`AgentTaskState`，当前任务上下文。
   - **短期记忆**：对话历史（如果需要多轮交互）。
3. **工具抽象**：Agent 调用 RAG pipeline、模型 provider 应通过统一工具接口，便于替换和测试。
4. **状态可恢复**：`AgentTaskState` 应有序列化/反序列化能力，支持中断后恢复。

---

## 9. OpenHands / Software Agent SDK

参考来源：
- https://github.com/OpenHands/OpenHands
- https://github.com/OpenHands/software-agent-sdk
- https://docs.openhands.dev/sdk

### 9.1 项目定位

OpenHands 是面向**软件工程**的 AI Agent 平台，核心能力是让 AI Agent 在隔离环境中编写、修改和测试代码。Software Agent SDK 是其 Python SDK，提供构建代码处理 Agent 的编程接口。

OpenHands 的核心设计理念：

| 概念 | 说明 |
|---|---|
| Agent | 决策单元，接收观察并产生动作 |
| Runtime / Sandbox | Agent 的执行环境（本地 / Docker / K8s） |
| Event Stream | 所有交互的事件日志（Action + Observation） |
| Workspace | Agent 操作的文件系统隔离区 |
| Controller | 控制 Agent 执行循环和状态管理 |

### 9.2 典型目录结构

基于公开文档推断的概念结构：

```text
OpenHands/
├── openhands/
│   ├── agent/              # Agent 实现
│   ├── controller/         # 执行循环与状态管理
│   ├── runtime/            # 沙箱与执行环境
│   ├── server/             # API 服务
│   └── events/             # 事件数据结构
├── frontend/               # Web 前端
├── sdk/                    # Software Agent SDK（Python）
└── docs/
```

Software Agent SDK 的简化概念：

```text
software-agent-sdk/
├── src/
│   ├── agent/              # Agent 基类与接口
│   ├── runtime/            # Runtime 抽象
│   ├── tools/              # 工具定义
│   └── events/             # 事件数据类型
└── examples/
```

### 9.3 RAG 设计参考点

- OpenHands 不直接涉及 RAG。其可借鉴点主要在**执行规范**和**隔离边界**上。

### 9.4 Agent 编排参考点

1. **Action-Observation 循环**：Agent 发出 Action，Runtime 执行并返回 Observation。这个循环是 Agent 与外部世界交互的核心模式。本项目 Agent 与 RAG、模型、文件系统的交互也可建模为 action-observation。
2. **Event Stream**：所有交互记录为事件日志，便于回溯、审计和 demo 展示。本项目的 `AgentTaskState` 可记录每次步骤的输入输出事件。
3. **Agent 权限控制**：Agent 只能执行被允许的操作（读允许的文件、写允许的字段）。这直接影响本项目的 `AGENTS.md` 和任务卡设计——每个任务卡必须声明允许/禁止修改的文件。
4. **Workflow 作为一等公民**：任务有明确的开始、执行步骤、完成/失败状态，不是开放式的对话。

### 9.5 工程化和 Demo 展示参考点

1. **事件回放**：通过 event stream 可以完整回放 Agent 的执行过程。本项目的 demo 可借鉴此设计。
2. **状态可视化**：界面展示当前 Agent 状态、最近动作、文件变更。
3. **错误处理**：Agent 出错时有清晰的错误信息和恢复建议。

### 9.6 不适合本项目照搬的原因

1. **面向代码工程**：OpenHands 的核心能力是让 Agent 写代码、执行命令、修改文件。本项目是求职资料 RAG 应用，不需要这些能力。
2. **Docker/K8s 依赖**：Sandbox 需要容器环境。学校服务器可能不支持。
3. **代码执行安全风险**：Agent 执行代码需要严格沙箱，这不是本项目的关注点。
4. **复杂的 event 系统**：OpenHands 的 event stream 是生产级设计，第一阶段用简单的日志即可。

### 9.7 对 career-agent-assistant 的具体启发

1. **Agent 执行边界是最重要的启发**：
   - 每个任务卡必须声明 `允许修改文件` 和 `禁止修改文件`。
   - Agent 执行前必须检查 `git status`。
   - Agent 不能跨任务卡声明的边界操作。
2. **日志设计**：每次 Agent 执行记录 step_name、input_summary、output_summary、timestamp、errors。
3. **任务卡即规范**：OpenHands 的 task 定义对应本项目的 `docs/superpowers/tasks/*.md` 任务卡。
4. **"不写代码" 的思维方式**：OpenHands 强调 Agent 应知道 "何时不该写代码"。本项目 Agent（尤其是 BuildAgent）应知道 "何时应拒绝编造经历"。

---

## 10. Khoj

参考来源：
- https://github.com/khoj-ai/khoj
- https://github.com/khoj-ai

### 10.1 项目定位

Khoj 是**自托管个人 AI / second brain**，核心理念是 "你的数据，你的 AI"。用户可以将个人笔记、文档、图片等导入 Khoj，然后通过自然语言对话来搜索、问答和获取洞察。Khoj 支持本地部署和云端扩展。

### 10.2 典型目录结构

基于公开仓库推断：

```text
khoj/
├── src/khoj/
│   ├── processor/          # 内容处理器（不同文件类型）
│   ├── search_filter/      # 搜索与过滤
│   ├── database/           # 向量数据库适配
│   ├── router/             # API 路由
│   └── utils/
├── web/                    # Web 前端
├── docs/
└── docker/
```

### 10.3 RAG 设计参考点

1. **个人数据优先**：Khoj 的核心场景是 "搜索我的笔记/文档"，而非通用搜索。这与本项目的 "搜索我的能力资料" 高度一致。
2. **多格式内容处理器**：支持 Markdown、PDF、图片、网页等格式的内容摄入。本项目第一阶段只需 Markdown，但接口设计应不排斥后续扩展。
3. **增量索引**：新增或修改文档后，只更新变化部分而非全量重建。第一阶段的 sample 数据量小，可以不实现，但应了解这个方向。
4. **搜索结果与 LLM 结合**：检索到的文档片段作为 LLM 的上下文，生成有据可查的回答。

### 10.4 Agent 编排参考点

- Khoj 的 Agent 能力相对简单，主要是 "对话 Agent + 搜索工具" 的组合。
- 对话历史管理是重要组件，支持多轮上下文。
- 搜索策略可根据对话意图调整（如追问时缩小搜索范围）。

### 10.5 工程化和 Demo 展示参考点

1. **自托管优先**：支持一键 Docker 部署和个人服务器运行。本项目学校服务器部署可参考。
2. **本地优先**：数据存储在本地，不依赖云服务。本项目也应优先本地数据。
3. **渐进式复杂度**：基础功能（搜索、问答）易用，高级功能（自动化、research）可选。

### 10.6 不适合本项目照搬的原因

1. **功能过宽**：Khoj 覆盖个人知识搜索、日程管理、自动化、deep research 等，本项目只需聚焦求职投递。
2. **多用户支持**：Khoj 支持多用户，而本项目是单用户工具。
3. **持续索引**：Khoj 需要持续监控文件变化并更新索引，本项目第一阶段的 sample 数据是一次性的。
4. **完整的 Web 和移动端**：Khoj 有 Web 界面和移动 App，本项目不需要。

### 10.7 对 career-agent-assistant 的具体启发

1. **"个人能力知识库"定位**：这是 Khoj 给本项目最大的启发。用户维护一份 Markdown 能力资料，AI 基于这份资料做匹配分析和输出生成。
2. **自托管展示**：学校服务器上运行，访问者可以看到完整的 "输入资料 → 检索证据 → 分析匹配 → 输出结果" 流程。
3. **数据可控**：用户资料完全在本地，不上传云端。这对求职场景的数据隐私很重要。
4. **对话 + 检索的结合方式**：虽然第一阶段可能是单轮匹配，但后续可支持 "追问某段经历" 的多轮交互。

---

## 11. Flowise

参考来源：
- https://github.com/FlowiseAI/Flowise
- https://docs.flowiseai.com/
- https://docs.flowiseai.com/getting-started
- https://docs.flowiseai.com/using-flowise/document-stores
- https://docs.flowiseai.com/using-flowise/agentflowv2

### 11.1 项目定位

Flowise 是**开源低代码 LLM workflow 可视化构建平台**。用户通过拖拽节点（如 Document Loader、Text Splitter、Vector Store、LLM Chain、Agent 等）来构建 AI 应用，无需写代码。Flowise 采用 Node.js + React monorepo 架构。

### 11.2 典型目录结构

```text
flowise/
├── packages/
│   ├── server/             # Node.js 后端服务
│   ├── ui/                 # React 前端 UI
│   ├── components/         # 可拖拽组件定义
│   │   ├── documentstores/ # Document Store 节点
│   │   ├── embeddings/     # Embedding 节点
│   │   ├── llms/           # LLM 节点
│   │   ├── agents/         # Agent 节点
│   │   ├── tools/          # Tool 节点
│   │   └── chains/         # Chain 节点
│   └── api-documentation/
├── docker/
└── docs/
```

### 11.3 RAG 设计参考点

1. **Document Stores 节点**：清晰的文档处理流程节点——Document Loader → Text Splitter → Embeddings → Vector Store → Retriever。每个节点职责单一，可替换。这种节点化思维可直接用于本项目的 RAG pipeline 设计。
2. **Vector Store 抽象**：支持多种向量数据库（Pinecone、Weaviate、Chroma、Qdrant 等）。本项目也应定义 `VectorStore` 接口，第一阶段用 memory/lightweight 实现。
3. **Upsert 和查询分离**：索引写入和检索查询是独立操作。

### 11.4 Agent 编排参考点

1. **Agentflow V2**：引入 Flow State 概念，每个节点可以读取/更新全局状态。这对应 LangGraph 的 State 思想，也对应本项目的 `AgentTaskState`。
2. **多 Agent 节点**：单个 workflow 中可以有多个 Agent 节点，每个负责不同任务。对应本项目的四个核心 Agent。
3. **Human-in-the-Loop 节点**：可在 workflow 中插入需要人工确认的步骤。本项目后续可在此位置加入用户审核（如 "匹配分析是否合理？"）。

### 11.5 工程化和 Demo 展示参考点

1. **Marketplace 模板**：预置 workflow 模板，一键导入使用。本项目后续可提供 "示例 JD + 示例用户资料" 的模板组合。
2. **流程可视化**：每个节点执行状态（pending / running / done / error）直观可见。本项目的 Streamlit demo 应展示类似的状态流。
3. **Tracing & Analytics**：追踪每个节点的输入输出和耗时。对应本项目的日志和评估。

### 11.6 不适合本项目照搬的原因

1. **低代码平台路线**：Flowise 的核心价值是 "不用写代码搭 AI 应用"，这需要完整的可视化编辑器和平台。本项目使用者是开发者，不需要低代码。
2. **Node / React monorepo**：技术栈与 Python 工具不一致，增加维护成本。
3. **拖拽编辑器复杂度**：可视化编辑器开发工作量巨大，且不是本项目的核心需求。
4. **平台化倾向**：Flowise 正在向多用户、团队协作、企业版发展，与个人工具定位不符。

### 11.7 对 career-agent-assistant 的具体启发

1. **"流程可见" 是 demo 的关键**：虽然不做拖拽编辑器，但 Streamlit 页面可以逐步展示 JD 解析结果、检索到的证据、匹配分析、最终输出——每一步都可展开查看。
2. **节点化思维用于文档，而非代码**：用 Markdown 表格或 Mermaid 流程图描述 "JD Parser → RAG Retrieve → Match Analysis → Build"，帮助 reviewer 理解系统。
3. **模板化 demo**：提供 1-2 套完整的 "示例 JD + 用户资料 + 完整输出" 组合，作为 demo 素材。
4. **Document Store 的产品化思维**：用户资料的 "上传 → 解析 → 分块 → 入库 → 检索" 是核心流程，应在 demo 中展示。

---

## 12. 八个项目横向对比

### 12.1 定位对比

| 维度 | LangGraph | LangGraph RAG | Dify | RAGFlow | DeerFlow | OpenHands | Khoj | Flowise | career-agent-assistant |
|---|---|---|---|---|---|---|---|---|---|
| 类型 | 框架 | 示例 | 平台 | 引擎 | Harness | 平台+SDK | 个人AI | 低代码平台 | CLI 工具+轻量展示 |
| 用户 | 开发者 | 开发者 | 应用构建者 | 企业 | 开发者 | 工程师 | 个人用户 | 非开发者 | 求职者/面试官 |
| 部署 | pip install | Notebook | Docker | Docker | Docker | Docker | Docker/云 | Docker | 本地+学校服务器 |
| 技术栈 | Python | Python | Python+TS | Python | Python+TS | Python+TS | Python+TS | Node+React | Python |

### 12.2 RAG 设计对比

| 维度 | LangGraph RAG | Dify | RAGFlow | Khoj | Flowise | 本项目采用 |
|---|---|---|---|---|---|---|
| 文档输入 | 通用 | 多格式 | 复杂文档 | 个人笔记 | 多格式 | 本地 Markdown |
| Chunk 策略 | 可配置 | 可配置 | 模板化 | 按格式 | 可视化选择 | 按 section 分块 |
| 检索模式 | 向量+路由 | 混合 | 混合+引用 | 向量 | 多种 | 向量（预留混合接口） |
| 证据追溯 | score+grade | 来源标注 | citation | 片段引用 | 流程可视 | score+reason+source+quote |
| 自校正 | 多轮循环 | 评测 | Rerank | 动态上下文 | 条件边 | 第一阶段预留接口 |

### 12.3 Agent 编排对比

| 维度 | LangGraph | DeerFlow | OpenHands | Flowise | 本项目采用 |
|---|---|---|---|---|---|
| 编排模式 | StateGraph | Supervisor | Controller | Agentflow | 普通 Python workflow |
| 状态管理 | Shared State | Memory+State | Event Stream | Flow State | AgentTaskState |
| 多 Agent | 条件路由 | Sub-agent | 单Agent+工具 | 多Agent节点 | 四个固定 Agent |
| 隔离 | Checkpoint | Sandbox | Sandbox | 节点边界 | 任务卡+字段边界 |
| 持久化 | Thread持久化 | Memory后端 | Event日志 | 流程保存 | 日志+任务卡 |

### 12.4 工程化对比

| 维度 | Dify | RAGFlow | DeerFlow | OpenHands | 本项目采用 |
|---|---|---|---|---|---|
| 前端 | React | React | React | React | Streamlit（仅展示） |
| 后端 | Python API | Python API | Python API | Python API | CLI + workflow |
| 数据库 | PostgreSQL | MySQL | PostgreSQL | 多种 | 无（第一阶段） |
| 异步 | Celery | 内置 | 内置 | 内置 | 无（第一阶段） |
| 部署 | Docker Compose | Docker Compose | Docker | Docker | pip + 本地运行 |

---

## 13. 本项目应采用的参考组合

本项目不照搬任何一个大型平台，而是从八个项目中各取所长：

### 13.1 架构思想层

| 来源 | 采用的思想 | 具体应用 |
|---|---|---|
| LangGraph | 状态化 workflow | `AgentTaskState` 设计，预留 LangGraph 迁移路径 |
| LangGraph RAG | 检索后评估 | `RetrievedEvidence.score/reason`，预留 ReviewAgent |
| Dify | 知识库生命周期 | Demo 展示 "资料→加载→分块→检索" 流程 |
| RAGFlow | RAG pipeline 分层 | Loader / Chunker / VectorStore / Retriever / Pipeline 分层 |
| DeerFlow | Agent 边界与 memory 分层 | Agent 只操作自己字段，memory 与上下文分离 |
| OpenHands | 执行边界和日志 | 任务卡声明允许/禁止操作，每步记录日志 |
| Khoj | 个人数据优先 | 本地 Markdown 知识库，自托管展示 |
| Flowise | 流程可视化 | Streamlit 逐步展示，Markdown/Mermaid 解释流程 |

### 13.2 具体设计决策

```text
状态管理：AgentTaskState（LangGraph 风格，普通 Python 实现）
RAG 分层：Loader → Chunker → VectorStore → Retriever → Pipeline（RAGFlow 风格）
Agent 编排：四个固定 Agent，普通 workflow（简化的 DeerFlow 模式）
执行规范：任务卡 + AGENTS.md + git status 检查（OpenHands 风格）
数据边界：本地 Markdown 优先，个人知识库定位（Khoj 风格）
Demo 展示：CLI + Streamlit 逐步展示流程（Flowise 可视化思想）
Prompt 管理：`.md` 文件管理模板（简化的 Dify Prompt IDE 思想）
模型抽象：provider 接口，不绑定具体模型（Dify/RAGFlow 模型管理思想）
```

### 13.3 不采用的路线

| 路线 | 代表项目 | 不采用原因 |
|---|---|---|
| 完整 AI 应用平台 | Dify | 前后端、队列、权限、多用户体系太重 |
| 企业级 RAG 引擎 | RAGFlow | 复杂文档解析、OCR、ES 等依赖超出需求 |
| 低代码可视化平台 | Flowise | Node/React monorepo、拖拽编辑器工作量巨大 |
| Super Agent 框架 | DeerFlow | sandbox、skills marketplace、supervisor 路由过度设计 |
| 软件工程 Agent | OpenHands | 代码修改、命令执行不是本项目关注点 |
| 个人 second brain | Khoj | 功能过宽（日程、自动化、research） |
| 框架级依赖 | LangGraph | 第一阶段固定流程不需要复杂图路由 |
| Agentic RAG 全套 | LangGraph RAG | 多轮自校正、外部搜索第一阶段不需要 |

---

## 14. 第一阶段技术路线确认

基于以上调研，本项目的**第一阶段技术路线**明确如下：

| 维度 | 选择 | 依据 |
|---|---|---|
| 输入 | 本地 Markdown 用户资料 + JD 文本 | Khoj 个人知识库思想 + RAGFlow 分层处理 |
| RAG | 分层 pipeline，向量检索 | RAGFlow/Dify 的分层 + Flowise 的节点化 |
| Agent | 四个固定 Agent，普通 Python workflow | DeerFlow sub-agent 边界 + LangGraph 状态思想 |
| 状态 | AgentTaskState（dataclass/TypedDict） | LangGraph 状态设计，预留迁移路径 |
| 输出 | Markdown + CLI + Streamlit | Flowise 流程可视化思想 + Khoj 自托管 |
| 部署 | 本地 pip install + 学校服务器 | Khoj 自托管理念，不依赖 Docker |
| 模型 | provider 接口抽象 | Dify/RAGFlow 的模型管理思想 |
| 评估 | 独立 evaluation 模块 | LangGraph RAG 的评估思维 + RAGFlow 的召回测试 |
| 文档 | 任务卡 + 设计文档 + journal | OpenHands 的执行规范思想 |

---

## 15. 结论

1. **LangGraph**、**Dify**、**RAGFlow**、**DeerFlow**、**OpenHands**、**Khoj**、**Flowise** 这七个项目（加上 LangGraph RAG examples 共八个）分别代表了 Agent 框架、AI 平台、RAG 引擎、Super Agent、软件工程 Agent、个人知识库、低代码平台和 Agentic RAG 示例八个不同方向。

2. 每个项目都有值得学习的设计思想，但**没有一个项目可以直接照搬**——它们的定位、技术栈、复杂度都远超本项目的需求。

3. 第一阶段应保持轻量：**本地 Markdown 资料 + 清晰 RAG pipeline + 四个核心 Agent + 普通 Python workflow + CLI/Markdown 输出 + Streamlit 轻量展示**。

4. Dify、RAGFlow、Flowise、DeerFlow 这类项目说明了复杂平台最终可以长什么样，但当前阶段更重要的是把**模块边界、证据追溯、状态流和 demo 可复现性**做好。

5. 后续进入 ARCH-003 时，本项目将基于这些参考思想，最终确定代码目录结构和第一批创建的文件。
