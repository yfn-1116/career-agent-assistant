# Phase 2 Agentic RAG Upgrade：需求与接口 Spec

## 需求列表

### R1: Hybrid Retrieval
- 同时运行 keyword + embedding 检索
- 分数归一化到 [0, 1]
- 融合公式：0.40×vector + 0.35×keyword + 0.15×metadata + 0.10×priority
- 去重：相同 chunk 不重复；同 source 超阈值减分

### R2: Reranker
- 检索后重排 Top-K
- 考虑：skill_overlap, source_quality, evidence_specificity, length_penalty, duplicate_penalty
- 输出 rerank_score + rerank_reason
- 默认为规则实现，接口预留 LLM reranker

### R3: Agentic Retry
- LangGraph 条件分叉：高分通过，低分 retry
- rewrite_query 基于 missing_keywords + previous_queries + fail_reason
- max_retries 后进入 fallback，不编造经历
- retry_history 写入 state 和 diagnostics

### R4: Tool Calling
- Tool interface: name, description, input_schema, output_schema, safety_notes, run()
- Tool Registry: 10 个标准 tool
- Planner: 根据 state 选择 tool（规则型，LLM 可插拔）
- ToolCallTrace: tool_name, input_summary, output_summary, duration_ms, success, error

### R5: Faithfulness Checker
- 每条 GeneratedBullet 必须有至少一个 evidence
- 检查 bullet 中的技能是否在 evidence 或 JD 中出现
- 检测夸大 claims（如 "完整实现 MCP" 但 evidence 只说 "预留接口"）
- faithfulness_score < 0.75 → revise_required

### R6: Diagnostics
- `outputs/diagnostics/{trace_id}.json`：完整运行数据
- `outputs/rag_reports/{trace_id}.md`：增强版 Markdown 报告
- eval dataset：`data/eval/jd_cases.jsonl`（8+ JD）
- eval runner：`scripts/run_eval.py`

### R7: Domain Schema
- 所有核心对象使用 dataclass
- score 必须是 0.0~1.0 finite float
- bool 不允许作为 score
- 所有 generated content 可关联 source

## Non-Goals

- 不做自动投递
- 不做平台爬虫
- 不做完全自治 LLM Agent（planner 是规则型）
- 不删除已有通过测试的 API
- 不做完整 PDF 简历生成
- 不接外部 RAG 服务（如 Pinecone, Weaviate）

## 接口设计

### Tool Interface

```python
class Tool:
    name: str
    description: str
    input_schema: dict       # JSON Schema
    output_schema: dict      # JSON Schema
    safety_notes: list[str]

    def run(self, **kwargs) -> ToolResult: ...
```

### Tool Registry

```
parse_jd_tool          — 解析 JD → ParsedJD
plan_queries_tool      — 生成检索 queries
retrieve_chunks_tool   — Hybrid RAG 检索
rerank_chunks_tool     — 重排序
grade_retrieval_tool   — 检索评分
select_evidence_tool   — 选择最相关 evidence
analyze_match_tool     — 匹配分析
generate_resume_tool   — 生成简历 bullet
check_faithfulness_tool — 校验真实性
write_report_tool      — 写报告
```

### Planner 决策逻辑

```
state.parsed_jd is None      → parse_jd_tool
state.queries is empty       → plan_queries_tool
state.retrieved_chunks empty → retrieve_chunks_tool
state.rerank_scores is None  → rerank_chunks_tool
state.retrieval_scores low   → plan_queries_tool (retry)
state.retrieval_scores pass  → select_evidence_tool → analyze_match_tool
state.match_analysis exists  → generate_resume_tool
state.generated exists       → check_faithfulness_tool
state.faithfulness pass      → write_report_tool
state.faithfulness fail      → generate_resume_tool (revise)
```

## State Schema

### JobMatchState（扩展后）

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
```

## Retrieval Result Schema

```python
@dataclass
class RetrievedChunk:
    chunk_id: str
    source: str                # source file path
    content: str               # full chunk text
    summary: str               # short summary
    keyword_score: float       # [0, 1]
    vector_score: float        # [0, 1]
    metadata_score: float      # [0, 1]
    final_hybrid_score: float  # [0, 1]
    rerank_score: float        # [0, 1]
    matched_skills: list[str]
    rerank_reason: str
```

## Diagnostics Schema

```json
{
  "trace_id": "...",
  "timestamp": "...",
  "raw_jd": "...",
  "parsed_jd": {...},
  "query_rounds": [
    {
      "round": 1,
      "queries": [...],
      "retrieved_chunks": [...],
      "hybrid_scores": {...},
      "rerank_scores": {...},
      "retrieval_score": {...},
      "decision": "retry"
    }
  ],
  "retry_history": [...],
  "tool_trace": [
    {
      "tool_name": "parse_jd_tool",
      "input_summary": "...",
      "output_summary": "...",
      "duration_ms": 12,
      "success": true,
      "error": null
    }
  ],
  "selected_evidence": [...],
  "generated_bullets": [...],
  "faithfulness_report": {...},
  "unsupported_claims": [...],
  "final_decision": "continue",
  "report_path": "..."
}
```

## Report Schema (Markdown)

```
# RAG Agent 诊断报告
## 1. JD 解析结果
## 2. Agent Workflow Trace
## 3. Query Rewrite History
## 4. Hybrid Retrieval Table
## 5. Reranker Table
## 6. Retrieval Grading
## 7. Evidence Selection
## 8. Faithfulness Check
## 9. Final Output
## 10. Source Mapping
## 11. Missing Evidence
```

## 验收标准

1. 输入 JD → 解析技能 → 生成 queries
2. Hybrid RAG 同时关键词+语义检索
3. Reranker 重排并给出原因
4. 检索评分每轮可见
5. 低分自动 retry rewrite_query
6. max_retries 后 fallback（不编造）
7. 高分进入匹配分析 → 生成简历 bullet
8. 每条 bullet 有 evidence source
9. Faithfulness checker 标记 unsupported claims
10. 输出 diagnostics JSON + Markdown report
11. 离线 eval dataset 可运行
12. CLI/Streamlit 展示完整过程
13. 测试覆盖核心行为
