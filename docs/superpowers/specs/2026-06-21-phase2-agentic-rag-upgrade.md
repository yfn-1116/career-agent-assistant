# Phase 2: Agentic RAG Upgrade Design

## Purpose

Upgrade the current linear RAG workflow into an **explainable, gradable, retryable,
tool-callable Agentic RAG system**. This is Phase 2 — the system must move from
"fixed pipeline demo" to "engineer-grade RAG with conditional execution".

## Current State (Phase 1)

| Capability | Status | Limitation |
|---|---|---|
| Keyword retrieval | ✅ | Standalone |
| Semantic (embedding) retrieval | ✅ | Standalone |
| Hybrid fusion | ❌ | Not implemented |
| Reranker | ❌ | Not implemented |
| Retrieval grading | ✅ | 5-dimension rule-based |
| LangGraph workflow | ✅ | 7-node linear, no branches |
| Query rewrite | ✅ | Template-based, no retry |
| Retry loop | ❌ | decision=retry written but unused |
| Tool calling | ❌ | Agents are fixed node functions |
| Diagnostics JSON | ❌ | Markdown-only report |
| Multi-round evidence | ❌ | Single-shot retrieval |

## Goals

1. **Conditional branching**: LangGraph workflow branches on retrieval quality.
2. **Query rewrite retry**: Low-score retrieval triggers smarter query rewrites.
3. **Hybrid RAG**: Keyword + vector scores fused into a single ranking.
4. **Reranker**: Rule-based reranker boosts skill-matched, penalizes duplicates.
5. **Tool calling layer**: Agents wrapped as tools with schemas, traceable execution.
6. **Diagnostics**: JSON diagnostics + enhanced Markdown report.

## Non-Goals

- No auto-apply or platform scraping.
- No LLM-driven autonomous agent (planner is rule-based, tool-level LLM is optional).
- No deletion of existing passing tests.
- No complete project rewrite — each module upgraded independently.

## Architecture

```
User → CLI / Streamlit
         │
         ▼
┌─────────────────────────────────────┐
│         LangGraph Workflow          │
│                                     │
│  parse_jd ──► rewrite_query ◄──┐   │
│       │            │            │   │
│       │      retrieve_context   │   │
│       │            │            │   │
│       │      grade_retrieval    │   │
│       │            │            │   │
│       │   ┌───────┴───────┐    │   │
│       │   │ score >= 0.65 │    │   │
│       │   └───────┬───────┘    │   │
│       │       yes │ no         │   │
│       │           │            │   │
│       │      retry < max?      │   │
│       │      yes │    │ no     │   │
│       │      retry    fallback │   │
│       │      └──► loop ───────┘   │
│       │                            │
│       ▼                            │
│  rerank_chunks ◄── optional        │
│       │                            │
│       ▼                            │
│  analyze_match                     │
│       │                            │
│       ▼                            │
│  build_output                      │
│       │                            │
│       ▼                            │
│  write_report + diagnostics        │
└─────────────────────────────────────┘
```

## Task Breakdown

### Task 3: Agentic RAG Conditional Branching & Query Rewrite Retry
- Add conditional edges to LangGraph workflow
- Upgrade rewrite_query_node with missing-keyword-aware logic
- Add fallback_node for exhausted retries
- Enhance report with retry history

### Task 4: Hybrid RAG + Reranker
- HybridRetriever: keyword + vector fusion
- Metadata-based score boost
- Rule-based reranker (skill overlap, specificity, source quality, dedup)
- Upgraded per-chunk score fields
- Enhanced report table

### Task 5: Tool Calling Agent Layer
- Tool registry with named tools and schemas
- Rule-based planner that selects tools from state
- Execution trace per tool call
- Tool calling architecture (LLM-pluggable later)

### Task 6: Evaluation Dashboard / Diagnostics
- Diagnostics JSON output per run
- Enhanced Markdown with hybrid scores, retry history, source mapping
- Streamlit updates for tabular score display and retry history

## State Extension

The `JobMatchState` will be extended across tasks:

```
Task 3 adds: max_retries, query_rewrite_reason, retry_history
Task 4 adds: hybrid_scores (per chunk), rerank_reason
Task 5 adds: tool_trace, planner_decision
Task 6 reads: all of the above for diagnostics
```

## Constraints

- All existing tests must continue to pass.
- RAG grading API (`grade_retrieval`) must not be broken.
- Must work without external LLM in default mode.
- Each task = one commit.
- Each task includes tests and demo verification.

## Acceptance Criteria

1. Input a JD → system parses skills → generates queries.
2. Hybrid RAG runs keyword + semantic retrieval simultaneously.
3. Reranker re-ranks top-K with explicit reasons.
4. Retrieval grader scores each round.
5. Low score → automatic query rewrite retry.
6. Max retries exhausted → fallback with missing-keyword suggestions.
7. Passed retrieval → match analysis → resume generation.
8. Every generated bullet has a source evidence.
9. Output: Markdown report + diagnostics JSON.
10. CLI or Streamlit shows the full process.
