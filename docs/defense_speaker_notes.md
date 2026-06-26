# 答辩演讲备注 / Speaker Notes

> 此文档对着 PPT 逐页使用。包含 PPT 上不展示但你需要知道的全部技术细节。

---

## 第一章：项目定位

### PPT 说：是什么 / 不是什么

**你需要知道的补充：**

- 产品架构定义在 `docs/architecture/internship_copilot_product_architecture.md`
- 核心原则就一句话：**Evidence-Grounded**——所有生成内容必须能从知识库找到证据
- Human-in-the-loop：ApprovalGate 拦截 6 类动作（`send_greeting`, `send_hr_reply`, `send_resume`, `mark_message_sent`, `mark_resume_sent`, `browser_click_send`）
- 代码位置：`src/career_agent/approval/gate.py:11-14`

### PPT 说：用户旅程

**代码对应：**

```
上传资料 → KnowledgeBaseService.ingest_upload()
            service/knowledge_base.py:78
粘贴 JD  → _route_intent() 识别意图
            demo/streamlit/app.py:69-85
匹配分析 → AgentRunService.analyze_job()
            service/agent_run.py:101-119
生成话术 → MessageAgent.generate()
            messages/agent.py:29-67
保存记录 → ApplicationService.save_from_agent_result()
            service/application_service.py:21-46
```

---

## 第二章：需求分析

### PPT 说：用户痛点

**每一个痛点对应的实际模块：**

| 痛点 | 对应模块 | 文件 |
|---|---|---|
| 不确定是否匹配 | `JobMatchScorer` | `matching/scorer.py:47` |
| 不敢乱写经历 | `EvidenceGate` + `BuildAgent` | `evidence/gate.py:46` · `agents/build_agent.py:240` |
| 不知道怎么聊 | `MessageAgent` + `HRReplyAssistant` | `messages/agent.py` · `conversation/reply.py` |
| 记不住投递 | `ApplicationRepository` (JSONL) | `applications/repository.py:55` |

### PPT 说：非目标

**为什么这些明确不做：**

- 不自动投递：法律风险，且平台会封号
- 不爬取网站：同上，反爬机制
- 不多用户：MVP 阶段不引入认证系统
- 代码体现：`approval/gate.py` 的 `ACTIONS_REQUIRING_APPROVAL` 列表

---

## 第三章：系统架构

### PPT 展示：六层架构图

**每层的实际目录和关键文件：**

```
interface/     demo/streamlit/app.py                  ← Streamlit UI
               demo/streamlit/ui_components.py         ← 组件渲染
               demo/streamlit/styles.py                ← DeepSeek 风格 CSS
               src/career_agent/api/app.py             ← FastAPI 入口
               src/career_agent/api/routes/*.py        ← 6 个路由

service/       src/career_agent/service/agent_run.py           ← 统一调度
               src/career_agent/service/knowledge_base.py      ← 知识库
               src/career_agent/service/application_service.py ← 投递记录
               src/career_agent/service/browser_service.py     ← 浏览器辅助

workflow/      src/career_agent/workflows/langgraph_workflow.py ← 核心编排
               src/career_agent/workflows/job_match_workflow.py ← 简单版

agent/         src/career_agent/agents/jd_parser.py            ← JD 解析
               src/career_agent/agents/rag_retrieve_agent.py   ← 检索查询
               src/career_agent/agents/match_analysis_agent.py ← 匹配分析
               src/career_agent/agents/build_agent.py          ← 输出生成
               src/career_agent/agents/state.py                ← 共享状态

rag/           src/career_agent/rag/loaders/*.py       ← 文档加载
               src/career_agent/rag/chunking/          ← 分块
               src/career_agent/rag/retrievers/        ← 检索器
               src/career_agent/rag/reranker/          ← 精排
               src/career_agent/rag/grading.py         ← 检索评分
               src/career_agent/rag/embeddings/        ← Embedding

domain/        src/career_agent/domain/schemas.py      ← 11 个数据模型
               src/career_agent/domain/validation.py   ← 分数校验
```

### PPT 说：依赖方向

**为什么这样设计：**

- domain 层在最底层，零依赖——任何层都可以安全引用
- interface 只能调用 service，不碰 agent/rag 内部
- 这种分层确保换任何一个层（比如把 MemoryVectorStore 换成 Chroma）不影响上层
- 实际上有两条检索路径：`_run_chat` 走 KnowledgeBaseService，`_run_analysis` 走 LangGraph Workflow

---

## 第四章：核心流程（JD → 输出）

### 4.1 完整数据流：每一步的实际函数

```
Step 1: JD 解析
  函数: JDParserAgent.parse(job_description)
  文件: agents/jd_parser.py:65
  输入: "AI Agent 实习生\n要求 Python、RAG、LangGraph..."
  输出: ParsedJD {job_title="AI Agent 开发实习生", job_direction="agent",
                  hard_skills=["Python","LangGraph","RAG"...], keywords=[...]}
  逻辑: 先用正则匹配技能池（33 个硬技能词），失败时可选 LLM 解析
        方向判定: 统计 agent/rag/backend/ai_application 四类关键词出现次数

Step 2: 查询构建
  函数: RAGRetrieveAgent.build_query_from_parsed_jd(parsed_jd)
  文件: agents/rag_retrieve_agent.py:24
  逻辑: job_direction + hard_skills[:8] + bonus_skills[:5] + keywords[:10]
        拼接成空格分隔的查询字符串

Step 3: 双路检索
  BM25 路:
    BM25Retriever.search(query, top_k=80)
    文件: rag/retrievers/bm25_retriever.py:42
    实现: jieba 分词 → rank_bm25.get_scores() → 排序取 top 80
          BM25 公式: score = Σ IDF(qi) × TF(qi,chunk) × (k1+1) / (TF+...)
          听不懂可以只说"基于词频和逆文档频率的关键词检索"

  Embedding 路:
    QwenEmbeddingProvider.embed_text(query) → cosine similarity
    文件: rag/embeddings/qwen_embedding.py:38

Step 4: RRF 融合
  函数: reciprocal_rank_fusion(bm25_results, emb_results, k=60)
  文件: rag/retrievers/rrf_fusion.py:15
  公式: RRF_score(chunk) = 1/(60+rank_bm25) + 1/(60+rank_emb)
  为什么 k=60: 论文中经过大量实验验证，60 是通用性最好的常数

Step 5: Cross-Encoder 精排
  函数: CrossEncoderReranker.rerank(query, chunks, top_n=5)
  文件: rag/reranker/cross_encoder_reranker.py:63
  模型: BAAI/bge-reranker-base (279M 参数, 12 层 Transformer)
  实现: 把 (query, chunk) 拼成 "[CLS] query [SEP] chunk [SEP]"
        整对送进 Transformer → 输出单一 relevance score
        比 embedding 点乘准 10-15%，因为能看到 query 和 chunk 的交叉注意力

Step 6: 匹配分析
  函数: MatchAnalysisAgent.analyze(parsed_jd, evidence)
  文件: agents/match_analysis_agent.py:24
  输出: MatchAnalysisResult {strengths, weaknesses, matched_keywords, suggestions}

Step 7: 输出生成
  函数: BuildAgent.build(parsed_jd, evidence, analysis)
  文件: agents/build_agent.py:47
  核心: _build_constraint_metadata() 对每个 bullet 分类
        → can_write_claims / needs_confirmation_claims / learning_plan_claims

Step 8: 真实性检查
  函数: FaithfulnessChecker.check(bullets, evidences)
  文件: evaluation/faithfulness.py:153
  阈值: 0.75 (低于此分 → revise_required)
```

### 4.2 检索 Pipeline 详解

**答辩时可说的技术亮点：**

1. **为什么双路召回？** BM25 擅长精确匹配（"LangGraph" 一词不漏），Embedding 擅长语义匹配（"写代码"≈"开发"）。两者互补是 RAG 社区共识
2. **为什么用 RRF 而不是加权求和？** RRF 不需要调权重（零超参数），排名的分布差异（BM25 分数范围可能是 [0,20]，Embedding 是 [0,1]）不影响融合结果——这是 SIGIR 2009 论文的核心贡献
3. **为什么加 Reranker？** Embedding 是 Bi-Encoder，query 和 chunk 各自编码后再点乘——两者之间没有交互。Cross-Encoder 把 query 和 chunk 拼在一起编码——Transformer 的 self-attention 让 query 和 chunk 的每个 token 都能看到对方，准确率提升显著
4. **我们做了什么独创性工作？** Evidence Gate 四阶段分级（implemented/designed/planned/无证据）——业界 RAG 通常只检查"有没有证据"，我们进一步区分了证据的质量等级

### 4.3 Chunker 详解

```
TextChunker.chunk_document(doc)
  │  rag/chunking/text_chunker.py:36
  │
  ├─ clean_text(content)
  │   去首尾空白 → 统一换行符 \n → 压缩 3+ 空行为 2
  │   保留 Markdown 结构（# 标题、- 列表）
  │
  ├─ _split_text(cleaned)
  │   参数: chunk_size=800, overlap=100
  │   step = 800 - 100 = 700
  │   while start < len(text):
  │       chunk = text[start : start+800]
  │       start += 700
  │
  └─ _build_chunks(doc, segments)
       每个 segment → DocumentChunk
       chunk_id = "{document_id}_{序号}"
       继承父文档的 metadata
```

**如果老师问"为什么不用模型做 chunking"：**
- Chunking 目标是找自然语义边界（段落、句子）
- 业界做法是用规则找这些边界（`\n\n` → `\n` → `。` → `.`），不需要 ML
- 当前用固定窗口是 MVP 版本，改进方向是 `RecursiveCharacterTextSplitter`
- 真正需要模型的是检索和精排（BM25、Embedding、Reranker），这些我们都已经用了

---

## 第五章：技术选型

### 5.1 每个模型的具体选择理由

**jieba (分词):**
- 文件: `rag/retrievers/bm25_retriever.py:12`
- 为什么不是 HanLP/LAC: jieba 最轻量（词库 ~50MB），pip install 即用，中文分词准确率 95%+
- 为什么不过度依赖分词: BM25 即使分词不太准也能工作，后续还有 Reranker 兜底

**BM25 (关键词检索):**
- 文件: `rag/retrievers/bm25_retriever.py`
- 为什么不是 TF-IDF: BM25 是 TF-IDF 的改进版，多了文档长度归一化（参数 b=0.75）和词频饱和曲线（参数 k1=1.5），短文档不会被严重惩罚
- 为什么不是 ElasticSearch: 太重，不适合 pip install

**Qwen text-embedding-v3 (语义检索):**
- 文件: `rag/embeddings/qwen_embedding.py`
- 为什么不是 bge-m3 本地: bge-m3 568M 参数，CPU 推理 200ms/条。API 调用 50ms，且已有 Key
- 维度: 1024

**bge-reranker-base (精排):**
- 文件: `rag/reranker/cross_encoder_reranker.py`
- 为什么是 base 不是 v2-m3: base 279M 参数 vs v2-m3 568M。CPU 推理 base ~10ms/对，v2-m3 ~30ms/对。精排 30 个候选 → 300ms vs 900ms。准确率差异 <5%
- 为什么不是规则: 规则 Reranker (LightweightReranker) 只看技能词重叠，不理解语义。"React 前端开发"和"Python 后端"在规则看来都有"开发"，都会给高分。Cross-Encoder 读完整句子后能判断不相关

### 5.2 两种模式切换

```
轻量模式（默认）:
  BM25Retriever + LightweightReranker + 模板生成
  启动: 不设 API Key 即可

完整模式:
  BM25 + Qwen Embedding + RRF + Cross-Encoder + Qwen LLM
  启动: 设置 QWEN_API_KEY + 下载 bge-reranker-base 模型
```

代码体现：
- `src/career_agent/workflows/langgraph_workflow.py:598-619`
- 检测 `Settings.embedding.api_key` 是否存在来决定是否启用 Hybrid 模式

---

## 第六章：关键模块实现

### 6.1 PDF 数据摄入

```
完整调用链（每一步的文件+行号+函数名）：

1. 浏览器上传 → streamlit file_uploader
   demo/streamlit/app.py:225-229

2. KnowledgeBaseService.ingest_upload(filename, data: bytes)
   service/knowledge_base.py:78-88
   → saved_path.write_bytes(data)  # 保存到 runtime/uploads/

3. FileLoader.load(saved_path) → ProfileDocument
   rag/loaders/file_loader.py:22-51
   → .pdf  → _read_pdf()  (pypdf.PdfReader, 逐页 extract_text)
   → .docx → _read_docx() (python-docx, 逐段提取)
   → .md   → path.read_text()

4. KnowledgeBaseService.index_text(content, source_name)
   service/knowledge_base.py:64-76
   → 包装为 ProfileDocument
   → TextChunker.chunk_document(doc) → list[DocumentChunk]

5. TextChunker 分块
   rag/chunking/text_chunker.py:36-110
   → clean_text() → _split_text() → _build_chunks()

6. _append_chunks(chunks) → JSONL 持久化
   service/knowledge_base.py:274-284
   → open("chunks.jsonl", "a") → json.dumps() → write

7. 检索时重建索引
   service/knowledge_base.py:90-101
   → load_store() → MemoryVectorStore().add_chunks()
   → store.search(query, top_k)
```

### 6.2 LangGraph 工作流

```
StateGraph 定义:
  langgraph_workflow.py:562-591

节点: 10 个 (parse_jd, rewrite_query, retrieve_context, rerank,
              grade_retrieval, analyze_match, build_output,
              check_faithfulness, write_report, fallback)

边: 9 条普通边 + 1 条条件边

条件路由 (_route_after_grading, 第 371 行):
  score ≥ 0.65 → analyze_match
  score < 0.65 且 retry < 2 → rewrite_query
  retry ≥ 2 且 score < 0.65 → fallback

状态: JobMatchState (TypedDict, 30 个字段, 第 49 行)

重试机制:
  - 每次检索后 grade_retrieval 评分
  - 评分低 → 提取 missing_keywords → 重写 query → 重新检索
  - 最多 2 次重试 → 仍不达标 → fallback（诚实告知）

工具调用追踪:
  _record_tool_call() 记录每个工具的名称、输入摘要、输出摘要、耗时(ms)
  最终写入 diagnostics JSON
```

### 6.3 Evidence Gate（你答辩时重点讲这个）

**四阶段的代码位置：**

```python
# 状态常量
STATUS_IMPLEMENTED = "implemented"  # 可直接写入简历
STATUS_DESIGNED    = "designed"     # 需用户确认
STATUS_PLANNED     = "planned"      # 仅学习方向
STATUS_UNCERTAIN   = "uncertain"    # 拒绝使用

# EvidenceGate 验证单个声称 (evidence/gate.py:46-84)
gate.validate(claim="实现了完整的 RAG pipeline", evidence_status="planned")
→ EvidenceResult(allowed=False, blocked_reason="planned 不能声称已完成")

# BuildAgent 批量约束 (agents/build_agent.py:240-278)
_build_constraint_metadata(evidence, resume_bullets)
→ {
    "can_write_claims": ["参与 RAG 项目..."],          # implemented
    "needs_confirmation_claims": ["设计了 MCP 方案..."], # designed
    "learning_plan_claims": ["计划补强 K8s..."],        # planned
    "warnings": ["evidence xxx 状态为 planned, 不能直接写入简历"]
}
```

**为什么这个重要：**
- 业界 RAG 只检查"有没有检索到证据"
- 我们多了一步：检查"证据的质量等级"
- 例如你设计了一个方案但没实现——系统不会让它写进简历
- 这是本项目的**核心独创性**

---

## 第七章：开发过程

### 7.1 整体推进

```
Week 1-2: 项目定位 + 需求分析
  → docs/architecture/internship_copilot_product_architecture.md
  → 确定: Agentic RAG, Evidence-Grounded, Human-in-the-loop

Week 3-4: 模块设计 + 技术选型
  → docs/architecture/industrial_agentic_rag.md
  → 五层分层架构, Domain Schema 标准化

Week 5-8: Vibe Coding 实现
  → Phase 1: 规则 Agent + 纯 token 检索 + CLI Demo
  → Phase 2: LLM 增强 + Embedding + LangGraph + Streamlit
  → Phase 3: BM25 + RRF + Cross-Encoder Reranker

Week 9-10: 测试 + 文档
  → 663 个测试全部通过
  → 答辩文档 + Speaker Notes
```

### 7.2 项目规模

```
源代码: 85 个 .py 文件
测试:   60 个 test_*.py 文件, 663 个测试用例
文档:   10+ 个 Markdown 文档
模型:   3 本地 (jieba, BM25, bge-reranker-base) + 3 API (Qwen Embedding, Qwen LLM, DeepSeek)
工具:   15 个标准化 Tool (ToolRegistry)
```

### 7.3 测试分布

| 层 | 测试数 | 说明 |
|---|---|---|
| Unit (agents/rag/domain/matching) | ~550 | 函数/Schema/Gate/公式 |
| Evals (业务场景) | ~52 | JD 匹配方向/状态约束/分数校准 |
| E2E (端到端) | ~18 | 8 种 JD 全链路不崩溃 |
| 新增检索模块 | ~23 | BM25/RRF/Cross-Encoder |
| **总计** | **663** | |

运行命令: `PYTHONPATH=src:$PWD pytest tests/ -q`

---

## 第八章：答辩问答补充

### Q1 追问："证据约束"怎么实现的？

答：(1) `ProfileLoader` 根据文档内容推断 status（见 `profile/loader.py:73-95`）
- 文件含"实现/完成/部署"关键词 → implemented
- 文件含"设计/架构/方案"关键词 → designed
- 文件含"计划/TODO/FIXME"关键词 → planned

(2) `EvidenceGate.validate()` 根据 status 检查措辞合法性
- planned 证据声称"实现了"→ blocked

(3) `FaithfulnessChecker.check()` 验证所有 bullet 有证据引用
- 没有 evidence_ids → unsupported → revise_required

### Q2 追问：BM25 具体怎么算的？

答：BM25 公式涉及三个因子：
- **TF（词频）**：这个词在文档中出现多次 → 得分高（但有饱和曲线，出现 100 次≈出现 20 次）
- **IDF（逆文档频率）**：少见词权重高（"LangGraph"比"Python"重要）
- **文档长度归一化**：短文档不被惩罚（参数 b=0.75）

（回答到这层次就够了，老师不太会让现场推导公式）

### Q3 追问：bge-reranker-base 和 Embedding 的区别？

答：两者都用 Transformer，但用法不同：
- **Embedding (Bi-Encoder)**：query 和 chunk 各自独立编码成向量，用 cosine 算相似度——快但粗糙，看不出细节关系
- **Reranker (Cross-Encoder)**：把 query 和 chunk 拼成一对，整对送进 Transformer——慢但准，能看到 query 中每个词和 chunk 中每个词的交互

### Q4 追问：RRF 为什么 k=60？

答：Cormack 等人在 SIGIR 2009 论文中经过大量实验验证，k=60 对各种场景和数据集都有稳定的融合效果。k 越大排名差异越平坦（top 1 和 top 10 区别变小），k 越小排名差异越陡（top 1 权重极高）。60 是平衡点。

### Q5 追问：如果 Embedding API 挂了怎么办？

答：系统有完整的降级策略。代码在 `langgraph_workflow.py:598-619`：
```python
if Settings.embedding.api_key:
    # 启用 BM25 + Embedding + RRF + Cross-Encoder 完整模式
else:
    # 降级为 BM25 + 规则 Reranker 轻量模式
    # 生成也可降级为规则模板，不依赖 LLM API
```
即使所有 API 都不可用，系统仍能运行——只是准确率会降低。

---

## 第九章：Agent 设计 — OpenCode 源码对比分析

> 本项目的 Agent 设计参考了 OpenCode (github.com/opencode-ai/opencode) 的架构。

### 9.1 OpenCode Agent 架构

OpenCode 是一个 Go 语言实现的 AI 编码助手，Agent 架构核心在 `internal/llm/agent/agent.go`。

**核心架构：**

```
用户输入
    │
    ▼
┌──────────────────────────────────────────────┐
│              Agent.processGeneration()        │
│                                              │
│  ① 创建 UserMessage                          │
│  ② 追加到 msgHistory                         │
│                                              │
│  ┌─── loop ───────────────────────────────┐  │
│  │                                         │  │
│  │  ③ provider.StreamResponse(history, tools)│
│  │     LLM 流式返回                          │
│  │       ↓                                  │
│  │  ④ AssistantMsg 可能包含 ToolCalls        │
│  │       ↓                                  │
│  │  ⑤ 遍历 ToolCalls, 匹配 tool by name     │
│  │       ↓                                  │
│  │  ⑥ tool.Run(ctx, ToolCall)               │
│  │       ↓                                  │
│  │  ⑦ ToolResult 作为 UserMessage 追加      │
│  │       ↓                                  │
│  │  ⑧ 如果 FinishReason == ToolUse          │
│  │     → continue loop                      │
│  │     否则 → 返回最终结果                    │
│  └──────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

**关键代码路径：**

1. `agent.go:198-231 Run()` — 入口，创建 goroutine 异步执行
2. `agent.go:233-311 processGeneration()` — **核心循环**：LLM → tool calls → 追加结果 → 继续
3. `agent.go:322-438 streamAndHandleEvents()` — 流式接收 LLM 事件，执行工具调用
4. `tools.go:69-72 BaseTool` — 工具接口：`Info() ToolInfo` + `Run(ctx, ToolCall) ToolResponse`
5. `agent-tool.go:29-41` — **Agent 本身也是一个 Tool**——可以递归调用子 Agent

**工具定义（tools/）：**
- `bash.go` — 执行 shell 命令
- `edit.go` — 编辑文件
- `write.go` — 写入文件
- `view.go` — 读取文件
- `grep.go` — 搜索文本
- `glob.go` — 搜索文件
- `ls.go` — 列出目录
- `fetch.go` — HTTP 请求
- `sourcegraph.go` — 代码图搜索
- `agent-tool.go` — **递归 Agent（Agent 调用 Agent）**

### 9.2 本项目 Agent 架构（参考 OpenCode 改造后）

```
用户输入 (JD 文本)
    │
    ▼
┌──────────────────────────────────────────────┐
│         LangGraph StateGraph                 │
│         (workflows/langgraph_workflow.py)     │
│                                              │
│  parse_jd ──→ rewrite_query ──→ retrieve     │
│       ↑                           │            │
│       │    (retry ≤ 2)    ┌───────┘            │
│       │                   ▼                    │
│       └───── grade_retrieval ──→ rerank       │
│                   │                            │
│                   ▼ (score ≥ 0.65)            │
│            analyze_match ──→ build_output     │
│                                  │            │
│                                  ▼            │
│                          check_faithfulness   │
│                                  │            │
│                                  ▼            │
│                            write_report      │
└──────────────────────────────────────────────┘
```

**关键代码路径：**

1. `langgraph_workflow.py:562-591 create_langgraph_workflow()` — 创建 StateGraph，注册 10 个节点
2. `langgraph_workflow.py:117-125 parse_jd_node()` — JD 解析节点
3. `langgraph_workflow.py:151-193 retrieve_context_node()` — 检索节点（BM25 + Embedding）
4. `langgraph_workflow.py:196-257 rerank_node()` — 精排节点（CrossEncoder / Lightweight）
5. `langgraph_workflow.py:276-283 analyze_match_node()` — 匹配分析
6. `langgraph_workflow.py:285-291 build_output_node()` — 输出生成
7. `langgraph_workflow.py:293-334 check_faithfulness_node()` — 真实性检查
8. `tools/registry.py:14-52 ToolRegistry` — 15 个标准化 Tool 的注册中心
9. `tools/planner.py:22-114 ControlledPlanner` — 规则驱动的工具选择器

### 9.3 核心差异对比

| 维度 | OpenCode | 本项目 |
|---|---|---|
| **语言** | Go | Python |
| **编排方式** | LLM 自主决策下一个 Tool | LangGraph StateGraph 确定性 DAG |
| **循环机制** | `for { LLM → tool calls → append → continue }` | `grade_retrieval` 条件边 → `rewrite_query` 重试 |
| **工具调用** | LLM 根据 system prompt 自主选择工具 | `ControlledPlanner.decide(state)` 规则驱动 |
| **重试策略** | 无显式重试（LLM 自己决定是否重试） | 最多 2 次自动重试，不达标进入 fallback |
| **Agent 递归** | ✅ `agentTool` 可以 spawn 子 Agent | ❌ 无（单层 10 节点 DAG） |
| **工具数量** | 10 个（bash/edit/write/view/...) | 15 个（parse_jd/retrieve/rerank/grade/...) |
| **事件驱动** | pub/sub Broker 异步事件流 | LangGraph StateGraph 同步节点执行 |
| **失败处理** | LLM 自主判断，cancel 信号 | ControlledPlanner 规则 + Evidence Gate |
| **证据约束** | ❌ 无 | ✅ FaithfulnessChecker + EvidenceGate 四阶段 |

### 9.4 为什么本项目选择 LangGraph 而非 LLM 自主决策

| | LLM 自主决策 (OpenCode 风格) | LangGraph DAG (本项目) |
|---|---|---|
| **可控性** | 低 — LLM 可能跳过关键步骤 | 高 — 每个节点必然执行 |
| **可解释性** | 低 — 不知道 LLM "为什么"调用某个工具 | 高 — 状态图的边就是解释 |
| **成本** | 高 — 每个决策都是一次 LLM 调用 | 低 — 规则 Planner 零 API 调用 |
| **适合场景** | 开放式任务（代码编辑、文件操作） | 结构化任务（JD 分析流程固定） |

**核心原因：** 求职投递场景的流程是固定的——解析 JD → 检索 → 匹配分析 → 生成输出。这不需要 LLM 的"创造力"来决策下一步做什么。用 DAG 比 LLM 自主决策更可靠、更快、更便宜。

**但如果要加开放功能（如"帮我分析一下这个岗位适合我吗"），OpenCode 的自主循环模式就比固定 DAG 更灵活。** 这是 Phase 3 的演进方向——在确定性 Pipeline 之外增加 LLM 自主工具调用。

---

> 配合 PPT 使用：每个 PPT 章节对着阅读对应的 Speaker Notes 章节
