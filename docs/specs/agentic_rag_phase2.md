# Phase 2 Agentic RAG Upgrade：需求与接口 Spec

## 需求总览

| ID | 需求 | 状态 |
|----|------|------|
| R1 | Hybrid Retrieval | ✅ Task D 完成 |
| R2 | Reranker | ⏳ Task E |
| R3 | Agentic Retry | ⏳ Task F |
| R4 | Tool Calling | ⏳（并入 Task G/H）|
| R5 | Faithfulness Checker | ⏳ Task G |
| R6 | Diagnostics & Eval | ⏳ Task J |
| R7 | Domain Schema | ✅ Task B 完成 |
| R8 | LLM Provider Abstraction | ⏳ Task C |
| R9 | Agent Run Service | ⏳ Task H |
| R10 | Codex-like Streamlit UI | ⏳ Task I |

## R1: Hybrid Retrieval ✅

- 同时运行 keyword + embedding 检索
- 分数归一化到 [0, 1]
- 融合公式：0.40×vector + 0.35×keyword + 0.15×metadata + 0.10×priority
- 去重：相同 chunk 不重复
- metadata_score：source_type_weight + JD skill_overlap

## R2: Reranker

- 检索后重排 Top-K
- 考虑：skill_overlap, source_quality, evidence_specificity, length_penalty, duplicate_penalty
- 输出 rerank_score + rerank_reason
- 默认为规则实现，接口预留 LLM reranker

## R3: Agentic Retry

- LangGraph 条件分叉：高分通过，低分 retry
- rewrite_query 基于 missing_keywords + previous_queries + fail_reason
- max_retries 后进入 fallback，不编造经历
- retry_history 写入 state 和 diagnostics

## R4: Tool Calling（并入 Task G/H）

- Tool interface: name, description, input_schema, output_schema, safety_notes, run()
- Planner: 根据 state 选择 tool（规则型，LLM 可插拔）
- ToolCallTrace 写入 diagnostics

## R5: Faithfulness Checker

- 每条 GeneratedBullet 必须有至少一个 evidence
- 检查 bullet 中的技能是否在 evidence 或 JD 中出现
- 检测夸大 claims
- faithfulness_score < 0.75 → revise_required

## R6: Diagnostics & Eval

- `outputs/diagnostics/{trace_id}.json`
- `outputs/rag_reports/{trace_id}.md`
- eval dataset：`data/eval/jd_cases.jsonl`（8+ JD）
- eval runner：`scripts/run_eval.py`

## R7: Domain Schema ✅

- 11 个 dataclass schema
- score 必须是 0.0~1.0 finite float，bool 拒绝
- 所有 generated content 可关联 source
- to_dict/from_dict 序列化

## R8: LLM Provider Abstraction

**目标**：系统不再只依赖规则引擎，可插拔 LLM 做结构化解析、query rewrite、匹配分析、生成。

### LLM Provider Interface

```python
class LLMProvider(ABC):
    """Pluggable LLM backend."""

    @abstractmethod
    def generate(self, prompt: str, *, system_prompt: str = None) -> str: ...

    @abstractmethod
    def generate_structured(self, prompt: str, *, schema: dict) -> dict: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @property
    @abstractmethod
    def is_available(self) -> bool: ...
```

### Providers

- `QwenProvider` — 通义千问（已有，需规范化）
- `DeepSeekProvider` — DeepSeek（已有，需规范化）
- `MockLLMProvider` — 测试用
- 从 `.env` 读取配置，Constructor 支持显式注入

### LLM 使用边界

| 允许 | 不允许 |
|------|--------|
| 结构化解析 JD | 凭空编造用户经历 |
| Query rewrite | 绕过 evidence 生成简历 |
| 匹配分析 | 直接执行任意工具 |
| 生成自然语言回答 | 修改数据库/文件（除非通过 tool） |
| Faithfulness check | — |

### Fallback

- LLM 不可用 → 回退规则实现
- trace 中记录 `llm_unavailable`
- demo 默认可跑（规则模式）

## R9: Agent Run Service

**目标**：UI 不直接拼流程，所有请求通过统一入口。

```python
@dataclass
class AgentRunRequest:
    user_message: str
    raw_jd: str = ""
    mode: str = "analyze"  # analyze / resume / chat
    profile_scope: str = ""


@dataclass
class AgentRunResult:
    final_answer: str
    match_summary: dict
    generated_bullets: list[str]
    communication_script: str
    evidence_sources: list[str]
    retrieval_scores: dict
    trace_id: str
    report_path: str
    diagnostics_path: str
    warnings: list[str]


class AgentRunService:
    def run(self, request: AgentRunRequest) -> AgentRunResult: ...
```

Service 内部调用 LangGraph workflow，不在 UI 层拼流程。

## R10: Codex-like Streamlit UI

**目标**：极简 Agent 对话界面。

### 布局

```
┌─ Smart Apply Agent ──────────────────────┐
│                                          │
│  🤖 Agent 回答区域                        │
│  （匹配分析 + 建议 + 话术 + 来源）          │
│                                          │
│  ┌─ 📋 查看详情 ───────────────────┐     │
│  │  ▸ Parsed JD / Queries          │     │
│  │  ▸ Top-K Evidence / Scores      │     │
│  │  ▸ Retry History / Tool Trace   │     │
│  │  ▸ Faithfulness / Source Map    │     │
│  └─────────────────────────────────┘     │
│                                          │
│  ─────────────────────────────────────── │
│  📎 粘贴 JD 或输入问题...                  │
│  [Ask Agent]                             │
└──────────────────────────────────────────┘
```

### 原则
- 一个输入框 + 一个回答区
- 执行步骤简洁展示（3-5 步）
- 技术细节全部折叠
- 默认只给用户清晰结论
- 不做复杂 dashboard、不堆按钮

## Non-Goals

- 不做自动投递
- 不做平台爬虫
- 不做完全自治 LLM Agent
- 不删除已有通过测试的 API
- 不做完整 PDF 简历生成
- 不引入复杂前端框架（React/Vue）
- 不做多用户管理

## State Schema（扩展后）

```
raw_jd: str
parsed_jd: ParsedJD | None
queries: list[RetrievalQuery]
retrieved_chunks: list[RetrievedChunk]
retrieval_scores: RetrievalScore | None
missing_keywords: list[str]
decision: str                     # continue / retry / fallback
retry_count: int
max_retries: int                  # default 2
retry_history: list[dict]
query_rewrite_reason: str
fallback_reason: str
selected_evidence: list[Evidence]
match_analysis: MatchAnalysis | None
generated_bullets: list[GeneratedBullet]
faithfulness_report: FaithfulnessReport | None
tool_trace: list[ToolCallTrace]
workflow_trace: list[str]
report_path: str
diagnostics_path: str
trace_id: str
status: str
error_message: str
user_message: str                 # 用户自然语言输入
mode: str                         # analyze / resume / chat
final_answer: str                 # Agent 最终回答（自然语言）
```

## 验收标准

1. 输入 JD → 解析技能 → Hybrid RAG 检索 → Reranker 重排
2. 低分自动 retry，max 后 fallback
3. 每条生成内容有 evidence source
4. Faithfulness checker 标记 unsupported claims
5. LLM 可插拔，不可用时回退规则
6. Agent Run Service 统一入口
7. Streamlit UI 极简对话式，Codex 风格
8. 技术细节可展开但不默认展示
9. Diagnostics JSON + Markdown report 输出
10. 离线 eval dataset 可运行
11. 364+ 已有测试持续通过
