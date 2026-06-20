# 参考架构启发下的本项目架构草案

## 1. 用途

本文档将 ARCH-002 和 DOC-REFERENCE-001 的开源项目调研结果转化为 `career-agent-assistant` 后续代码结构建议。本轮只写文档，不创建这些目录。

## 2. 参考来源映射

每个架构决策都有明确的开源参考来源：

| 架构决策 | 参考项目 | 采用程度 | 说明 |
|---|---|---|---|
| State 设计 | LangGraph | 思想采用，实现裁剪 | AgentTaskState 对齐 LangGraph State 概念，但用普通 dataclass |
| RAG 分层 | RAGFlow / Flowise | 思想采用，实现裁剪 | 五层 pipeline，但只处理 Markdown |
| Evidence schema | LangGraph RAG / RAGFlow | 完整采用 | source/quote/score/reason 四字段 |
| Agent 边界 | OpenHands / DeerFlow | 思想采用 | 字段级隔离 + 任务卡声明 |
| Memory 分层 | DeerFlow | 思想采用 | 长期/工作/短期三层，第一阶段只做前两层 |
| 模型抽象 | Dify / RAGFlow | 完整采用 | provider 接口 + mock 实现 |
| 个人知识库 | Khoj | 定位采用，功能裁剪 | 只做求职场景，不做日程/自动化 |
| 流程展示 | Flowise / Dify | 思想采用 | Streamlit 逐步展示，不做拖拽编辑器 |
| 执行规范 | OpenHands | 完整采用 | 任务卡声明允许/禁止，执行前 git status |
| Demo 模板化 | Flowise | 思想采用 | 示例 JD + 示例资料 + 完整输出组合 |

## 3. 总体原则

- 采用 LangGraph 的状态化 workflow 思想，但第一阶段不强制引入 LangGraph。
- 采用 RAGFlow 的 RAG pipeline 分层思想。
- 采用 LangGraph RAG examples 的 evidence 评估思想。
- 采用 OpenHands / DeerFlow 的 Agent 边界和执行隔离思想。
- 采用 Khoj 的个人知识库定位。
- 采用 Flowise / Dify 的流程可视化启发，但不做低代码平台。
- 采用 Dify / RAGFlow 的模型 provider 抽象思想。

## 4. ARCH-003 最终代码目录决策

ARCH-003 最终确认：第一阶段采用 `src/career_agent/` 作为 Python package，但本轮不创建该目录。后续具体创建目录和文件必须进入 RAG、Agent、Workflow、Demo 等实现任务。

最终建议结构如下：

```text
src/
└── career_agent/
    ├── __init__.py
    ├── rag/
    │   ├── __init__.py
    │   ├── schemas.py
    │   ├── loaders/
    │   │   └── markdown_loader.py
    │   ├── chunking/
    │   │   └── text_chunker.py
    │   ├── vectorstores/
    │   │   ├── base.py
    │   │   └── memory_store.py
    │   ├── retrievers/
    │   │   └── simple_retriever.py
    │   └── pipeline.py
    │
    ├── agents/
    │   ├── __init__.py
    │   ├── state.py
    │   ├── jd_parser.py
    │   ├── rag_retrieve_agent.py
    │   ├── match_analysis_agent.py
    │   └── build_agent.py
    │
    ├── workflows/
    │   ├── __init__.py
    │   └── job_match_workflow.py
    │
    ├── models/
    │   ├── __init__.py
    │   ├── provider.py
    │   └── mock_provider.py
    │
    ├── evaluation/
    │   ├── __init__.py
    │   ├── rag_eval.py
    │   └── output_eval.py
    │
    └── utils/
        ├── __init__.py
        └── text.py

tests/
├── rag/
├── agents/
├── workflows/
├── models/
└── evaluation/

data/
└── samples/
    ├── profile/
    └── jobs/

outputs/
└── demo/

demo/
├── cli/
└── streamlit/
```

## 5. 第一阶段创建边界

第一阶段可以在后续实现任务中创建：

- `src/career_agent/rag/`
- `src/career_agent/agents/`
- `src/career_agent/workflows/`
- `src/career_agent/models/`
- `src/career_agent/evaluation/`
- `src/career_agent/utils/`
- `tests/rag/`
- `tests/agents/`
- `tests/workflows/`
- `tests/models/`
- `tests/evaluation/`
- `data/samples/profile/`
- `data/samples/jobs/`
- `demo/cli/`
- `demo/streamlit/`

第一阶段仍禁止创建：

- `frontend/`
- `backend/`
- `server/`
- `app/`
- `scripts/`

`pyproject.toml` 和 `requirements.txt` 暂不在 ARCH-003 中创建。是否引入由后续“工程配置任务”单独决定。

## 6. 第二阶段再创建的目录

第二阶段如果进入服务化或产品化，再考虑：

- `frontend/`
- `backend/`
- `server/`
- API 服务层
- 账号系统
- 任务历史数据库
- 复杂部署脚本

## 7. 关键结构决策

### 是否使用 `src/career_agent` package

结论：使用。

原因：

- 方便测试和导入。
- 项目边界清楚。
- 后续可以扩展为包。
- 避免 `src/` 根目录杂乱。
- 仓库名 `career-agent-assistant` 包含连字符，不适合作为 Python import 名称；`career_agent` 更稳定。

### RAG 模块如何拆分

RAG 拆成 schema、loader、chunking、vectorstore、retriever、pipeline 六层。这样可以先用 Markdown + MemoryVectorStore 验证链路，后续替换 Chroma / FAISS 时不影响 Agent。

### Agent 模块如何拆分

Agent 拆成 `state.py` 和四个核心 Agent 文件。每个 Agent 只读写 `AgentTaskState` 中自己的字段，避免上下文污染。

### Workflow 模块如何拆分

第一阶段只实现 `job_match_workflow.py`。不创建 `graph_workflow.py` 的实际文件，直到决定引入 LangGraph。

### Models / Provider 是否第一阶段设计

结论：第一阶段保留 `models/provider.py` 和 `models/mock_provider.py`。先用 MockProvider 或 RuleBasedProvider 支持测试和 demo，后续再接 DeepSeek / OpenAI / 本地模型。

### Evaluation 是否第一阶段保留

结论：保留。RAG 和输出生成的质量必须能被评估，否则 demo 只证明“能生成”，不能证明“可信”。

### Demo 层放在哪里

结论：采用仓库根目录下的 `demo/cli/` 和 `demo/streamlit/`。

原因：

- demo 是运行入口和展示层，不属于核心 package。
- CLI demo 优先。
- Streamlit demo 第二步。
- Demo 只能调用 workflow，不允许重写 RAG / Agent 业务逻辑。

### 是否创建 `app/streamlit_app.py`

结论：不创建。`app/` 容易暗示独立应用层或 Web 服务入口，第一阶段使用 `demo/streamlit/app.py` 更符合“展示层”定位。

### 是否现在引入 `pyproject.toml`

结论：ARCH-003 不引入。后续如需 pytest、ruff、editable install，再由独立工程配置任务决定。

### 是否现在引入 LangGraph

结论：不引入。第一阶段先用普通 Python workflow，保留 `AgentTaskState` 兼容 LangGraph 的设计。

## 8. 后续代码目录建议

建议后续进入实现阶段时，采用 Python package 结构：

```text
src/
└── career_agent/
    ├── rag/
    │   ├── schemas.py          # ProfileItem, ProfileDocument, DocumentChunk, RetrievedEvidence
    │   ├── loaders/
    │   │   └── markdown_loader.py  # MarkdownProfileLoader（第一阶段唯一 loader）
    │   ├── chunking/
    │   │   └── text_chunker.py     # 文本清洗 + 按 section 分块
    │   ├── vectorstores/
    │   │   ├── base.py             # VectorStore 接口
    │   │   └── memory_store.py     # 内存/轻量实现（第一阶段）
    │   ├── retrievers/
    │   │   └── simple_retriever.py # 向量检索 + 结果封装为 RetrievedEvidence
    │   └── pipeline.py             # 组合 loader/chunker/vectorstore/retriever
    │
    ├── agents/
    │   ├── state.py                # AgentTaskState
    │   ├── jd_parser.py            # JDParserAgent：解析 JD 文本
    │   ├── rag_retrieve_agent.py   # RAGRetrieveAgent：调用 RAG pipeline
    │   ├── match_analysis_agent.py # MatchAnalysisAgent：匹配分析
    │   └── build_agent.py          # BuildAgent：基于 evidence 生成输出
    │
    ├── workflows/
    │   ├── job_match_workflow.py   # 第一阶段固定编排
    │   └── graph_workflow.py       # 后续 LangGraph 版本入口（预留）
    │
    ├── models/
    │   ├── provider.py             # ModelProvider 接口
    │   └── mock_provider.py        # Mock/rule-based 实现
    │
    ├── evaluation/
    │   ├── rag_eval.py             # RAG 检索质量评估
    │   └── output_eval.py          # 输出质量评估（是否引用证据、是否编造）
    │
    └── utils/
        └── logger.py               # 执行日志

tests/
├── rag/
│   ├── test_schemas.py
│   ├── test_loader.py
│   ├── test_chunking.py
│   ├── test_vectorstore.py
│   └── test_retriever.py
├── agents/
│   ├── test_state.py
│   ├── test_jd_parser.py
│   ├── test_rag_retrieve.py
│   ├── test_match_analysis.py
│   └── test_build_agent.py
├── workflows/
│   └── test_job_match_workflow.py
└── evaluation/
    ├── test_rag_eval.py
    └── test_output_eval.py
```

## 5. RAG 模块设计详述

### 5.1 `rag/schemas.py` — 核心数据契约

**参考来源**：RAGFlow 的 Dataset/Chunk 概念 + LangGraph RAG 的 document grading 字段

```python
# 概念示意（非实际代码）
class ProfileItem:
    """用户资料中的一条经历/技能"""
    item_id: str
    section: str        # 所属分区（education/skills/projects/internship）
    title: str          # 条目标题
    content: str        # 原始内容
    tags: list[str]     # 标签（技能关键词等）

class DocumentChunk:
    """切分后的文本块"""
    chunk_id: str
    content: str
    metadata: dict      # source_file, section, item_id, chunk_index
    embedding: list[float] | None

class RetrievedEvidence:
    """检索到的证据"""
    chunk: DocumentChunk
    score: float        # 相关性评分
    reason: str         # 评分理由
    source: str         # 来源文件路径
    quote: str          # 原文引用
```

### 5.2 `rag/loaders/` — 文档加载

**参考来源**：RAGFlow 的 Parser 层 + Flowise 的 Document Loader 节点

- `MarkdownProfileLoader`：读取本地 Markdown 文件，按 section 解析为 `ProfileItem` 列表。
- 第一阶段只处理 Markdown，后续可扩展 `GitHubProfileLoader`、`JSONResumeLoader` 等。
- 加载器输出 `list[ProfileItem]`，不直接对接 chunking——中间可以插入清洗步骤。

### 5.3 `rag/chunking/` — 文本分块

**参考来源**：RAGFlow 的 Chunk 模板机制

- 按 section 分块：每个 section（如 "项目经历"）下的每个 item 独立成 chunk。
- Chunk 必须保留 metadata：`source_file`、`section`、`item_id`。
- 文本清洗：去除多余空白、统一标点、保留 Markdown 结构。
- Chunk 策略应可配置（chunk_size、overlap、分隔符），但第一阶段用默认值。

### 5.4 `rag/vectorstores/` — 向量存储

**参考来源**：Flowise 的 Vector Store 抽象 + RAGFlow 的索引层

- `VectorStore` 接口：`add_chunks(chunks: list[DocumentChunk])`、`search(query_embedding, top_k)`。
- 第一阶段实现 `MemoryVectorStore`：基于 numpy 的内存向量存储。
- 后续可接入 Chroma、FAISS、Qdrant 等，只需实现相同接口。

### 5.5 `rag/retrievers/` — 检索策略

**参考来源**：LangGraph RAG 的 query analysis + RAGFlow 的检索模式

- `SimpleRetriever`：接收查询文本 → 生成 embedding → 向量检索 → 封装为 `RetrievedEvidence`。
- 检索结果附带 score 和 reason，reason 由 LLM 对 top-K 结果做相关性判断生成。
- 后续可扩展 `HybridRetriever`（向量 + 关键词混合检索）。

### 5.6 `rag/pipeline.py` — 流水线编排

**参考来源**：RAGFlow 的 RAG pipeline 设计

- 组合 loader、chunker、vectorstore、retriever，提供 `build_index()` 和 `retrieve(query)` 两个入口。
- `build_index()`：加载文档 → 分块 → 向量化 → 入库。
- `retrieve(query)`：生成 query embedding → 检索 → 返回 `list[RetrievedEvidence]`。

## 6. Agent 模块设计详述

### 6.1 `agents/state.py` — 共享状态

**参考来源**：LangGraph 的 State 概念 + DeerFlow 的 memory 分层

```python
# 概念示意
class AgentTaskState:
    """多 Agent 共享的任务状态"""
    task_id: str
    jd_text: str                      # 输入：JD 原文
    parsed_jd: dict | None            # JDParserAgent 输出
    retrieved_evidence: list | None   # RAGRetrieveAgent 输出
    match_analysis: dict | None       # MatchAnalysisAgent 输出
    final_output: str | None          # BuildAgent 输出
    errors: list[dict]                # 错误记录
    step_log: list[dict]              # 每步执行日志
```

### 6.2 四个核心 Agent — 边界定义

**参考来源**：DeerFlow 的 sub-agent 工具边界 + OpenHands 的权限声明

| Agent | 读取字段 | 写入字段 | 调用权限 | 禁止行为 |
|---|---|---|---|---|
| JDParserAgent | `jd_text` | `parsed_jd` | LLM provider | 不能读文件、不能调用 RAG |
| RAGRetrieveAgent | `parsed_jd` | `retrieved_evidence` | RAG pipeline | 不能写文件、不能直接调 LLM |
| MatchAnalysisAgent | `parsed_jd` + `retrieved_evidence` | `match_analysis` | LLM provider | 不能编造经历、不能修改 evidence |
| BuildAgent | `match_analysis` + `retrieved_evidence` | `final_output` | LLM provider | 不能编造经历、不能修改匹配结论 |

## 7. Workflow 模块设计详述

### 7.1 第一阶段固定流程

**参考来源**：LangGraph 的图结构思想 + Flowise 的节点编排思想

```text
输入 JD 文本
    │
    ▼
JDParserAgent          # 解析 JD：提取技能要求、经历偏好等
    │
    ▼
RAGRetrieveAgent       # 基于解析结果检索用户资料
    │
    ▼
MatchAnalysisAgent     # 对比 JD 要求与检索证据，做匹配分析
    │
    ▼
BuildAgent             # 基于 evidence 和 analysis 生成输出
    │
    ▼
输出结果（Markdown）
```

每个 Agent 执行后更新 `AgentTaskState` 和 `step_log`。

### 7.2 后续 LangGraph 版本预留

**参考来源**：LangGraph 的条件边和 checkpoint

`graph_workflow.py` 预留以下能力：
- 条件边：`retrieval_quality` 不足 → 触发 query rewrite 或重试。
- Checkpoint：每个节点执行后保存状态快照，支持回放。
- Human-in-the-loop：在 MatchAnalysis 后暂停，等待用户确认。

第一阶段不实现，但 `AgentTaskState` 需包含 `retrieval_quality` 和 `checkpoint_id` 字段预留。

## 8. Models 模块设计详述

### 8.1 模型 Provider 接口

**参考来源**：Dify 的模型管理 + RAGFlow 的 LLM 集成

- `ModelProvider` 接口：`generate(prompt, system_prompt, **kwargs) -> str`。
- `DeepSeekProvider`：接入 DeepSeek API。
- `MockProvider`：rule-based 输出，用于测试和 demo 兜底。
- 后续可扩展 `OpenAIProvider`、`ClaudeProvider` 等。

### 8.2 为什么不直接绑定 DeepSeek

- 后续可能切换到 Claude、OpenAI 或其他模型。
- Demo 和测试需要 mock 输出，避免 API 调用。
- Provider 接口隔离后，业务代码不感知具体模型。

## 9. Evaluation 模块设计详述

### 9.1 `evaluation/rag_eval.py` — RAG 检索评估

**参考来源**：RAGFlow 的召回测试 + LangGraph RAG 的 document grading

- 检查检索是否命中正确 section（如 JD 要求 "Python"，应检索到技能 section 中的 Python 条目）。
- 检查 `RetrievedEvidence` 是否包含 source、quote。
- 计算 hit rate、MRR 等基本指标。

### 9.2 `evaluation/output_eval.py` — 输出质量评估

**参考来源**：LangGraph RAG 的 evidence→answer 一致性检查

- 检查生成内容是否引用真实资料。
- 检查是否编造经历（输出中的技能是否在检索证据中出现）。
- 检查输出格式是否符合要求（Markdown 结构、必要字段）。

## 10. Demo 模块设计详述

### 10.1 Demo 层原则

**参考来源**：Flowise 的流程可视化 + Dify 的应用发布

- Demo 层只能调用 workflow，不能重写 RAG 或 Agent 逻辑。
- CLI demo 是最稳定路径，输出 Markdown 文本。
- Streamlit demo 只做展示层：输入框 → 执行按钮 → 逐步展示中间结果。

### 10.2 CLI Demo 设计

```text
$ python -m career_agent.cli --jd sample_jd.md --profile sample_profile.md
# 输出：
# [Step 1/4] JD 解析完成（耗时 2.3s）
# [Step 2/4] 检索到 5 条相关经历（耗时 1.8s）
# [Step 3/4] 匹配分析完成（耗时 3.1s）
# [Step 4/4] 输出生成完成（耗时 2.0s）
# → 结果写入 output/
```

### 10.3 Streamlit Demo 设计

- 左侧：输入区（JD 文本、用户资料选择）。
- 右侧：输出区（逐步展示，每步可展开）。
- 展示内容：JD 解析摘要、检索到的证据卡片（含原文引用和评分）、匹配分析详情、最终输出。
- 不做拖拽编辑器、不做流程配置。

## 11. 配置模块建议

**参考来源**：Dify 的模型配置 + Flowise 的节点参数

第一阶段使用简单配置对象或环境变量：

```python
# 概念示意
class Config:
    model_provider: str = "deepseek"
    model_name: str = "deepseek-chat"
    sample_profile_dir: str = "data/samples/profiles"
    sample_jd_dir: str = "data/samples/jds"
    output_dir: str = "outputs"
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 5
```

不立即引入复杂配置框架（如 Hydra、Pydantic Settings），但预留升级空间。

## 12. 测试目录建议

**参考来源**：OpenHands 的测试覆盖思路

测试按模块分层，优先覆盖：
1. Schema：数据结构正确性。
2. Loader：正确解析 Markdown 用户资料。
3. Chunking：正确切分和保留 metadata。
4. VectorStore：正确存取和检索。
5. Retriever：正确封装检索结果。
6. Agent：正确读取/写入 State 字段。
7. Workflow：正确编排 Agent 顺序和状态传递。

## 13. 为什么不采用 frontend/backend/server

**参考来源**：对 Dify / Flowise / RAGFlow 架构的反向决策

- 第一阶段核心不是 Web 平台，而是 RAG + Agent 原型。
- 完整前后端会引入部署、接口、状态同步和 UI 复杂度，推迟核心链路验证。
- Dify、Flowise、RAGFlow 都是成熟产品的架构，本项目在第一阶段不需要达到这个工程化水平。

## 14. 为什么不把所有代码直接放在 `src/rag` 和 `src/agents`

- 直接放在 `src/rag` 和 `src/agents` 容易造成包边界模糊。
- 不利于后续安装、导入、测试和部署。
- 使用 `src/career_agent/` 形成清晰 Python package，体现项目语义。

## 15. 为什么使用 `career_agent` 作为 Python package

- `career_agent` 体现项目语义，便于后续导入：

```python
from career_agent.rag.pipeline import RAGPipeline
from career_agent.workflows.job_match_workflow import run_job_match
```

- 方便未来发布、测试和部署。
- 不与仓库名中的连字符（`career-agent-assistant`）冲突。

## 16. 为什么 demo 层应该调用 workflow

**参考来源**：OpenHands 的 "单一真相源" 思想

- Demo 层如果重写业务逻辑，会导致 CLI、Streamlit 和测试输出不一致。
- 正确方式：Demo 输入 → 调用 workflow → 展示 workflow 输出。
- 这样可以保证核心逻辑只在 RAG、Agent、Workflow 层维护。

## 17. 与开源项目的关键差异总结

| 维度 | Dify/RAGFlow/Flowise | 本项目 |
|---|---|---|
| 用户 | 应用构建者/企业 | 求职者个人 |
| 输入 | 多格式文档/数据库 | 本地 Markdown 个人资料 |
| 交互 | Web 平台 + 拖拽编排 | CLI + Streamlit 展示 |
| 部署 | Docker Compose（多服务） | pip install + 本地运行 |
| 数据 | 平台数据库 + 云存储 | 本地文件系统 |
| 扩展 | 插件/Marketplace/API | 后续 `src/` 下扩展 |
| 定位 | 通用 AI 平台 | 特定领域工具 |

## 18. 后续决策

ARCH-003 需要最终确认：

- 是否采用 `src/career_agent/` package。
- 是否立即创建 `pyproject.toml`。
- demo 入口放在哪里（`src/career_agent/cli.py` 或 `src/career_agent/interfaces/cli.py`）。
- `graph_workflow.py` 是否只预留，不实现。
- 第一批实现任务创建哪些目录。
- `AgentTaskState` 的具体字段和类型。
- `RetrievedEvidence` 的完整 schema。
