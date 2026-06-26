# 基于证据约束的智能实习投递 Agent

> 毕业答辩 PPT 素材

---

## 一、项目定位

| 是 | 不是 |
|---|---|
| 基于个人知识库的求职匹配分析 | 自动投递机器人 / GPT 包装壳 |
| 所有声称有据可查（Evidence-Grounded） | 简历生成器（编造经历） |

**一句话：** 一个"不能说谎"的求职助手。所有生成内容必须能从真实经历中找到证据。

---

## 二、系统架构：PPAM 认知 Agent

本系统按认知 Agent 四组件（PPAM）设计，代码按层组织：

```
用户输入 → Perception → Planning → Action → 输出
               │            │          │
               └────────────┴──────────┘
                        │
                     Memory
```

| 组件 | 一句话 | 包路径 | 核心模块 |
|---|---|---|---|
| **Perception** | 看懂用户说什么 | `perception/` | FileLoader + JDParser + GitHubReader + 意图路由 |
| **Planning** | 决定走哪条路 | `planning/` | Orchestrator + LangGraph DAG + ControlledPlanner |
| **Action** | 干活 | `action/` | ToolRegistry (15 tools) + RAG Pipeline + Evidence Gate |
| **Memory** | 记住上下文 | `memory/` | ConversationMemory + KnowledgeBaseService |

---

## 三、Perception（感知层）

**职责：把原始输入变成结构化信息。**

```
用户输入
    │
    ├── 文本 → _perceive() ──→ {intent, keywords}
    │           agents/orchestrator.py:57
    │
    ├── PDF/DOCX → FileLoader ──→ 全文纯文本
    │               rag/loaders/file_loader.py
    │
    └── JD → JDParserAgent ──→ ParsedJD {job_title, direction, skills}
              agents/jd_parser.py
```

**6 种意图分类（关键词规则）：**

| 信号 | 意图 |
|---|---|
| "岗位要求/职责/招聘" + 长度>200 | analyze_job |
| "简历/bullet/改写" | tailor_resume |
| "话术/沟通/打招呼/HR" | generate_message |
| "知识库/画像/了解我" | show_profile |
| "github.com" | github_ingest |
| default | chat |

---

## 四、Planning（规划层）

**职责：根据意图选择执行路径，编排 Agent 协作。**

**意图 → 执行路径映射：**

```python
analyze_job  → langgraph_job_match   # LangGraph 10 节点 DAG
chat         → rag_chat              # BM25 检索 + LLM
show_profile → kb_lookup             # 知识库查询
...
```

**LangGraph 工作流（核心执行图）：**

```
parse_jd → rewrite → retrieve → rerank → grade
                                              │
                    ┌─────────────────────────┤
                    ▼                         ▼
              analyze_match            rewrite (retry≤2)
                    │                         │
                    ▼                         ▼
              build_output               fallback (耗尽)
                    │
                    ▼
              faithfulness → report → END
```

**10 个节点，每个是专用 Agent：**

| 节点 | Agent | 职责 |
|---|---|---|
| parse_jd | JDParserAgent | JD → 结构化 |
| retrieve | RAGRetrieveAgent + BM25 + Embedding | 双路检索 |
| rerank | CrossEncoder / LightweightReranker | 精排 |
| grade | grade_retrieval() | 5 维度评分 |
| analyze | MatchAnalysisAgent | 匹配分析 |
| build | BuildAgent | 生成简历+话术 |
| faithfulness | FaithfulnessChecker | 真实性检查 |

---

## 五、Action（执行层）

**职责：15 个 Tool 统一调用 + RAG 检索 Pipeline + Evidence Gate。**

### 5.1 ToolRegistry

15 个标准化 Tool，接口统一：

```python
class Tool(ABC):
    name: str
    description: str
    def run(**kwargs) → ToolResult
```

### 5.2 RAG 检索 Pipeline

```
用户查询
  → jieba 分词
  → BM25 关键词检索 (rank_bm25, top 80)
  → Qwen Embedding 语义检索 (text-embedding-v3, top 80)
  → RRF 融合 (k=60) → top 30
  → bge-reranker-base Cross-Encoder → top 5
  → FaithfulnessChecker + EvidenceGate
  → Qwen-Plus / DeepSeek LLM 生成
```

| 环节 | 技术 | 部署 |
|---|---|---|
| 分词 | jieba 0.42 | 本地 pip |
| BM25 | rank_bm25 0.2 | 本地 pip |
| Embedding | Qwen text-embedding-v3 | 阿里云 API |
| 融合 | RRF (k=60) | 本地公式 |
| 精排 | bge-reranker-base (279M) | 本地 ~1.1GB |
| LLM | Qwen-Plus / DeepSeek | API |

### 5.3 Evidence Gate（独有创新）

| 状态 | 简历权限 | 例子 |
|---|---|---|
| implemented | ✅ 可直接写入 | "实现了 Agent workflow" |
| designed | ⚠️ 需降级措辞 | "实现了 MCP" → "设计了 MCP 方案" |
| planned | ❌ 阻止 | 不生成简历 bullet |

---

## 六、Memory（记忆层）

```
ConversationMemory
├── 短时记忆：内存列表（最近 20 条）─→ LLM 上下文
├── 长时记忆：JSONL 持久化 + BM25 检索 ─→ 跨会话回忆
└── 知识库：chunks.jsonl ─→ 完整 RAG Pipeline 检索
```

| | 短时 | 长时 | 知识库 |
|---|---|---|---|
| 存什么 | 当前对话 | 所有历史 | PDF/DOCX/MD |
| 怎么查 | 顺序读 | BM25 | BM25+Embedding+RRF+CE |
| 作用 | 上下文 | 跨会话 | 证据支撑 |

---

## 七、Agent 设计对比

参考 OpenCode 的 Tool 注册 + Provider 抽象，但做了关键简化：

| | OpenCode（通用） | 本系统（垂直） |
|---|---|---|
| 谁决策 | LLM 自主 | **规则 + LangGraph DAG** |
| Agent 关系 | 父 spawn 子 | **固定流水线** |
| 灵活性 | 极高 | 固定 |
| 可控性 | 低 | **高** |
| 成本 | 每步 LLM | **零额外 LLM** |

> "OpenCode 是通用士兵，我的系统是流水线工人。求职场景流程固定，流水线更可控。"

---

## 八、技术选型总览

| 组件 | 选型 | 部署 |
|---|---|---|
| 分词 | jieba 0.42 | 本地 |
| BM25 | rank_bm25 | 本地 |
| Embedding | Qwen text-embedding-v3 | API |
| RRF | 公式 1/(60+rank) | 本地 |
| Reranker | bge-reranker-base | 本地 ~1.1GB |
| LLM | Qwen-Plus + DeepSeek | API |
| 工作流 | LangGraph | 本地 |
| 前端 | Streamlit | 本地 |
| 后端 | FastAPI | 本地 |

---

## 九、开发过程

| 阶段 | 内容 | 状态 |
|---|---|---|
| Phase 1 | 规则 JD 解析 + 纯 token 检索 + CLI Demo | ✅ |
| Phase 2 | LLM 增强 + Embedding + LangGraph + Streamlit | ✅ |
| Phase 3 | BM25 + RRF + CrossEncoder + PPAM 架构 | ✅ |
| 测试 | **683 passed, 0 failed** | ✅ |

---

## 十、答辩常见问题

**Q1: 和 ChatGPT/Claude 有什么区别？**

A: 核心区别是**证据约束**。ChatGPT 可能编造经历，本系统的 Evidence Gate 保证所有声称必须能从知识库找到真实证据，planned 状态的经历不会被写进简历。

**Q2: RAG Pipeline 为什么设计成这样？**

A: 参考了红楼梦知识库的 Boss Baseline（BM25+Embedding→RRF→Reranker）。BM25 精确匹配技能名，Embedding 语义理解，RRF 零参数融合，Cross-Encoder 逐对精排。

**Q3: Agent 和 OpenCode 有什么区别？**

A: 参考了 OpenCode 的 Tool 注册和 Provider 抽象。但针对求职固定场景，用 LangGraph 确定性 DAG 替代 LLM 自主决策——更可控、更可解释、零额外成本。

**Q4: 为什么不直接用大模型做 Chunking？**

A: 业界不用 ML 模型做 chunking。文档的自然结构（段落、句子）已经提供足够边界，用规则算法就够了。真正需要模型的是检索和精排，这些我们都已经用了。

**Q5: 系统能在哪些场景用？**

A: 个人求职 + 批量筛选 + 浏览器辅助 + Docker 学校服务器部署。

---

## 十一、环境配置速查

```bash
# 安装
pip install jieba rank_bm25 sentence-transformers
pip install -e ".[demo,dev,rag]"

# 模型（仅一次）
python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification
AutoTokenizer.from_pretrained('BAAI/bge-reranker-base')
AutoModelForSequenceClassification.from_pretrained('BAAI/bge-reranker-base')"

# 启动
uvicorn career_agent.api.app:app --host 0.0.0.0 --port 8000 &
streamlit run demo/streamlit/app.py --server.port 8501

# 测试
PYTHONPATH=src:$PWD pytest tests/ -q   # 683 passed
```

---

> 详细技术手册见 `defense_speaker_notes.md` · RAG 流程图见 `rag_pipeline_flow.md`
> PPAM 详解见 `ppam_architecture.md` · Evidence 设计见 `evidence_design.md`
