# 项目日志

## 2026-06-20

### AGENT-003 RAGRetrieveAgent

- Executor: Claude Code + DeepSeek
- Type: implementation / agent-rag-retrieve
- Summary:
  - 实现 RAGRetrieveAgent，包装 RAGPipeline。
  - build_query_from_parsed_jd 从 ParsedJD 构造检索 query。
  - 支持 retrieve 和 retrieve_by_query 两种检索方式。
- Changed files:
  - src/career_agent/agents/rag_retrieve_agent.py
  - tests/agents/test_rag_retrieve_agent.py
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 未修改 RAG 模块和已有 Agent。
  - 110 tests passed (61 RAG + 19 state + 18 jd_parser + 12 rag_retrieve).
- Next:
  - AGENT-004 MatchAnalysisAgent

### AGENT-002 JDParserAgent

- Executor: Claude Code + DeepSeek
- Type: implementation / agent-jd-parser
- Summary:
  - 实现规则型 JDParserAgent。
  - 从 JD 文本提取 job_title、job_direction、hard/bonus/soft skills、keywords。
  - 不调用 LLM，纯关键词匹配。
- Changed files:
  - src/career_agent/agents/jd_parser.py
  - tests/agents/test_jd_parser.py
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 未修改 state.py 和 RAG 模块。
  - 98 tests passed (61 RAG + 19 state + 18 jd_parser).
- Next:
  - AGENT-003 RAGRetrieveAgent

### AGENT-001 AgentTaskState 设计

- Executor: Claude Code + DeepSeek
- Type: implementation / agent-state
- Summary:
  - 实现 ParsedJD、MatchAnalysisResult、GeneratedOutput、AgentTaskState 四个 dataclass。
  - 使用 default_factory 避免可变对象共享。
  - task_id 自动生成，status 默认为 created。
  - retrieved_evidence 使用已有 RetrievedEvidence 类型。
- Changed files:
  - src/career_agent/agents/__init__.py
  - src/career_agent/agents/state.py
  - tests/agents/test_state.py
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 未修改 RAG 模块。
  - 未实现 Agent 逻辑。
  - 80 tests passed (61 RAG + 19 state).
- Next:
  - AGENT-002 JDParserAgent

### RAG-005 RAGPipeline 集成

- Executor: Codex
- Type: implementation / rag-pipeline
- Summary:
  - 实现 SimpleRetriever。
  - 实现 RAGPipeline。
  - 串联 MarkdownProfileLoader、TextChunker、MemoryVectorStore。
  - 支持从本地 Markdown 目录构建索引并返回 RetrievedEvidence。
- Changed files:
  - src/career_agent/rag/retrievers/__init__.py
  - src/career_agent/rag/retrievers/simple_retriever.py
  - src/career_agent/rag/pipeline.py
  - tests/rag/test_rag_pipeline.py
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 未修改 schema、loader、chunking、vectorstore。
  - 未实现 Agent 或 workflow。
  - 未引入 Chroma / FAISS / LangChain / LangGraph。
  - 测试不依赖外部模型或网络。
- Next:
  - AGENT-001 AgentTaskState 建议交给 Codex。
  - AGENT-002 JDParserAgent 可交给 Claude Code + DeepSeek。

### RAG-004 VectorStore 接口与 MemoryVectorStore

- Executor: Codex
- Type: implementation / rag-vectorstore
- Summary:
  - 定义 VectorStore 抽象接口。
  - 实现 MemoryVectorStore。
  - 支持添加 DocumentChunk、关键词检索、top_k、clear、count。
  - 返回 RetrievedEvidence 列表。
- Changed files:
  - src/career_agent/rag/vectorstores/__init__.py
  - src/career_agent/rag/vectorstores/base.py
  - src/career_agent/rag/vectorstores/memory_store.py
  - tests/rag/test_vectorstore_interface.py
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 未修改 schema、loader、chunking。
  - 未实现 retriever/pipeline。
  - 未引入 Chroma / FAISS / LangChain / LangGraph。
  - 测试不依赖外部模型或网络。
- Next:
  - RAG-005 RAGPipeline 集成建议交给 Codex。

### RAG-003 文本清洗与 Chunk 切分

- Executor: Claude Code + DeepSeek
- Type: implementation / rag-chunking
- Summary:
  - 实现 TextChunker。
  - 支持文本清洗、单文档切分、多文档切分、overlap。
  - 将 ProfileDocument 转换为 DocumentChunk。
  - 添加 chunking 单元测试。
- Changed files:
  - src/career_agent/rag/chunking/__init__.py
  - src/career_agent/rag/chunking/text_chunker.py
  - tests/rag/test_text_chunker.py
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 未修改 RAG schema。
  - 未修改 MarkdownProfileLoader。
  - 未实现 vectorstore/retriever/pipeline。
  - 测试不依赖外部模型或网络。
  - 49 tests passed (6 schema + 20 loader + 23 chunker).
- Next:
  - RAG-004 VectorStore interface 建议交给 Codex。
  - RAG-005 RAG Pipeline 建议交给 Codex。

### RAG-002 Markdown 用户资料加载器

- Executor: Claude Code + DeepSeek
- Type: implementation / rag-loader
- Summary:
  - 实现 MarkdownProfileLoader。
  - 支持读取单个 Markdown 文件和目录。
  - 将 Markdown 文件转换为 ProfileDocument。
  - 添加 loader 单元测试。
- Changed files:
  - src/career_agent/rag/loaders/__init__.py
  - src/career_agent/rag/loaders/markdown_loader.py
  - tests/rag/test_markdown_loader.py
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 未修改 RAG schema。
  - 未实现 chunking/vectorstore/retriever/pipeline。
  - 测试不依赖外部模型或网络。
  - 26 tests passed (6 schema + 20 loader).
- Next:
  - RAG-003 Text Chunking 可继续由 Claude Code + DeepSeek 实现。
  - RAG-004 VectorStore interface 建议交给 Codex。

### SAMPLE-001 示例用户资料与岗位 JD（v2 按新结构重建）

- Executor: Claude Code + DeepSeek
- Type: data / sample
- Summary:
  - 按新目录结构重建 SAMPLE-001：`data/samples/profile/` + `data/samples/jobs/`。
  - 创建 9 份脱敏示例数据文件。
  - 用户资料贴合化学+计算机交叉背景，项目包含智能投递 Agent、自动滴定、Smart Journey、CNN 分类。
  - 4 份 JD 覆盖 Agent 开发、RAG 工程师、AI 应用开发、后端 AI 方向。
- Changed files:
  - data/samples/profile/resume.md
  - data/samples/profile/projects.md（4 个项目）
  - data/samples/profile/github_repos.md（5 个仓库）
  - data/samples/profile/skills.md（7 个技能分区）
  - data/samples/profile/internship.md（2 段实习/实践）
  - data/samples/jobs/agent_intern_jd.md
  - data/samples/jobs/rag_engineer_intern_jd.md
  - data/samples/jobs/ai_application_intern_jd.md
  - data/samples/jobs/backend_ai_intern_jd.md
  - documents/06-demo/02-demo-data.md
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 所有数据为脱敏虚构内容，无真实手机号/邮箱/学号/API Key。
  - 未修改 src/、tests/、outputs/。
  - 未写 Python 业务代码。
  - projects.md 严格按照统一结构：类型/背景/技术栈/个人负责/核心亮点/可匹配岗位/简历依据。
  - JD 覆盖 Agent、RAG、AI 应用、后端四个方向。
- Key decisions:
  - 用户设定为化学+计算机交叉背景，更贴合真实大学生情况（非纯 CS）。
  - 项目经历不过度包装，不使用"精通""独立上线大型平台"等措辞。
  - 智能投递 Agent 项目本身成为用户资料的一部分，体现"自用工具"的产品思维。
- Next:
  - RAG-002 Markdown Loader 可基于新结构读取 `data/samples/profile/`。
  - RAG-003 Text Chunking 可针对 resume/skills/projects 等不同内容类型设计 chunk 策略。

### SAMPLE-001 示例用户资料与岗位 JD（v1 已废弃，被 v2 替代）

- Executor: Claude Code + DeepSeek
- Type: data / sample
- Summary:
  - 第一版创建了 4 份扁平样例数据文件。
  - 已被 v2 按新目录结构替代。
- Changed files (v1, superseded):
  - data/samples/profile.md（已删除）
  - data/samples/projects.md（已删除）
  - data/samples/github_summary.md（已删除）
  - data/samples/jd_agent_intern.md（已删除）



### RAG-001 RAG 核心数据结构设计

- Executor: Codex
- Type: implementation / schema
- Summary:
  - 创建 RAG 核心 schema。
  - 实现 ProfileItem、ProfileDocument、DocumentChunk、RetrievedEvidence。
  - 添加 schema 单元测试。
- Changed files:
  - src/career_agent/rag/schemas.py
  - tests/rag/test_schemas.py
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 仅实现 schema，不实现 loader/chunking/vectorstore/pipeline。
  - 测试不依赖外部模型或网络。
- Next:
  - RAG-002 Markdown Loader 可交给 Claude Code + DeepSeek。
  - RAG-003 Text Chunking 可交给 Claude Code + DeepSeek。
  - RAG-004 VectorStore interface 建议交给 Codex。

### ARCH-003 代码目录结构决策与第一阶段工程骨架规划

- Executor: Codex
- Type: architecture / codebase planning
- Summary:
  - 基于 ARCH-002 开源项目调研结果，确定第一阶段代码目录结构建议。
  - 决定采用 src/career_agent 作为 Python package。
  - 决定第一阶段不做完整 frontend/backend/server。
  - 决定第一阶段先使用普通 Python workflow，后续再接 LangGraph。
  - 决定第一阶段先抽象 VectorStore interface，具体向量库后续替换。
  - 决定 demo 层只调用 workflow，不重写业务逻辑。
  - 补强 RAG、Agent、Workflow、Demo 后续实现任务卡。
- Changed files:
  - documents/02-design/
  - documents/03-technical-decisions/
  - docs/superpowers/tasks/
  - documents/99-project-planning.md
  - documents/97-journal.md
- Validation:
  - 本轮未实现业务代码。
  - 本轮未修改 src/、tests/、data/、outputs/。
  - 本轮未引入依赖。
- Next:
  - RAG-001 可交给 Codex。
  - SAMPLE-001、RAG-002、RAG-003 可交给 Claude Code + DeepSeek。
  - RAG-004、RAG-005、AGENT-001 建议交给 Codex。

### DOC-REFERENCE-001 开源项目参考文档补全

- Executor: Claude Code + DeepSeek
- Type: documentation / research
- Summary:
  - 基于 ARCH-002 调研结果，对 8 个开源项目进行深入分析。
  - 每个项目补充了：项目定位、典型目录结构、RAG 设计参考点、Agent 编排参考点、工程化/demo 参考点、不适合照搬原因、对本项目具体启发。
  - 新增八个项目横向对比表（定位、RAG、Agent、工程化四个维度）。
  - 明确第一阶段技术路线确认矩阵（输入/RAG/Agent/状态/输出/部署/模型/评估/文档）。
  - 确认本项目不采用 Dify/RAGFlow/Flowise 重型平台路线，不采用 DeerFlow/OpenHands 过度设计，不照搬 LangGraph 框架依赖。
- Changed files:
  - documents/99-knowledge-base/05-open-source-reference-projects.md（大幅扩充）
  - documents/97-journal.md（本记录）
  - documents/99-project-planning.md（状态更新）
- Validation:
  - 本轮未实现业务代码。
  - 本轮未修改 src/、tests/、data/、outputs/。
  - 本轮未修改 02-design/、03-technical-decisions/ 已有文件内容。
  - 所有新增内容为中文 Markdown。
  - 未复制开源项目 README 大段内容。
- Key findings:
  - LangGraph：状态化 workflow 思想值得采用，但第一阶段用普通 Python workflow，预留迁移路径。
  - LangGraph RAG：检索后评估（document grading）和 query analysis 思想值得吸收，但多轮自校正第一阶段不需要。
  - Dify：知识库生命周期管理和 workflow 可视化思维值得借鉴，但平台架构不照搬。
  - RAGFlow：RAG pipeline 分层（loader/chunker/vectorstore/retriever/pipeline）是核心启发，但复杂文档解析不需要。
  - DeerFlow：Agent 边界和 memory 分层思想值得采用，但 supervisor/sandbox/skills 过度设计。
  - OpenHands：任务卡声明允许/禁止操作是重要启发，但代码执行和 sandbox 不需要。
  - Khoj："个人知识库"定位是本项目最接近的参考，但功能范围需裁剪为求职场景。
  - Flowise：流程可视化思想用于 demo 展示，但不做低代码平台。
- Next:
  - ARCH-003 代码目录结构决策（Codex 执行）。

### ARCH-002 开源项目调研与参考架构沉淀

- Executor: Codex
- Type: architecture / research / documentation
- Summary:
  - 调研 RAG、多 Agent、个人知识库、AI 应用平台相关开源项目。
  - 总结 LangGraph、Dify、RAGFlow、DeerFlow、OpenHands、Khoj、Flowise 等项目的可借鉴设计。
  - 明确本项目不照搬重型平台，而是裁剪吸收状态化 workflow、RAG pipeline、sub-agent 边界、个人知识库和轻量 demo 设计。
  - 新增参考架构决策文档和后续任务卡。
- Changed files:
  - documents/99-knowledge-base/05-open-source-reference-projects.md
  - documents/03-technical-decisions/06-reference-architecture-selection.md
  - documents/02-design/07-reference-inspired-architecture.md
  - docs/superpowers/tasks/ARCH-002-open-source-reference-research.md
  - docs/superpowers/tasks/DOC-REFERENCE-001-open-source-reference-docs.md
  - docs/superpowers/tasks/ARCH-003-codebase-structure-decision.md
- Validation:
  - 本轮未实现业务代码。
  - 本轮未修改 src/、tests/、data/、outputs/。
  - 本轮未引入依赖。
- Next:
  - 可交给 Claude Code + DeepSeek 继续补充开源项目参考细节。
  - 可由 Codex 执行 ARCH-003，最终确定代码目录结构。

### ARCH-001 补强核心架构边界与模块契约

- Executor: Codex
- Type: architecture / documentation
- Summary:
  - 补强项目总览、需求边界、RAG 模块设计、多 Agent 编排设计。
  - 明确第一阶段采用 CLI + Streamlit，不做完整前后端。
  - 明确第一阶段 RAG 只处理本地 Markdown 用户资料和 GitHub 仓库摘要。
  - 明确第一阶段多 Agent 只包含 JDParserAgent、RAGRetrieveAgent、MatchAnalysisAgent、BuildAgent。
  - 补强后续 RAG、Agent、Workflow、Demo 任务卡。
- Changed files:
  - README.md
  - documents/00-project-overview.md
  - documents/01-requirements/
  - documents/02-design/
  - documents/03-technical-decisions/
  - documents/04-challenges/
  - documents/05-evaluation/
  - documents/06-demo/
  - documents/97-journal.md
  - documents/99-project-planning.md
  - docs/superpowers/
- Validation:
  - 本轮未实现业务代码。
  - 本轮未修改 src/、tests/、data/、outputs/。
  - 本轮未引入依赖。
- Next:
  - 可将 DOC-RUNBOOK-001、SAMPLE-001 交给 Claude Code + DeepSeek。
  - 可将 RAG-001、AGENT-001 保留给 Codex。

### DOC-INIT-001 初始化项目文档体系

- Executor: Codex
- Type: documentation / structure
- Summary:
  - 初始化中文 documents 文档体系。
  - 初始化 docs/superpowers Agent 执行规范体系。
  - 创建 AGENTS.md 多 AI 协作规则。
  - 创建基础目录占位。
- Changed files:
  - README.md
  - AGENTS.md
  - documents/
  - docs/superpowers/
  - src/
  - tests/
  - data/
  - outputs/
- Validation:
  - 本轮未实现业务代码。
  - 本轮未创建 frontend/backend/server。
  - 文档目录采用分层结构，避免 documents 下平铺大量 md。
- Next:
  - 补充 requirements 文档。
  - 补充 RAG 模块设计文档。
  - 补充多 Agent 编排设计文档。
