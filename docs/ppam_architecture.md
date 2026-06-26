# PPAM 认知 Agent 架构详解

> Perception → Planning → Action → Memory

---

## 总览

```
                         ┌──────────────┐
          用户输入 ──────→│  Perception  │
                         │  感知层       │
                         └──────┬───────┘
                                │ intent + keywords
                                ▼
                         ┌──────────────┐
                         │   Planning   │
                         │   规划层      │
                         └──────┬───────┘
                                │ execution plan
                                ▼
              ┌─────────────────┴─────────────────┐
              │                                   │
              ▼                                   ▼
      ┌──────────────┐                    ┌──────────────┐
      │    Action    │◄───────────────────│    Memory    │
      │   执行层      │    存储/召回       │   记忆层      │
      └──────────────┘                    └──────────────┘
```

---

## 一、Perception（感知层）

### 1.1 定义

**让系统"看懂"用户在说什么。** 输入是原始文本，输出是结构化的意图和关键词。

### 1.2 实现模块

| 感知类型 | 模块 | 文件 | 技术 |
|---|---|---|---|
| 用户意图感知 | `OrchestratorAgent._perceive()` | `agents/orchestrator.py:57` | 关键词规则匹配 |
| 文件内容感知 | `FileLoader.load()` | `rag/loaders/file_loader.py:22` | pypdf / python-docx |
| JD 结构化感知 | `JDParserAgent.parse()` | `agents/jd_parser.py:65` | 正则 + LLM fallback |
| GitHub 数据感知 | `GitHubRemoteReader.read_repo()` | `github/remote_repo_reader.py:32` | GitHub API |

### 1.3 意图路由

```
用户输入文本
    │
    ▼
_is_jd()?          → len>200 且含"岗位要求/职责/招聘" → analyze_job
_is_resume()?      → 含"简历/bullet/改写"             → tailor_resume
_is_message()?     → 含"话术/沟通/打招呼/HR"          → generate_message
_is_profile()?     → 含"知道我/资料/知识库/画像"       → show_profile
_is_github()?      → 含"github.com"                  → github_ingest
_is_match()?       → 含"适合/匹配/分析"               → analyze_job
default            →                                  → chat
```

### 1.4 代码路径

```python
# agents/orchestrator.py:57
@staticmethod
def _perceive(text: str) -> tuple[str, list[str]]:
    t = text.lower()
    
    if len(text) > 200 and any(kw in text for kw in ["岗位要求", "岗位职责", ...]):
        return ("analyze_job", keywords)
    if any(kw in text for kw in ["简历", "bullet", "改写", ...]):
        return ("tailor_resume", keywords)
    # ... 6 种意图识别
    
    return ("chat", keywords)
```

---

## 二、Planning（规划层）

### 2.1 定义

**根据感知结果，决定走哪条执行路径。**

### 2.2 实现模块

| 规划方式 | 模块 | 文件 | 说明 |
|---|---|---|---|
| 路径选择 | `OrchestratorAgent._plan()` | `agents/orchestrator.py:101` | 意图 → 执行路径映射 |
| 确定性 DAG | `create_langgraph_workflow()` | `workflows/langgraph_workflow.py:573` | LangGraph StateGraph |
| 规则决策 | `ControlledPlanner.decide()` | `tools/planner.py:45` | 状态驱动，决定下一步工具 |
| 条件路由 | `_route_after_grading()` | `workflows/langgraph_workflow.py:371` | 检索质量 → retry/continue/fallback |

### 2.3 路径映射

```
analyze_job      → langgraph_job_match (LangGraph 8 节点 DAG)
tailor_resume    → langgraph_job_match (同上)
generate_message → message_agent (MessageAgent 模板生成)
show_profile     → kb_lookup (KnowledgeBaseService 查询)
github_ingest    → github_ingest (GitHubRepoReader 拉取)
chat             → rag_chat (BM25 检索 + LLM 对话)
```

### 2.4 代码路径

```python
# agents/orchestrator.py:101
@staticmethod
def _plan(intent: str, user_message: str) -> str:
    plans = {
        "analyze_job": "langgraph_job_match",
        "tailor_resume": "langgraph_job_match",
        "generate_message": "message_agent",
        "show_profile": "kb_lookup",
        "github_ingest": "github_ingest",
        "chat": "rag_chat",
    }
    return plans.get(intent, "rag_chat")
```

### 2.5 LangGraph DAG（langgraph_job_match 的完整图）

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

**10 个节点：** parse_jd / rewrite_query / retrieve_context / rerank / grade_retrieval / analyze_match / build_output / check_faithfulness / write_report / fallback

**2 条条件边：** grade_retrieval 分叉 → retry / continue / fallback

---

## 三、Action（执行层）

### 3.1 定义

**根据规划结果，执行具体的动作。**

### 3.2 工具注册表

**文件：** `tools/registry.py:14-503`

15 个标准化 Tool，所有能力必须注册才能调用：

```
ToolRegistry
├── ParseJDTool         ← JDParserAgent 封装
├── PlanQueriesTool     ← RAGRetrieveAgent 封装
├── RewriteQueryTool    ← 查询重写
├── RetrieveProfileTool ← 知识库检索
├── RerankChunksTool    ← 重排序
├── GradeRetrievalTool  ← 检索评分
├── SelectEvidenceTool  ← 证据选择
├── AnalyzeMatchTool    ← 匹配分析
├── GenerateGroundedAnswerTool ← 生成输出
├── CheckFaithfulnessTool ← 真实性检查
├── FallbackTool        ← 兜底处理
├── WriteReportTool     ← 写报告
├── WriteDiagnosticsTool ← 写诊断
├── WebSearchTool       ← 网络搜索
└── GitHubRepoTool      ← GitHub 读取
```

### 3.3 Tool 接口

```python
# tools/base.py:32-65
class Tool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:           # 工具唯一名称
        ...
    
    @property
    @abstractmethod
    def description(self) -> str:    # 功能描述
        ...
    
    @abstractmethod
    def run(self, **kwargs) -> ToolResult:  # 执行
        ...
```

### 3.4 RAG 检索 Pipeline

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

### 3.5 Evidence Gate（独有创新）

| evidence status | 允许的动词 | 不允许 | 简历权限 |
|---|---|---|---|
| implemented | 实现/构建/完成/开发 | — | ✅ 可直接写入 |
| designed | 设计/规划/架构 | 实现/构建 | ⚠️ 需降级措辞 |
| planned | — | 全部 | ❌ 阻止生成 |
| 无 evidence | — | 全部 | ❌ 阻止生成 |

---

## 四、Memory（记忆层）

### 4.1 定义

**让系统"记住"之前的对话和用户信息。**

### 4.2 实现模块

**文件：** `agents/memory.py:30-140`

```
ConversationMemory
├── 短时记忆 (short-term)
│   ├── 内存列表，保留最近 20 条消息
│   ├── remember(role, content)  → 写入短时 + 持久化
│   ├── get_context(n)           → 最近 n 条作为 LLM 上下文
│   └── context_text(n)          → 格式化为 "[用户]: ... [助手]: ..."
│
├── 长时记忆 (long-term)
│   ├── JSONL 文件持久化 (runtime/memory/conversations.jsonl)
│   ├── recall(query, top_k)    → BM25 检索历史相关对话
│   └── summary()               → 会话摘要
│
└── 知识库记忆 (KnowledgeBase)
    ├── chunks.jsonl             → 用户上传的资料 chunk
    ├── chunks.repos.txt         → GitHub 仓库列表
    └── ProfileItems             → 结构化用户画像
```

### 4.3 记忆生命周期

```
用户发言
  │
  ├─→ 短时记忆: remember("user", text) → 内存列表 + JSONL
  │
  ├─→ 长时召回: recall(text, top_k=3) → BM25 搜历史
  │     返回相关历史对话，作为 LLM 上下文
  │
  ├─→ 知识库: kb_service.search(text) → BM25 搜知识库
  │     返回相关证据片段
  │
系统回复
  │
  └─→ 短时记忆: remember("assistant", text) → 内存列表 + JSONL
```

### 4.4 三层记忆对比

| | 短时记忆 | 长时记忆 | 知识库记忆 |
|---|---|---|---|
| 存什么 | 当前对话 | 所有历史对话 | 用户资料 (PDF/DOCX/MD) |
| 存储位置 | 内存列表 | JSONL 文件 | JSONL chunks |
| 容量限制 | 最近 20 条 | 全量 | 全量 |
| 检索方式 | 顺序读取 | BM25 关键词 | BM25 + Embedding + RRF + CrossEncoder |
| 作用 | LLM 上下文窗口 | 跨会话回忆 | 证据支撑 |
| 对应变量 | `self._short_term` | `self._history_file` | `kb_service.chunk_file` |

---

## 五、答辩串讲思路

```
"我的系统遵循认知 Agent 的 PPAM 框架——Perception、Planning、Action、Memory。

感知层负责理解用户输入：6 种意图分类、PDF 文件解析、JD 结构化提取。

规划层负责决策：意图映射到执行路径、LangGraph DAG 保证流程完整、
ControlledPlanner 状态驱动工具选择。

执行层负责行动：15 个标准化 Tool、工业级 RAG Pipeline (BM25+Embedding
+RRF+CrossEncoder)、Evidence Gate 四阶段证据约束。

记忆层负责上下文：短时记忆存当前对话、长时记忆 JSONL 持久化 + BM25 检索、
知识库记忆存用户全部资料。

这四层全部有代码实现、有测试覆盖、有数据流追踪。"
```
