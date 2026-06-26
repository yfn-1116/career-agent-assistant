# 答辩 Speaker Notes — 代码路径追踪手册

> 对着 PPT 逐章使用。每一节怎么讲、代码在哪、数据怎么流。

---

## ① 项目定位（PPT 第1页）

**PPT 展示：** 是什么 / 不是什么表格

**你需要知道的：**

```
核心原则：Evidence-Grounded — 所有生成内容必须能从知识库找到证据

代码体现：
  evidence/gate.py:46    EvidenceGate.validate(claim, status)
  agents/build_agent.py:240  _build_constraint_metadata() → can_write/needs_confirmation/learning_plan
  approval/gate.py:11    ACTIONS_REQUIRING_APPROVAL — 6 类动作需人工确认
```

---

## ② PPAM 架构总览（PPT 第2页）

**PPT 展示：** 四层架构图 + RAG 贯穿标注

**你需要知道的：**

```
四层包路径：
  perception/  → from career_agent.perception import FileLoader, JDParserAgent
  planning/    → from career_agent.planning import create_langgraph_workflow
  action/      → from career_agent.action import ToolRegistry, EvidenceGate
  memory/      → from career_agent.memory import ConversationMemory

贯穿层 RAG：
  Perception 写入 → Memory 存储 → Action 检索

一条完整请求：
  demo/streamlit/app.py:314  orchestrator.handle(text)
      │
      ▼
  agents/orchestrator.py:70  def handle() → _handle_autonomous() or _handle_ppam()
      │
      ▼
  agents/autonomous_agent.py:56  AutonomousAgent.run(user_message)
      │
      ├── LLM (Qwen/DeepSeek) 自主决策
      ├── ToolRegistry.invoke("parse_jd", ...)
      ├── ToolRegistry.invoke("retrieve_profile", ...)
      └── ToolRegistry.invoke("check_faithfulness", ...)
```

---

## ③ Perception 感知层（PPT 第3-4页）

**PPT 展示：** LLM 调用 Skill/MCP 解析外部信息

**你需要知道的完整代码路径：**

### 怎么讲

> "感知层不是写死的规则——是 LLM 自己决定调用哪个 Skill 或 MCP 来解析外部输入。用户发一段 JD，LLM 看到 parse_jd 这个 Tool，自己去调。用户发 GitHub 链接，LLM 看到 github_repo 这个 Tool，自己去调。"

### 代码路径

```
入口（LLM 自主模式）：
  agents/autonomous_agent.py:56  AutonomousAgent.run()
    │
    ├── LLM 看到 System Prompt 里列了 16 个 Tool 的 name + description
    │     tools/registry.py:85-535  所有 Tool 的注册
    │
    └── LLM 决定调哪一个：

① 用户发了 JD 文本 → LLM 调 parse_jd
   tools/registry.py:85  ParseJDTool
     → agents/jd_parser.py:65  JDParserAgent.parse(job_description)
        ├── 先试 LLM 解析 → _llm_parse() → JSON → ParsedJD
        └── LLM 失败 → _rule_parse() → 正则 + 技能池匹配 → ParsedJD
        输出：ParsedJD {job_title="AI Agent 实习生", direction="agent",
                         hard_skills=["Python","RAG","LangGraph"...]}

② 用户上传了 PDF → LLM 调文件加载 skill
   rag/loaders/file_loader.py:22  FileLoader.load(path)
     → pypdf.PdfReader → page.extract_text() → 纯文本
     → service/knowledge_base.py:64  index_text(content)
        → rag/chunking/text_chunker.py:36  chunk_document()
           → clean_text() → _split_text() → _build_chunks()
           输出：list[DocumentChunk]（每个 800 字，重叠 100）
        → service/knowledge_base.py:274  _append_chunks(chunks)
           写入：runtime/knowledge_base/chunks.jsonl

③ 用户发了 GitHub 链接 → LLM 调 MCP github 或 github_repo skill
   tools/registry.py:449  GitHubRepoTool
     → service/knowledge_base.py:158  ingest_github_repo("yfn-1116/career-agent-assistant")
        → urllib: GET raw.githubusercontent.com/.../main/README.md
        → index_text(content) → chunk → JSONL
     或通过 MCP：
     infrastructure/mcp_client.py:28  MCPClient("github", "npx", [...])
       → subprocess: npx @modelcontextprotocol/server-github
       → JSON-RPC over stdio → list_tools() / call_tool()
```

### 关键设计点

- **为什么用 LLM 而不是写死规则？** 因为 LLM 能理解"帮我分析一下这个 JD"和"看看这个岗位适合我吗"是同一件事，不用维护关键词列表。
- **LLM 怎么知道有什么工具？** System Prompt 里列了 16 个 Tool 的 name + description。LLM 看到的和 OpenCode 的 system prompt 一样的格式。
- **处理完去哪了？** 全部进 Memory——chunks.jsonl（知识库）+ conversations.jsonl（对话记录）。

---

## ④ Planning 规划层（PPT 第5-6页）

**PPT 展示：** LLM 自主循环 + LangGraph 工作流

**你需要知道的完整代码路径：**

### 怎么讲

> "规划层是 LLM 自主决策的核心。LLM 看到 System Prompt 里列了 16 个 Tool，自己决定先调哪个、后调哪个。这和 OpenCode 的 agent loop 是完全一样的模式。当 LLM 不可用时，回退到 LangGraph 确定性 DAG。"

### 代码路径

```
自主模式（默认）：
  agents/autonomous_agent.py:56  AutonomousAgent.run()
    │
    ├── 构建 System Prompt（列出 16 个 Tool）
    │     _build_tool_prompt() → 遍历 ToolRegistry.list_tools()
    │     "可用工具列表：
    │      - parse_jd: 解析岗位 JD 文本...
    │      - retrieve_profile: 从知识库检索...
    │      - github_repo: 拉取 GitHub 仓库..."
    │
    ├── 循环（最多 10 步）：
    │     for step in range(max_steps):
    │       │
    │       ├── ① LLM 看历史对话 + 工具列表 → 返回 tool_call JSON 或最终答案
    │       │     llm.generate(prompt, system_prompt="")
    │       │
    │       ├── ② 解析 tool_call
    │       │     _parse_tool_call(raw_response)
    │       │     支持 3 种格式：纯 JSON / markdown代码块 / 嵌入式JSON
    │       │
    │       ├── ③ 如果 LLM 返回了 tool_call → 执行 → 追加结果 → 继续循环
    │       │     _execute_tool(name, inputs)
    │       │       → ToolRegistry.invoke(name, **inputs)
    │       │       → 返回 ToolResult → 追加到 messages
    │       │       → continue（LLM 可能还要调更多工具）
    │       │
    │       └── ④ 如果 LLM 返回了普通文本 → 最终答案 → break

    │
    └── 返回 AutonomousResult {answer, steps, total_steps}

回退模式（LLM 不可用时）：
  agents/orchestrator.py:88  _handle_ppam()
    ├── _perceive(text) → 关键词规则分类 → intent
    ├── _plan(intent) → 查字典 → execution plan
    └── _act(plan) → 调用对应函数
        │
        └── "langgraph_job_match" → 启动 LangGraph:
            workflows/langgraph_workflow.py:626  run_langgraph_workflow()
              │
              └── create_langgraph_workflow() → StateGraph
                  ├── parse_jd → rewrite_query → retrieve_context → rerank
                  ├── grade_retrieval → (score<0.65 → rewrite, retry≤2)
                  ├── analyze_match → build_output
                  └── check_faithfulness → write_report → END
```

### 关键设计点

- **LLM 怎么知道该调什么？** 它看到 System Prompt 里每个 Tool 的描述。比如 `parse_jd: "当用户粘贴招聘信息时触发"`——LLM 看到用户发了 JD，自己就会去调。
- **循环什么时候结束？** LLM 不输出 tool_call 了，而是输出一段普通文本 → 这就是最终答案。
- **安全和 OpenCode 一样吗？** max_steps=10 防止无限循环，每次 tool_call 都要匹配 ToolRegistry 里的名字。
- **为什么保留回退模式？** 如果没有 API Key 或网络断了，系统还能用规则模式跑。

---

## ⑤ Action 执行层（PPT 第7-9页）

**PPT 展示：** Skill + MCP + SubAgent + RAG Pipeline + Evidence Gate

**你需要知道的完整代码路径：**

### 怎么讲

> "执行层有三层扩展机制。第一层是内置 Skill——16 个 Python Tool 注册在 ToolRegistry 里。第二层是 MCP 外部服务——通过标准协议连接外部工具。第三层是 SubAgent 并行模式——LLM 可以 spawn 子 Agent 独立执行任务。"

### 5.1 Tool 注册与调用

```
tools/registry.py:14  ToolRegistry
  ├── register(tool)    → 注册（重名抛异常）
  ├── get(name)         → 获取（不存在抛 KeyError）
  ├── invoke(name, **kwargs) → 调用 + 计时 + 异常捕获
  └── create_standard_registry() → 注册全部 16 个 Tool

tools/base.py:32  Tool ABC
  ├── name: str              → 工具唯一名称
  ├── description: str       → "能做什么 + 何时触发"
  ├── run(**kwargs)          → 执行
  └── safety_notes: list[str] → 安全说明

16 个 Tool（tools/registry.py:85-535）：
  感知类：parse_jd, github_repo, web_search
  检索类：retrieve_profile, rerank_chunks, grade_retrieval, select_evidence
  分析类：analyze_match
  生成类：generate_grounded_answer
  验证类：check_faithfulness
  安全类：fallback
  工具类：write_report, write_diagnostics
  并行类：task_agent（新增）
  查询类：plan_queries, rewrite_query
```

### 5.2 MCP 外部服务

```
infrastructure/mcp_client.py:28  MCPClient
  ├── __init__(server_name, command, args, env)
  ├── start() → subprocess.Popen → JSON-RPC initialize → list_tools()
  ├── call_tool(name, arguments) → JSON-RPC → 返回文本
  └── stop() → process.terminate()

已配置的 MCP Server：
  GitHub MCP:
    create_github_mcp(token="ghp_xxx")
    → npx @modelcontextprotocol/server-github
    → 提供：search_repositories, get_file_contents, create_issue...

  resuml MCP:
    npx resuml mcp
    → 提供：init_resume, score_resume, tailor_resume, render_resume...
```

### 5.3 SubAgent 并行模式

```
agents/sub_agent.py:39  SubAgent
  ├── execute(task, allowed_tools) → SubAgentResult
  │     ├── 默认只读工具：[parse_jd, retrieve_profile, web_search, github_repo]
  │     ├── 独立上下文（看不到主 Agent 的中间步骤）
  │     ├── 自己的 LLM 循环（max_steps=8）
  │     └── 单次返回汇总结果
  │
  └── 参考：OpenCode agent-tool.go → AgentTask 模式

tools/registry.py:488  TaskAgentTool
  description: "启动子 Agent 执行独立任务，用于并行处理"
  → LLM 可以 spawn 子 Agent：
    tool_call: task_agent(
        task="搜索所有 Python 后端相关的 GitHub 项目",
        allowed_tools=["web_search", "github_repo"]
    )
```

### 5.4 RAG Pipeline（贯穿层核心）

```
完整的检索链路（一条 tool_call 的内部）：

用户问："Agent 开发实习生 要求 Python RAG LangGraph"

① jieba 分词
   "Agent 开发实习生 要求 Python RAG LangGraph"
   → ["Agent", "开发", "实习生", "要求", "Python", "RAG", "LangGraph"]

② BM25 关键词检索
   rag/retrievers/bm25_retriever.py:42  BM25Retriever.search(query, top_k=80)
   → jieba 分词 + rank_bm25.get_scores()
   → BM25 公式: score = Σ IDF(qi)×TF(qi,doc)×(k1+1)/(TF+k1×(1-b+b×len/avg))
   → 输出：top 80 chunks（按 BM25 得分排序）

③ Qwen Embedding 语义检索
   rag/embeddings/qwen_embedding.py:38  QwenEmbeddingProvider.embed_text(query)
   → DashScope API: text-embedding-v3, 1024 维
   → cosine_similarity(query_vec, chunk_vecs)
   → 输出：top 80 chunks（按 cosine 相似度排序）

④ RRF 融合
   rag/retrievers/rrf_fusion.py:15  reciprocal_rank_fusion(list1, list2, k=60)
   → RRF_score(chunk) = 1/(60+rank_bm25) + 1/(60+rank_emb)
   → 零参数，不需要调权重
   → 输出：top 30 chunks

⑤ CrossEncoder 精排
   rag/reranker/cross_encoder_reranker.py:63  CrossEncoderReranker.rerank(query, chunks, top_n=5)
   → bge-reranker-base (279M 参数, 12层 Transformer)
   → 把 query 和 chunk 拼成一对：[CLS] query [SEP] chunk [SEP]
   → 整对送进 Transformer，Cross-Attention 让每个 token 互看
   → 输出：top 5 chunks（按 CrossEncoder 得分排序）

⑥ FaithfulnessChecker
   evaluation/faithfulness.py:153  FaithfulnessChecker.check(bullets, evidences)
   → 验证每个声称有证据支撑
   → 检测夸大措辞："完整实现""大规模部署"
   → 通过阈值：0.75

⑦ EvidenceGate
   evidence/gate.py:46  EvidenceGate.validate(claim, status)
   → implemented → ✅ 可直接写入简历
   → designed    → ⚠️ 需降级措辞
   → planned     → ❌ 阻止生成

⑧ LLM 生成
   Qwen-Plus / DeepSeek → 基于 top 5 evidence + System Prompt
   → BuildAgent 四阶段分级：can_write / needs_confirmation / learning_plan
```

### 关键设计点

- **BM25 和 Embedding 为什么两个都要？** BM25 精确匹配技能名（不会漏掉"LangGraph"），Embedding 理解语义（"写代码"≈"编程"）。两者互补，RRF 零参数融合。
- **为什么加 CrossEncoder？** Embedding 是 Bi-Encoder，query 和 chunk 各自编码再点乘——信息交互不够。CrossEncoder 把两者拼在一起编码——能看到细节关系，准确率高 10-15%。
- **Evidence Gate 为什么是独有创新？** 业界的 RAG 只检查"有没有证据"，我们多一步——检查"证据的质量等级"。planned 的经历不会被写进简历。

---

## ⑥ Memory 记忆层（PPT 第10页）

**PPT 展示：** 三层记忆表格

**你需要知道的完整代码路径：**

### 怎么讲

> "记忆层分三层。短时记忆存当前对话，给 LLM 做上下文。长时记忆存所有历史对话，用 BM25 检索回忆。知识库存用户上传的全部资料，用完整 RAG Pipeline 检索。"

### 代码路径

```
短时记忆：
  agents/memory.py:54  ConversationMemory.remember(role, content)
    → self._short_term.append(entry)           # 内存列表
    → if len > 20: truncate                    # 保留最近 20 条
    → self._persist(entry)                     # 写 JSONL

  agents/memory.py:69  get_context(n=10)
    → self._short_term[-n:]                    # 最近 n 条 → LLM 上下文

  agents/memory.py:73  context_text(n=10)
    → "[用户]: ... [助手]: ..."                # 格式化为 LLM prompt

长时记忆：
  agents/memory.py:86  recall(query, top_k=3)
    → _iter_history()                          # 读 conversations.jsonl
    → BM25Retriever.search(query, top_k)       # BM25 检索历史
    → 返回相关对话条目

知识库：
  service/knowledge_base.py:48  KnowledgeBaseService
    ├── ingest_upload(filename, data)  → PDF/DOCX → chunk → JSONL
    ├── ingest_github_repo(repo)       → README → chunk → JSONL
    ├── search(query, top_k)           → BM25Retriever (deduplicated, scored)
    └── get_summary()                  → {chunk_count, source_count, repo_count}
```

### 关键设计点

- **为什么用 JSONL 而不是数据库？** 学生项目不需要引入外部依赖。JSONL 追加写、逐行读，简洁透明。
- **长时记忆怎么查？** 和知识库检索一样——用 BM25。历史对话也是文本，也可以用关键词匹配。
- **和知识库有什么区别？** 知识库存的是用户上传的简历/项目资料（chunks.jsonl），长时记忆存的是对话记录（conversations.jsonl）。检索方式相同，数据来源不同。

---

## ⑩ 多 Agent 递归树（PPT 第10-11页）

**PPT 展示：** 树状递归图

**怎么讲：**

> "多 Agent 协作是一个树状递归结构。Agent 本身被注册为 task_agent 这个 Tool，所以父 Agent 能 spawn 子 Agent。子 Agent 也有独立的 System Prompt（角色不同）、受限的 Tool 白名单（权限不同）、通过 task 字符串传递任务。关键是子 Agent 也能调 task_agent——这就形成了递归。执行栈和函数调用栈一模一样：主 Agent 调子 Agent，子 Agent 调孙子 Agent，结果一层层传回来。"

**代码路径：**

```
主 Agent:
  agents/orchestrator.py:70 → _handle_autonomous()
    → agents/autonomous_agent.py:67 → AutonomousAgent.run()
        │
        │ LLM 看到 task_agent 这个 Tool:
        │   tools/registry.py:488  TaskAgentTool
        │   description: "启动子 Agent 执行独立任务..."
        │
        │ LLM 决定 spawn → 输出:
        │   {"tool_call": {"name": "task_agent", "input": {
        │     "task": "分析 JD_1",
        │     "allowed_tools": ["parse_jd", "retrieve_profile", "analyze_match"]
        │   }}}
        │
        ▼
子 Agent:
  tools/registry.py:488 → TaskAgentTool.run(task="分析 JD_1", allowed_tools=[...])
    → agents/sub_agent.py:39 → SubAgent.execute(task, allowed_tools)
        │
        │ 创建独立 System Prompt (sub_agent.py:79):
        │   "你是子任务执行 Agent。只做任务描述里要求的事情..."
        │
        │ 独立 session, 独立 LLM 循环 (max_steps=8)
        │
        │ 子 Agent 自己也能看到 task_agent → 能 spawn 孙子 Agent
        │
        └── 返回 SubAgentResult {answer: "匹配度 74%", tools_called: [...]}

结果回传主 Agent → 主 Agent 继续决策 → 最终整合输出
```

**递归本质：**

```
执行栈：
  main_agent(深度1)
    ├── sub_agent_B(深度2)
    │     ├── parse_jd
    │     ├── retrieve
    │     └── 返回结果
    │
    ├── sub_agent_C(深度2)
    │     ├── sub_sub_agent(深度3)  ← 子 Agent 也能 spawn!
    │     │     ├── web_search
    │     │     └── 返回结果
    │     └── 返回结果
    │
    └── 整合 → 返回用户

每个 Agent 都有 task_agent → 每层都能递归
和函数调用完全一样：父调子、子调孙、层层返回
```

**三个要素的代码：**

```
① 角色 = 不同的 System Prompt
   sub_agent.py:79-97
   "你是子任务执行 Agent。你的主 Agent 分配了一个任务给你。"

② 权限 = allowed_tools 白名单
   sub_agent.py:53-57
   default_tools = ["parse_jd","retrieve_profile","web_search","github_repo"]

③ 通信 = task 字符串 + SubAgentResult
   父 → 子：task="详细任务描述"
   子 → 父：SubAgentResult {answer, tools_called, success}
```

---

## ⑪ 对比 OpenCode（PPT 第12页）

**PPT 展示：** 对比表格

### 怎么讲

> "我参考了 OpenCode 的架构——Tool 注册、LLM 自主循环、Agent-as-Tool、MCP 扩展——这些我们都有。但在求职这个垂直场景上，我做了两个 OpenCode 没有的东西：工业级 RAG Pipeline 和 Evidence Gate 证据约束。OpenCode 用 Sourcegraph 做代码搜索，我们自己做了一套 BM25+Embedding+RRF+CrossEncoder 的检索系统。OpenCode 不做幻觉过滤，我们用 Evidence Gate 四阶段分级保证不编造经历。"

### 关键数据

```
OpenCode 的 Agent 循环：agent.go:233-311  processGeneration()
  你的 Agent 循环：   autonomous_agent.py:56  AutonomousAgent.run()
  同模式，不同语言。

OpenCode 的 Tool 接口：tools.go:69  BaseTool {Info(), Run()}
  你的 Tool 接口：     tools/base.py:32  Tool {name, description, run()}
  同接口。

OpenCode 的子 Agent：agent-tool.go:29  TaskAgentTools = [Glob, Grep, LS, View]
  你的子 Agent：      sub_agent.py:39  SubAgent(default_tools=[parse_jd, retrieve,...])
  同模式。
```

---

## ⑧ 测试与部署（PPT 第12页）

**关键数据：**

```
693 passed, 0 failed
模型：3 本地（jieba, BM25, bge-reranker-base 1.1GB）+ 2 API（Qwen, DeepSeek）+ 2 MCP
部署：docker compose up -d → FastAPI:8000 + Streamlit:8501
```

---

> 此文档配合 `defense_technical_deep_dive.md`（PPT 素材）使用
> 每个章节对着 PPT 页面阅读对应的代码路径
