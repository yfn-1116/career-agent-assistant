# 基于证据约束的智能实习投递 Agent

> 毕业答辩文档 · Career Agent Assistant

---

## 一、项目定位

### 1.1 一句话概括

**一个"不能说谎"的求职助手：所有生成内容必须能从你的真实经历中找到证据。**

### 1.2 是什么 / 不是什么

| 是 | 不是 |
|---|---|
| 基于个人知识库的求职匹配分析 | 简历生成器（自动编造经历） |
| 所有声称有据可查（Evidence-Grounded） | 自动投递机器人 |
| Human-in-the-loop：用户确认后才发送 | GPT 包装壳 |
| 长期维护的个人资料库 | 一次性 JD 分析工具 |

### 1.3 核心用户旅程

```
上传资料 ──→ 发现岗位 ──→ 匹配分析 ──→ 生成话术/简历 ──→ 用户确认 ──→ 投递
   │                                                          │
   └──────────── 持续积累个人知识库 ←──────────────────────────┘
```

---

## 二、需求分析

### 2.1 用户痛点

| 痛点 | 现有方案 | 我们的方案 |
|---|---|---|
| 投递前不确定自己是否匹配 | 人工逐条看 JD | 自动解析 JD → 匹配技能 → 输出匹配度 |
| 简历不敢乱写经历 | 要么抄模板、要么瞎编 | 只从知识库中检索真实经历，区分"实现了/设计了/计划中" |
| 和 HR 不知道怎么聊 | 百度搜模板 | 基于匹配结果生成个性化话术 |
| 投了哪些岗位记不住 | Excel 手动记录 | 自动保存投递记录和状态 |

### 2.2 MVP 范围

- ✅ 上传 PDF/DOCX/MD 简历和项目资料
- ✅ 解析岗位 JD（支持 BOSS 直聘、实习僧等格式）
- ✅ 检索个人知识库，找到与岗位相关的经历
- ✅ 匹配分析：输出 strengths / weaknesses / gaps
- ✅ 生成简历 bullet（标记"可直接写入/需确认/仅参考"）
- ✅ 生成 BOSS 沟通话术
- ✅ 所有外部动作需用户确认（Approval Gate）

### 2.3 非目标（明确不做）

- ❌ 不自动投递、不自动发送消息
- ❌ 不爬取招聘网站
- ❌ 不保存用户账号密码
- ❌ 不支持多用户系统

---

## 三、系统架构

### 3.1 整体架构

```
┌────────────────────────────────────────────┐
│                 前端 (Streamlit)            │
│          Chat-first UI · 意图路由           │
├────────────────────────────────────────────┤
│               API 层 (FastAPI)              │
│      健康检查 · 岗位分析 · 消息生成          │
├────────────────────────────────────────────┤
│              服务层 (Service)               │
│   AgentRunService · KnowledgeBaseService    │
├────────────────────────────────────────────┤
│            工作流层 (LangGraph)              │
│   parse → retrieve → grade → analyze       │
│        → build → faithfulness → report     │
├──────────────┬─────────────────────────────┤
│   Agent 层    │       RAG 基础设施层         │
│              │                              │
│ JDParser     │ Loader → Chunker              │
│ RAGRetriever │ BM25 + Embedding → RRF       │
│ MatchAnalysis│ Cross-Encoder Reranker        │
│ BuildAgent   │ Grading → Faithfulness        │
└──────────────┴─────────────────────────────┘
```

### 3.2 依赖方向（严格单向）

```
interface → service → workflow → agent/rag → domain
   │           │          │          │          │
   └───────────┴──────────┴──────────┴──────────┘
                    全部依赖 domain（纯数据模型）
```

---

### 3.3 Agent 设计：通用 Agent vs 垂直 Agent

本系统的 Agent 不是通用对话助手，而是**垂直领域专用 Agent**——每个节点只做一件事，通过 LangGraph DAG 编排。

| | 通用 Agent (OpenCode/Claude) | 本系统 (垂直 Agent) |
|---|---|---|
| 节点能力 | 通用——能读、能写、能执行 | **专用**——每个节点只做一件事 |
| 谁决定下一步 | LLM 自主决策 | **LangGraph 图的边决定** |
| Agent 关系 | 父 Agent 动态 spawn 子 Agent | **固定流水线**，10 个节点顺序执行 |
| 上下文 | 子 Agent 独立 session | 所有节点**共享 State** |
| 灵活性 | 极高 | 固定（6 种预定义意图） |
| 可控性 | 低 | **高**（每一步必然执行） |
| 成本 | 每次决策一次 LLM 调用 | **零额外 LLM 调用** |
| 适用场景 | 开放式任务 | **结构化任务**（JD 分析） |

### 3.4 认知架构：Perception → Planning → Action → Memory

本系统采用认知 Agent 四组件架构（PPAM），将求职匹配任务映射到标准的智能体认知循环：

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Perception  │───→│   Planning   │───→│    Action    │
│   感知层      │    │   规划层      │    │   执行层      │
├──────────────┤    ├──────────────┤    ├──────────────┤
│• FileLoader  │    │• Orchestrator│    │• ToolRegistry│
│• JDParser    │    │• LangGraph   │    │  15 个 Tool  │
│• IntentRouter│    │  StateGraph  │    │• BM25+Emb    │
│• GitHubReader│    │• Controlled  │    │• CrossEnc    │
│• jieba 分词   │    │  Planner     │    │• BuildAgent  │
└──────┬───────┘    └──────────────┘    └──────┬───────┘
       │                                       │
       │         ┌──────────────┐              │
       └────────→│    Memory    │←─────────────┘
                 │   记忆层      │
                 ├──────────────┤
                 │• 短时记忆     │
                 │  (会话上下文) │
                 │• 长时记忆     │
                 │  (JSONL 知识库)│
                 │• BM25 回忆    │
                 └──────────────┘
```

**四组件与代码模块的对应：**

| 认知组件 | 实现模块 | 关键技术 |
|---|---|---|
| **Perception** | `agents/orchestrator.py:_perceive()` | 意图分类（6 种）、关键词提取、文件解析（PDF/DOCX/MD） |
| **Planning** | `agents/orchestrator.py:_plan()` + `workflows/langgraph_workflow.py` | LangGraph StateGraph 确定性 DAG、ControlledPlanner 规则决策 |
| **Action** | `tools/registry.py` (15 Tool) + `rag/` Pipeline | BM25+Embedding→RRF→CrossEncoder→BuildAgent→Faithfulness |
| **Memory** | `agents/memory.py:ConversationMemory` | 短时（会话窗口）+ 长时（JSONL 持久化 + BM25 检索） |

**PPAM 循环示例（用户问"这个 JD 适合我吗"）：**

```
Perception: 识别意图=analyze_job，提取关键词=[Python,RAG,Agent]
     ↓
Memory:    从对话历史召回相关上下文（之前分析过的岗位）
     ↓
Planning:  选择 langgraph_job_match 执行路径
     ↓
Action:    执行 8 步 LangGraph 工作流 → 返回匹配度 74% + 简历建议
     ↓
Memory:    存储本轮对话（用户问题 + 系统回答）
```

---

## 四、核心流程：JD → 分析 → 输出

### 4.1 完整数据流

```
用户粘贴 JD
    │
    ▼
┌──────────────┐
│ ① JD 解析     │  JDParserAgent
│   规则+LLM    │  → ParsedJD {岗位名, 方向, 技能, 关键词}
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ ② 检索召回    │  BM25 + Qwen Embedding (双路并行)
│   top 80×2   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ ③ RRF 融合   │  score = Σ 1/(60+rank)
│   top 30      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ ④ 精排       │  bge-reranker-base (Cross-Encoder)
│   top 5       │  逐对 (query, chunk) 打分
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ ⑤ 匹配分析    │  MatchAnalysisAgent
│              │  → strengths / weaknesses / gaps
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ ⑥ 生成输出    │  BuildAgent (4 级证据约束)
│              │  → 简历 bullet + 沟通话术
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ ⑦ 真实性检查  │  FaithfulnessChecker + EvidenceGate
│              │  → 无证据 → 拒绝生成
└──────┬───────┘
       │
       ▼
  最终输出
  {匹配度, 简历建议, 沟通话术, 警告}
```

### 4.2 检索 Pipeline 详解（答辩重点）

此 Pipeline 参考 ACM SIGIR 2009 RRF 论文 + BAAI 的 bge-reranker 工作，并结合本场景（中文求职文档）做了模型选型。

```
用户问题
    │
    ├──→ jieba 分词 → BM25 关键词检索 (rank_bm25, top 80)
    │        优势：精确匹配技能名/人名/地名
    │
    ├──→ Qwen text-embedding-v3 → 语义检索 (cosine similarity, top 80)
    │        优势："Python开发"能找到"写代码"、"编程"
    │
    └──→ RRF 融合: score = Σ 1/(60+rank) → top 30
              │
              ▼
         bge-reranker-base Cross-Encoder → top 5
              │  把 query 和每个候选 chunk 拼成一对
              │  整对送进 Transformer 打分
              │  比 embedding 点乘准确 10-15%
              ▼
         FaithfulnessChecker + EvidenceGate
              │  检查每个声称是否有证据支撑
              │  检测夸大措辞（"完整实现"/"大规模部署"）
              │  planned 状态证据 → 阻止声称已完成
              ▼
         Qwen-Plus / DeepSeek LLM 生成
```

### 4.3 Chunker 逻辑

**算法：** 固定字符滑动窗口法（Fixed-size Sliding Window）

```
参数: chunk_size=800, overlap=100, step=700

text: ┌─────────────────────────────────────────┐
      │ A B C D E F G H I J K L M N O P Q ...   │
      └─────────────────────────────────────────┘

chunk_0: [0:800]     ──────────────────
chunk_1: [700:1500]       ──────────────────
chunk_2: [1400:2200]                ──────────────────

相邻窗口重叠 100 字符，确保关键信息不被切断
```

**已知局限与改进方向：** 纯字符位置切割可能在词中间切断（如"Python应用开发"被切成"Python应/用开发"）。计划引入 `RecursiveCharacterTextSplitter`，优先在段落和句子边界处切分。

---

## 五、技术选型

### 5.1 选型原则

1. **零依赖优先**：默认规则模式可脱离网络运行
2. **模型可选**：有 API Key/GPU 时自动升级到 ML 模式
3. **Python 标准库优先**：LLM Provider 用 `urllib` 而非 `requests`
4. **中文优先**：Embedding/Reranker 选型以中文效果为准

### 5.2 模型清单

| 组件 | 选型 | 部署方式 | 选型理由 |
|---|---|---|---|
| 分词 | jieba 0.42 | 本地 pip | 中文分词事实标准，轻量 |
| 关键词检索 | BM25 (rank_bm25) | 本地 pip | 词频×逆文档频率，与语义检索互补 |
| 语义检索 | Qwen text-embedding-v3 | 阿里云 API | 中文原生，1024 维，免 GPU 部署 |
| 融合排序 | RRF | 本地公式 | 公式固定零参数，SIGIR 2009 经典方法 |
| 精排 | bge-reranker-base | 本地 transformers (~1.1GB) | 中文 Cross-Encoder SOTA，CPU 可运行 |
| LLM 主 | Qwen-Plus | 阿里云 API | 中文对话能力强 |
| LLM 备 | DeepSeek-Chat | DeepSeek API | 成本低，fallback |

### 5.3 两种运行模式

| | 轻量模式（无 GPU/API） | 完整模式（有 API） |
|---|---|---|
| 检索 | BM25 + 纯 token 匹配 | BM25 + Qwen Embedding |
| 精排 | 规则打分 (LightweightReranker) | Cross-Encoder (bge-reranker-base) |
| 生成 | 规则模板 | Qwen/DeepSeek LLM |
| 延迟 | <50ms | ~800ms |
| 内存 | ~100MB | ~1.5GB |

---

## 六、关键模块实现

### 6.1 PDF 数据摄入链路

```
用户上传 PDF
    │
    ▼
KnowledgeBaseService.ingest_upload()
    │  service/knowledge_base.py
    ├─► write_bytes → runtime/uploads/xxx.pdf
    │
    ├─► FileLoader.load()
    │     rag/loaders/file_loader.py
    │     ├─ .pdf  → pypdf 逐页 extract_text()
    │     ├─ .docx → python-docx 逐段提取
    │     └─ .md   → 直接读文本
    │     返回 ProfileDocument {content="全文纯文本"}
    │
    ├─► TextChunker.chunk_document()
    │     rag/chunking/text_chunker.py
    │     clean_text() → _split_text() → _build_chunks()
    │     返回 list[DocumentChunk]（每个 800 字，重叠 100）
    │
    └─► _append_chunks() → JSONL 持久化
          runtime/knowledge_base/chunks.jsonl
```

### 6.2 多 Agent 协作（LangGraph 工作流）

```
START
  │
  ▼
parse_jd ──→ rewrite_query ──→ retrieve_context ──→ rerank
                                                       │
                          ┌────────────────────────────┤
                          ▼                            ▼
                    grade_retrieval              (retry ≤ 2)
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
        analyze_match  rewrite_query  fallback
              │         (score<0.65)  (retry 耗尽)
              ▼
        build_output
              │
              ▼
       check_faithfulness ──→ write_report ──→ END
```

**核心设计：** 检索质量不达标时自动重写查询重试，最多 2 次。耗尽后进入 fallback，诚实告知"资料不足以支持完整分析"，不编造。

### 6.3 Evidence Gate：四阶段证据约束

这是本系统的核心创新点。

| 证据状态 | 允许的动词 | 示例 | 效果 |
|---|---|---|---|
| **implemented** | 实现/构建/完成/开发 | "基于 LangGraph 实现了 Agent workflow" | 可直接写入简历 |
| **designed** | 设计/规划/架构 | "设计了 MCP 协议接入方案" | 需用户确认 |
| **planned** | 计划/拟/后续 | （不生成简历 bullet） | 仅作为学习方向 |
| **无证据** | — | "无法确定" | 拒绝生成 |

---

## 七、开发过程

### 7.1 整体推进流程

```
项目定位 ──→ 需求分析 ──→ 模块设计 ──→ 技术选型 ──→ Vibe Coding 实现
    │              │            │            │              │
    ▼              ▼            ▼            ▼              ▼
 确定做什么      明确边界    画架构图     选模型/库      写代码+测试
 不做什么        MVP 范围   模块依赖     权衡对比      迭代重构
```

### 7.2 迭代过程

| 阶段 | 内容 | 状态 |
|---|---|---|
| Phase 1 | 规则 JD 解析 · 纯 token 检索 · 模板生成 · CLI Demo | ✅ |
| Phase 2 | LLM 增强解析 · Embedding 语义检索 · LangGraph 工作流 · Streamlit UI | ✅ |
| Phase 3 | BM25 关键词检索 · RRF 融合 · Cross-Encoder Reranker · 幻觉过滤 | ✅ |
| Phase 4 (计划) | Recursive 语义分块 · 向量数据库 · 多轮对话 · Few-shot 提示 | ⏳ |

### 7.3 项目统计

| 指标 | 数值 |
|---|---|
| 源代码文件 | 85 个 Python 模块 |
| 测试用例 | 663 个（全部通过） |
| 支持格式 | PDF / DOCX / MD / TXT |
| 模型数 | 3 个本地 + 3 个 API |
| 工具注册 | 15 个标准化 Tool |

---

## 八、答辩常见问题

**Q1: 你的系统和其他求职工具有什么区别？**

A: 核心区别是**证据约束**。ChatGPT 可能帮你编一段"精通 K8s 集群管理"的经历，但我们的系统只从你的真实知识库里检索，没有证据就拒绝生成。且区分了"实现了/设计了/计划中"三种状态，planned 状态的经历不会被错误写进简历。

**Q2: RAG 检索 Pipeline 为什么设计成这样？**

A: 参考了工业界经典方案（BM25+Embedding→RRF→Cross-Encoder Reranker），其中 BM25 负责精确关键词匹配，Embedding 负责语义理解，RRF 零参数融合两者优势，Cross-Encoder 用 Transformer 逐对精排。每个环节的选择都有具体的权衡理由（见第五章技术选型）。

**Q3: 为什么不直接用大模型，还要做 RAG？**

A: 大模型容易产生幻觉——编造你没有的经历。RAG 将生成约束在检索到的真实证据范围内。另外求职场景中，技能名（"LangGraph"、"FAISS"）的精确匹配很重要，纯 LLM 无法区分你"用过"还是"听说过"。

**Q4: Chunker 为什么不用模型做语义分块？**

A: 业界生产 RAG 系统通常不需要 ML 模型做 chunking。文档的自然结构（标题、段落、句子）已经提供了足够的语义边界。本系统当前使用固定窗口法，计划升级为 `RecursiveCharacterTextSplitter`（优先在段落和句子末尾切分），这仍然是规则算法，不需要模型。

**Q5: 系统能在哪些场景下使用？**

A: (1) 个人求职：上传简历和项目资料，粘贴 JD 做匹配；(2) 批量筛选：多岗位文本→自动排序推荐；(3) 浏览器辅助：Chrome 插件读取当前页面，分析结果弹出；(4) 学校服务器展示：Docker 一键部署，Web 访问。

---

## 九、环境配置速查

### 9.1 一行安装

```bash
pip install jieba rank_bm25 sentence-transformers transformers torch
pip install -e ".[demo,dev,rag]"
```

### 9.2 模型下载（仅需一次）

```bash
python -c "
from transformers import AutoTokenizer, AutoModelForSequenceClassification
AutoTokenizer.from_pretrained('BAAI/bge-reranker-base')
AutoModelForSequenceClassification.from_pretrained('BAAI/bge-reranker-base')
"
```

### 9.3 启动

```bash
# 终端1: FastAPI
uvicorn career_agent.api.app:app --host 0.0.0.0 --port 8000

# 终端2: Streamlit
streamlit run demo/streamlit/app.py --server.port 8501
```

### 9.4 运行测试

```bash
PYTHONPATH=src:$PWD pytest tests/ -q  # 663 个测试
```

### 9.5 完整部署见

`docs/defense_technical_deep_dive.md` 第九章（原始详细版）

---

> 最后更新：2026-06-25 · 测试通过：663 passed, 0 failed
