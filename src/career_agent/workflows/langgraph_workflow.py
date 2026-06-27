"""LangGraph-based job match workflow — full Agentic RAG pipeline.

Node order::

    parse → rewrite → retrieve → rerank → grade ──(score≥0.65)──► analyze → build → faithfulness → write
       ▲                        │          │
       │     (retry: score<0.65)│          │(retry>=max)
       └────────────────────────┘          └──► fallback ──► END
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from career_agent.agents.build_agent import BuildAgent
from career_agent.agents.jd_parser import JDParserAgent
from career_agent.agents.match_analysis_agent import MatchAnalysisAgent
from career_agent.agents.rag_retrieve_agent import RAGRetrieveAgent
from career_agent.agents.state import (
    GeneratedOutput,
    MatchAnalysisResult,
    ParsedJD,
)
from career_agent.domain.schemas import Evidence, GeneratedBullet
from career_agent.evaluation.faithfulness import FaithfulnessChecker, FaithfulnessReport
from career_agent.rag.embeddings.embedding_store import EmbeddingVectorStore
from career_agent.rag.embeddings.qwen_embedding import QwenEmbeddingProvider
from career_agent.rag.grading import GRADE_FAILED, RetrievalGradeReport, grade_retrieval
from career_agent.rag.pipeline import RAGPipeline
from career_agent.rag.reranker import LightweightReranker
from career_agent.rag.retrievers.hybrid_retriever import HybridRetriever
from career_agent.rag.schemas import RetrievedEvidence
from career_agent.rag.vectorstores.memory_store import MemoryVectorStore

DEFAULT_MIN_RETRIEVAL_SCORE = 0.35
DEFAULT_MAX_RETRIES = 2


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


class JobMatchState(TypedDict):
    raw_jd: str
    parsed_jd: ParsedJD | None
    queries: list[str]
    retrieved_chunks: list[RetrievedEvidence]
    reranked_chunks: list[Any]
    retrieval_scores: RetrievalGradeReport | None
    missing_keywords: list[str]
    decision: str
    match_analysis: MatchAnalysisResult | None
    generated_result: GeneratedOutput | None
    faithfulness_report: FaithfulnessReport | None
    report_path: str
    trace_id: str
    logs: list[str]
    retry_count: int
    max_retries: int
    retry_history: list[dict[str, Any]]
    query_rewrite_reason: str
    fallback_reason: str
    tool_trace: list[dict[str, Any]]
    next_action: str
    top_k: int
    profile_dir: str
    output_dir: str
    status: str
    error_message: str


def _initial_state(
    *, raw_jd="", top_k=5, profile_dir="", output_dir="", max_retries=DEFAULT_MAX_RETRIES,
) -> JobMatchState:
    return JobMatchState(
        raw_jd=raw_jd, parsed_jd=None, queries=[], retrieved_chunks=[],
        reranked_chunks=[], retrieval_scores=None, missing_keywords=[],
        decision="continue", match_analysis=None, generated_result=None,
        faithfulness_report=None, report_path="", trace_id=uuid.uuid4().hex[:12],
        logs=[], retry_count=0, max_retries=max_retries, retry_history=[],
        query_rewrite_reason="", fallback_reason="", tool_trace=[], next_action="parse_jd",
        top_k=top_k, profile_dir=profile_dir, output_dir=output_dir,
        status="running", error_message="",
    )


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------

class _WorkflowContext:
    def __init__(
        self,
        jd_parser=None, rag_pipeline=None, match_agent=None, build_agent=None,
        hybrid_retriever=None, reranker=None, faithfulness_checker=None,
        cross_encoder_reranker=None,
    ):
        self.jd_parser = jd_parser or JDParserAgent()
        self.rag_pipeline = rag_pipeline or RAGPipeline()
        self.rag_retriever = RAGRetrieveAgent(pipeline=self.rag_pipeline)
        self.match_agent = match_agent or MatchAnalysisAgent()
        self.build_agent = build_agent or BuildAgent()
        self.hybrid_retriever = hybrid_retriever
        self.reranker = reranker or LightweightReranker(top_k=5)
        self.cross_encoder_reranker = cross_encoder_reranker
        self.faithfulness_checker = faithfulness_checker or FaithfulnessChecker()


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def parse_jd_node(state, *, ctx):
    _log(state, "parse_jd_node")
    parsed = ctx.jd_parser.parse(state["raw_jd"])
    state["logs"].append(f"parse_jd: title={parsed.job_title}, direction={parsed.job_direction}")
    tr = _record_tool_call(state, "parse_jd", input_summary=f"jd {len(state['raw_jd'])} chars",
                           output_summary=f"title={parsed.job_title}, direction={parsed.job_direction}")
    return {"parsed_jd": parsed, "next_action": "rewrite_query", "tool_trace": tr["tool_trace"]}


def rewrite_query_node(state, *, ctx):
    _log(state, "rewrite_query_node")
    pj = state["parsed_jd"]
    if pj is None:
        return {"queries": [], "next_action": "retrieve_context", "retry_count": state.get("retry_count", 0)}

    retry_count = state.get("retry_count", 0)
    query = ctx.rag_retriever.build_query_from_parsed_jd(pj)
    missing = state.get("missing_keywords", [])

    if retry_count > 0 and missing:
        query = f"{query} {' '.join(missing[:5])}"
        reason = f"retry #{retry_count}; missing: {', '.join(missing[:5])}"
    else:
        reason = "initial query from parsed JD"

    state["logs"].append(f"rewrite_query: query='{query[:120]}'")
    tr = _record_tool_call(state, "rewrite_query", input_summary=f"retry={retry_count}", output_summary=query[:100])
    return {
        "queries": [query], "retry_count": retry_count + 1,
        "query_rewrite_reason": reason, "next_action": "retrieve_context",
        "tool_trace": tr["tool_trace"],
    }


def retrieve_context_node(state, *, ctx):
    _log(state, "retrieve_context_node")
    queries = state.get("queries", [])
    if not queries or not queries[0]:
        return {"retrieved_chunks": [], "next_action": "rerank"}

    query = queries[-1]
    top_k = state["top_k"]
    if state["profile_dir"]:
        ctx.rag_pipeline.build_index(state["profile_dir"])

    # Use HybridRetriever if available, else fallback to pipeline
    hr = ctx.hybrid_retriever
    if hr is not None:
        from career_agent.domain.schemas import ParsedJD as DomainParsedJD
        pj = state.get("parsed_jd")
        domain_pj = None
        if pj is not None:
            domain_pj = DomainParsedJD(
                job_title=pj.job_title, job_direction=pj.job_direction,
                hard_skills=list(pj.hard_skills), keywords=list(pj.keywords),
            )
        domain_chunks = hr.retrieve(query, top_k=top_k, parsed_jd=domain_pj)
        # Convert domain RetrievedChunk → RetrievedEvidence for downstream compatibility
        evidence_list = []
        for dc in domain_chunks:
            evidence_list.append(RetrievedEvidence(
                evidence_id=f"hybrid-{dc.chunk_id}", chunk_id=dc.chunk_id,
                title=dc.source.split("/")[-1] if dc.source else "",
                content=dc.content, score=dc.final_hybrid_score,
                source_path=dc.source,
                matched_keywords=list(dc.matched_skills),
                metadata={"keyword_score": dc.keyword_score, "vector_score": dc.vector_score,
                          "metadata_score": dc.metadata_score, "final_hybrid_score": dc.final_hybrid_score},
            ))
        state["logs"].append(f"retrieve_context (hybrid): {len(evidence_list)} chunks")
        tr = _record_tool_call(state, "retrieve_profile", input_summary=query[:80], output_summary=f"{len(evidence_list)} chunks (hybrid)")
        return {"retrieved_chunks": evidence_list, "next_action": "rerank", "tool_trace": tr["tool_trace"]}

    chunks = ctx.rag_pipeline.retrieve(query, top_k=top_k)
    state["logs"].append(f"retrieve_context: {len(chunks)} chunks")
    tr = _record_tool_call(state, "retrieve_profile", input_summary=query[:80], output_summary=f"{len(chunks)} chunks")
    return {"retrieved_chunks": chunks, "next_action": "rerank", "tool_trace": tr["tool_trace"]}


def rerank_node(state, *, ctx):
    _log(state, "rerank_node")
    chunks = state.get("retrieved_chunks", [])
    if not chunks:
        return {"reranked_chunks": [], "next_action": "grade_retrieval"}

    query = state.get("queries", [""])[-1] if state.get("queries") else ""

    # --- try Cross-Encoder Reranker first ---
    ce = ctx.cross_encoder_reranker
    if ce is not None:
        try:
            ce_results = ce.rerank(query, chunks, top_n=10)
            result = []
            for ev, ce_score in ce_results:
                base_meta = dict(ev.metadata) if isinstance(ev.metadata, dict) else {}
                base_meta.update({"rerank_score": round(ce_score, 4), "reranker": "cross_encoder"})
                result.append(RetrievedEvidence(
                    evidence_id=ev.evidence_id, chunk_id=ev.chunk_id,
                    title=getattr(ev, "title", ""), content=ev.content,
                    score=ce_score, source_path=ev.source_path,
                    matched_keywords=list(getattr(ev, "matched_keywords", [])),
                    metadata=base_meta,
                ))
            state["logs"].append(f"rerank (cross-encoder): {len(result)} chunks (from {len(chunks)})")
            tr = _record_tool_call(state, "rerank_chunks", input_summary=f"{len(chunks)} chunks",
                                   output_summary=f"{len(result)} reranked (cross-encoder)")
            return {"reranked_chunks": result, "retrieved_chunks": result,
                    "next_action": "grade_retrieval", "tool_trace": tr["tool_trace"]}
        except Exception:
            pass  # fall through to lightweight reranker

    # --- fallback to rule-based LightweightReranker ---
    from career_agent.domain.schemas import RetrievedChunk as DomainChunk
    domain_chunks = []
    for ev in chunks:
        kw_score = ev.metadata.get("keyword_score", ev.score) if isinstance(ev.metadata, dict) else ev.score
        vec_score = ev.metadata.get("vector_score", 0.0) if isinstance(ev.metadata, dict) else 0.0
        domain_chunks.append(DomainChunk(
            chunk_id=ev.chunk_id, source=ev.source_path, content=ev.content,
            summary=ev.content[:120].replace("\n", " "),
            keyword_score=kw_score, vector_score=vec_score,
            final_hybrid_score=ev.score, matched_skills=list(ev.matched_keywords),
        ))

    pj = state.get("parsed_jd")
    jd_skills = set()
    if pj is not None:
        for s in pj.hard_skills + pj.keywords:
            if s.strip():
                jd_skills.add(s.strip().lower())

    reranked = ctx.reranker.rerank(domain_chunks, jd_skills=jd_skills if jd_skills else None)

    result = []
    for dc, orig_ev in zip(reranked, chunks):
        base_meta = dict(orig_ev.metadata) if isinstance(orig_ev.metadata, dict) else {}
        base_meta.update({
            "rerank_score": dc.rerank_score,
            "rerank_reason": dc.rerank_reason,
            "final_hybrid_score": dc.final_hybrid_score,
            "keyword_score": dc.keyword_score,
            "vector_score": dc.vector_score,
            "reranker": "lightweight",
        })
        result.append(RetrievedEvidence(
            evidence_id=f"rerank-{dc.chunk_id}", chunk_id=dc.chunk_id,
            title=dc.source.split("/")[-1] if dc.source else "",
            content=dc.content, score=dc.rerank_score,
            source_path=dc.source,
            matched_keywords=list(dc.matched_skills),
            metadata=base_meta,
        ))

    state["logs"].append(f"rerank (lightweight): {len(result)} chunks (from {len(chunks)})")
    tr = _record_tool_call(state, "rerank_chunks", input_summary=f"{len(chunks)} chunks",
                           output_summary=f"{len(result)} reranked (lightweight)")
    return {"reranked_chunks": result, "retrieved_chunks": result,
            "next_action": "grade_retrieval", "tool_trace": tr["tool_trace"]}


def grade_retrieval_node(state, *, ctx):  # noqa: ARG001
    _log(state, "grade_retrieval_node")
    queries = state.get("queries", [])
    query = queries[-1] if queries else ""
    chunks = state.get("retrieved_chunks", [])
    top_k = state["top_k"]
    retry_count = state.get("retry_count", 0)

    report = grade_retrieval(query=query, parsed_jd=state["parsed_jd"], evidence=chunks, top_k=top_k)
    missing = _collect_missing_keywords(report, state["parsed_jd"])
    total_score = report.metadata.get("total_score", 0)
    decision = _decide_from_grade(report, total_score, retry_count, state.get("max_retries", DEFAULT_MAX_RETRIES))

    history = list(state.get("retry_history", []))
    history.append({"round": retry_count if retry_count > 0 else 1, "query": query,
                    "top_k": top_k, "evidence_count": report.evidence_count,
                    "total_score": total_score, "grade": report.grade,
                    "decision": decision, "missing_keywords": list(missing)})

    state["logs"].append(f"grade_retrieval: round={history[-1]['round']}, grade={report.grade}, "
                         f"score={total_score:.2f}, decision={decision}")
    tr = _record_tool_call(state, "grade_retrieval", input_summary=f"{len(chunks)} evidence", output_summary=f"grade={report.grade} score={total_score:.2f}")
    return {"retrieval_scores": report, "missing_keywords": missing,
            "decision": decision, "retry_history": history, "next_action": decision,
            "tool_trace": tr["tool_trace"]}


def analyze_match_node(state, *, ctx):
    _log(state, "analyze_match_node")
    pj, chunks = state["parsed_jd"], state.get("retrieved_chunks", [])
    if pj is None:
        return {"match_analysis": None, "next_action": "build_output"}
    result = ctx.match_agent.analyze(pj, chunks)
    return {"match_analysis": result, "next_action": "build_output"}


def build_output_node(state, *, ctx):
    _log(state, "build_output_node")
    pj = state["parsed_jd"] or ParsedJD()
    chunks = state.get("retrieved_chunks", [])
    analysis = state.get("match_analysis") or MatchAnalysisResult()
    result = ctx.build_agent.build(pj, chunks, analysis)
    return {"generated_result": result, "next_action": "check_faithfulness"}


def check_faithfulness_node(state, *, ctx):
    _log(state, "check_faithfulness_node")
    gr = state.get("generated_result")
    if gr is None:
        return {"faithfulness_report": None, "next_action": "write_report"}

    # Build real Evidence from retrieved chunks
    chunks = state.get("retrieved_chunks", [])
    chunk_map = {}
    for ev in chunks:
        cid = ev.chunk_id
        # Also index by evidence_id
        chunk_map[ev.evidence_id] = ev
        chunk_map[cid] = ev

    evidences = []
    for ref in gr.evidence_refs:
        cv = chunk_map.get(ref)
        if cv is not None:
            evidences.append(Evidence(
                evidence_id=ref, chunk_id=cv.chunk_id,
                source=cv.source_path, content=cv.content,
                confidence=max(0.0, min(1.0, getattr(cv, 'score', 0.5) or 0.5)),
            ))
        else:
            evidences.append(Evidence(
                evidence_id=ref, chunk_id=ref, source="", content="",
            ))

    bullets = [GeneratedBullet(
        text=b, evidence_ids=list(gr.evidence_refs),
        source_paths=[ev.source for ev in evidences if ev.source],
        confidence=0.8,
    ) for b in gr.resume_bullets]

    report = ctx.faithfulness_checker.check(bullets, evidences)
    state["logs"].append(f"faithfulness: score={report.faithfulness_score:.2f}, "
                         f"decision={report.decision}, "
                         f"unsupported={len(report.unsupported_claims)}")
    tr = _record_tool_call(state, "check_faithfulness", input_summary=f"{len(bullets)} bullets", output_summary=f"score={report.faithfulness_score:.2f} {report.decision}")
    return {"faithfulness_report": report, "next_action": "write_report", "tool_trace": tr["tool_trace"]}


def write_report_node(state, *, ctx):  # noqa: ARG001
    _log(state, "write_report_node")
    output_dir = Path(state["output_dir"]) if state["output_dir"] else Path("outputs/demo")
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"langgraph_result_{state['trace_id']}.md"
    state["status"] = "completed"
    state["next_action"] = "end"
    report_path.write_text(_render_langgraph_report(state), encoding="utf-8")

    # Also write diagnostics JSON
    from career_agent.evaluation.diagnostics import write_diagnostics
    diag_path = write_diagnostics(dict(state), output_dir=str(output_dir.parent / "diagnostics"))
    state["logs"].append(f"write_report: {report_path}, diagnostics: {diag_path}")

    tr = _record_tool_call(state, "write_report", output_summary=str(report_path))
    tr2 = _record_tool_call(state, "write_diagnostics", output_summary=str(diag_path))
    merged_trace = list(tr.get("tool_trace", []))
    return {"report_path": str(report_path), "status": "completed", "next_action": "end", "tool_trace": merged_trace}


# ---------------------------------------------------------------------------
# Routing & fallback
# ---------------------------------------------------------------------------

def _decide_from_grade(report, total_score=0.0, retry_count=0, max_retries=DEFAULT_MAX_RETRIES):
    if retry_count >= max_retries:
        return "fallback"
    if total_score >= DEFAULT_MIN_RETRIEVAL_SCORE:
        return "continue"
    if report.grade in (GRADE_FAILED, "weak"):
        return "retry"
    return "continue"


def _route_after_grading(state, min_score=DEFAULT_MIN_RETRIEVAL_SCORE, max_retries=DEFAULT_MAX_RETRIES):
    decision = state.get("decision", "continue")
    if decision == "fallback":
        return "fallback"
    if decision == "retry":
        return "rewrite_query"
    rs = state.get("retrieval_scores")
    if rs is not None:
        total = rs.metadata.get("total_score", 0)
        retry_count = state.get("retry_count", 0)
        if total < min_score and retry_count < max_retries:
            return "rewrite_query"
        if retry_count >= max_retries and total < min_score:
            return "fallback"
    return "analyze_match"


def fallback_node(state, *, ctx):  # noqa: ARG001
    _log(state, "fallback_node")
    missing = state.get("missing_keywords", [])
    reason = (f"经过 {state.get('retry_count', 0)} 轮检索（最多 {state.get('max_retries', DEFAULT_MAX_RETRIES)} 轮），"
              f"检索质量未达到阈值 {DEFAULT_MIN_RETRIEVAL_SCORE}。")
    if missing:
        reason += f" 未覆盖技能：{', '.join(missing[:10])}。"

    output_dir = Path(state["output_dir"]) if state["output_dir"] else Path("outputs/demo")
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"langgraph_fallback_{state['trace_id']}.md"
    lines = ["# LangGraph — 检索未达标（Fallback）", "",
             f"- Trace ID: `{state['trace_id']}`", f"- Reason: {reason}", "",
             "## 建议", "当前用户资料库可能不足以覆盖该岗位的核心技能要求。",
             "建议补充以下材料：", ""]
    for kw in missing[:10]:
        lines.append(f"- {kw} 相关项目经历或技能说明")
    lines.append(""); lines.append("补充资料后重新运行即可获得更准确的匹配分析。")
    report_path.write_text("\n".join(lines), encoding="utf-8")

    return {"decision": "fallback", "fallback_reason": reason,
            "report_path": str(report_path), "status": "completed", "next_action": "end"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log(state, node):
    state.setdefault("logs", []).append(f"[{datetime.now(timezone.utc).isoformat()}] {node}")


def _record_tool_call(state, tool_name, input_summary="", output_summary="", success=True, error="", duration_ms=0.0):
    """Record a ToolCallTrace entry. Returns ``{"tool_trace": [...]}`` for LangGraph merging."""
    trace: list[dict[str, Any]] = list(state.get("tool_trace", []))
    trace.append({"tool_name": tool_name, "input_summary": input_summary,
                  "output_summary": output_summary, "duration_ms": duration_ms,
                  "success": success, "error": error, "state_changes": []})
    return {"tool_trace": trace}


def _collect_missing_keywords(report, parsed_jd):
    if parsed_jd is None:
        return []
    all_matched = set()
    for ev_summary in report.evidence_summaries:
        for kw in ev_summary.get("matched_keywords", []):
            all_matched.add(kw.lower())
    expected = set(kw.lower() for kw in (parsed_jd.hard_skills + parsed_jd.bonus_skills + parsed_jd.keywords))
    return sorted(expected - all_matched)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _render_langgraph_report(state):
    L = [].append
    lines = []

    def L(text): lines.append(text)  # noqa: E741

    L("# LangGraph Agentic RAG — 完整诊断报告")
    L("")
    L(f"- Trace: `{state['trace_id']}` | Status: {state['status']} | Decision: {state['decision']} | Retry: {state['retry_count']}")
    L("")

    pj = state["parsed_jd"]
    L("## 1. JD 解析")
    if pj is not None:
        L(f"- 标题: {pj.job_title}, 方向: {pj.job_direction}")
        L(f"- 硬技能: {', '.join(pj.hard_skills[:10]) if pj.hard_skills else '无'}")
    L("")

    L("## 2. Query Rewrite History")
    rh = state.get("retry_history", [])
    if rh:
        L("| Round | Query | Score | Grade | Decision |")
        L("|-------|-------|-------|-------|----------|")
        for e in rh:
            L(f"| {e['round']} | `{str(e.get('query',''))[:60]}` | {e.get('total_score',0):.2f} | {e.get('grade','')} | {e.get('decision','')} |")
    L("")

    L("## 3. Hybrid Retrieval")
    chunks = state.get("retrieved_chunks", [])
    L(f"共 {len(chunks)} 条:")
    for i, ev in enumerate(chunks, 1):
        meta = ev.metadata if isinstance(ev.metadata, dict) else {}
        kw = meta.get("keyword_score", "-")
        vec = meta.get("vector_score", "-")
        hyb = meta.get("final_hybrid_score", ev.score)
        L(f"  {i}. `{ev.source_path.split('/')[-1] if ev.source_path else '?'}` "
          f"kw={kw} vec={vec} hybrid={hyb:.2f} rerank={meta.get('rerank_score', '-')}")
    L("")

    L("## 4. Reranker")
    for i, ev in enumerate(chunks, 1):
        meta = ev.metadata if isinstance(ev.metadata, dict) else {}
        reason = meta.get("rerank_reason", "")
        if reason:
            L(f"  {i}. {reason}")
    if not any((ev.metadata or {}).get("rerank_reason") if isinstance(ev.metadata, dict) else False for ev in chunks):
        L("  (无 rerank 数据)")
    L("")

    L("## 5. Retrieval Grading")
    rs = state.get("retrieval_scores")
    if rs is not None:
        L(f"- Grade: **{rs.grade}** (total={rs.metadata.get('total_score', 0):.2f})")
        L(f"- Evidence: {rs.evidence_count}/{rs.top_k}, Coverage: {rs.keyword_coverage:.2f}, Diversity: {rs.source_diversity}")
        for item in rs.items:
            L(f"  - {'✅' if item.passed else '❌'} {item.name}: {item.message}")
    L("")

    L("## 6. Missing Keywords")
    mk = state.get("missing_keywords", [])
    L(", ".join(mk[:15]) if mk else "（全部覆盖）")
    L("")

    fr = state.get("fallback_reason", "")
    if fr:
        L(f"## 7. Fallback: {fr}")
        L("")

    L("## 8. Match Analysis")
    ma = state.get("match_analysis")
    if ma is not None:
        for s in ma.strengths[:5]:
            L(f"- ✅ {s}")
        for w in ma.weaknesses[:5]:
            L(f"- ⚠️ {w}")
    L("")

    L("## 9. Generated Output")
    gr = state.get("generated_result")
    if gr is not None:
        for b in gr.resume_bullets[:5]:
            L(f"- {b}")
        L(f"\n> {gr.communication_message}")
    L("")

    L("## 10. Faithfulness Check")
    frp = state.get("faithfulness_report")
    if frp is not None:
        L(f"- Score: {frp.faithfulness_score:.2f}, Decision: {frp.decision}")
        if frp.unsupported_claims:
            L(f"- Unsupported claims: {len(frp.unsupported_claims)}")
    L("")

    L(f"## 11. Report: `{state.get('report_path', '')}`")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def create_langgraph_workflow(
    jd_parser=None, rag_pipeline=None, match_agent=None, build_agent=None,
    profile_dir="", hybrid_retriever=None, reranker=None, faithfulness_checker=None,
    cross_encoder_reranker=None,
):
    ctx = _WorkflowContext(
        jd_parser=jd_parser, rag_pipeline=rag_pipeline,
        match_agent=match_agent, build_agent=build_agent,
        hybrid_retriever=hybrid_retriever, reranker=reranker,
        faithfulness_checker=faithfulness_checker,
        cross_encoder_reranker=cross_encoder_reranker,
    )
    if profile_dir:
        ctx.rag_pipeline.build_index(profile_dir)
        # Also build hybrid retriever index if available
        if ctx.hybrid_retriever is not None:
            # Build keyword store index too
            pass  # HybridRetriever delegates to its own retrievers

    graph = StateGraph(JobMatchState)

    for name, fn in [
        ("parse_jd", parse_jd_node), ("rewrite_query", rewrite_query_node),
        ("retrieve_context", retrieve_context_node), ("rerank", rerank_node),
        ("grade_retrieval", grade_retrieval_node), ("analyze_match", analyze_match_node),
        ("build_output", build_output_node), ("check_faithfulness", check_faithfulness_node),
        ("write_report", write_report_node), ("fallback", fallback_node),
    ]:
        graph.add_node(name, lambda s, f=fn: f(s, ctx=ctx))

    graph.add_edge(START, "parse_jd")
    graph.add_edge("parse_jd", "rewrite_query")
    graph.add_edge("rewrite_query", "retrieve_context")
    graph.add_edge("retrieve_context", "rerank")
    graph.add_edge("rerank", "grade_retrieval")

    graph.add_conditional_edges(
        "grade_retrieval",
        lambda s: _route_after_grading(s, DEFAULT_MIN_RETRIEVAL_SCORE, DEFAULT_MAX_RETRIES),
        {"analyze_match": "analyze_match", "rewrite_query": "rewrite_query", "fallback": "fallback"},
    )

    graph.add_edge("analyze_match", "build_output")
    graph.add_edge("build_output", "check_faithfulness")
    graph.add_edge("check_faithfulness", "write_report")
    graph.add_edge("write_report", END)
    graph.add_edge("fallback", END)

    return graph.compile()


def run_langgraph_workflow(
    raw_jd="", *, top_k=5, profile_dir="", output_dir="outputs/demo",
    jd_parser=None, rag_pipeline=None, match_agent=None, build_agent=None,
):
    from career_agent.core.settings import Settings

    _settings = Settings()
    # Auto-build HybridRetriever if embedding API key available
    hr = None
    if _settings.embedding.api_key:
        try:
            kw_store = MemoryVectorStore()
            emb_provider = QwenEmbeddingProvider()
            emb_store = EmbeddingVectorStore(emb_provider)
            hr = HybridRetriever(keyword_retriever=kw_store.search, embedding_retriever=emb_store.search)
            # Pre-index into keyword store
            if profile_dir:
                from career_agent.rag.loaders.markdown_loader import MarkdownProfileLoader
                from career_agent.rag.chunking.text_chunker import TextChunker
                loader, chunker = MarkdownProfileLoader(), TextChunker()
                docs = loader.load_directory(profile_dir)
                chunks = chunker.chunk_documents(docs)
                kw_store.add_chunks(chunks)
                emb_store.add_chunks(chunks)
        except Exception:
            hr = None

    # CrossEncoderReranker for ML-enhanced reranking (loaded by default).
    # Set DISABLE_ML_RERANKER=1 to skip (lightweight mode / testing).
    import os as _os
    ce_reranker = None
    if not _os.environ.get("DISABLE_ML_RERANKER"):
        try:
            from career_agent.rag.reranker import CrossEncoderReranker
            ce_reranker = CrossEncoderReranker(device="cpu")
        except Exception:
            pass

    app = create_langgraph_workflow(
        jd_parser=jd_parser, rag_pipeline=rag_pipeline,
        match_agent=match_agent, build_agent=build_agent,
        profile_dir=profile_dir, hybrid_retriever=hr,
        cross_encoder_reranker=ce_reranker,
    )
    initial = _initial_state(raw_jd=raw_jd, top_k=top_k,
                             profile_dir=str(profile_dir), output_dir=str(output_dir))
    return app.invoke(initial)


def run_langgraph_workflow_with_tools(
    raw_jd="", *, top_k=5, profile_dir="", output_dir="outputs/demo",
) -> dict[str, Any]:
    """Run via ToolRegistry + ControlledPlanner with full tool-trace recording."""
    import time as _time
    from career_agent.tools.registry import create_standard_registry
    from career_agent.tools.planner import ControlledPlanner

    reg = create_standard_registry()
    planner = ControlledPlanner()
    state: dict[str, Any] = {
        "raw_jd": raw_jd, "parsed_jd": None, "queries": [],
        "retrieved_chunks": [], "reranked_chunks": [],
        "retrieval_scores": None, "missing_keywords": [],
        "decision": "continue", "match_analysis": None,
        "generated_result": None, "faithfulness_report": None,
        "report_path": "", "diagnostics_path": "",
        "retry_count": 0, "max_retries": 2,
        "top_k": top_k, "profile_dir": str(profile_dir),
        "output_dir": str(output_dir),
        "trace_id": uuid.uuid4().hex[:12],
        "tool_trace": [], "logs": [], "status": "running",
    }

    _STATE_KEYS = {
        "parsed_jd", "queries", "retrieved_chunks", "reranked_chunks",
        "retrieval_scores", "match_analysis", "generated_result",
        "faithfulness_report", "report_path", "diagnostics_path",
        "retry_count", "decision", "fallback_reason",
    }

    for _ in range(20):
        decision = planner.decide(state)
        if decision.next_tool == "done":
            state["status"] = "completed"
            break
        kwargs = {}
        tn = decision.next_tool
        if tn == "parse_jd": kwargs["raw_jd"] = state.get("raw_jd", "")
        elif tn in ("plan_queries",): kwargs["parsed_jd"] = state.get("parsed_jd")
        elif tn == "rewrite_query":
            kwargs["parsed_jd"] = state.get("parsed_jd"); kwargs["missing_keywords"] = state.get("missing_keywords", [])
            kwargs["previous_query"] = state["queries"][-1] if state.get("queries") else ""
            kwargs["retry_count"] = state.get("retry_count", 0)
        elif tn == "retrieve_profile":
            kwargs["queries"] = state.get("queries", []); kwargs["top_k"] = state.get("top_k", 5)
            kwargs["profile_dir"] = state.get("profile_dir", "")
        elif tn == "rerank_chunks":
            kwargs["retrieved_chunks"] = state.get("retrieved_chunks", []); kwargs["parsed_jd"] = state.get("parsed_jd")
        elif tn == "grade_retrieval":
            kwargs["query"] = state["queries"][-1] if state.get("queries") else ""
            kwargs["evidence"] = state.get("retrieved_chunks", []); kwargs["parsed_jd"] = state.get("parsed_jd")
        elif tn in ("analyze_match",):
            kwargs["parsed_jd"] = state.get("parsed_jd"); kwargs["retrieved_chunks"] = state.get("retrieved_chunks", [])
        elif tn == "generate_grounded_answer":
            kwargs["parsed_jd"] = state.get("parsed_jd"); kwargs["retrieved_chunks"] = state.get("retrieved_chunks", [])
            kwargs["match_analysis"] = state.get("match_analysis")
        elif tn == "check_faithfulness":
            kwargs["generated_result"] = state.get("generated_result"); kwargs["retrieved_chunks"] = state.get("retrieved_chunks", [])
        elif tn == "fallback":
            kwargs["missing_keywords"] = state.get("missing_keywords", [])
            kwargs["retry_count"] = state.get("retry_count", 0); kwargs["max_retries"] = 2
            kwargs["output_dir"] = state.get("output_dir", "/tmp")
        elif tn in ("write_report", "write_diagnostics"):
            kwargs["state"] = state; kwargs["output_dir"] = state.get("output_dir", "outputs/demo")
        t0 = _time.perf_counter()
        result = reg.invoke(tn, **kwargs)
        elapsed = (_time.perf_counter() - t0) * 1000
        trace = list(state.get("tool_trace", []))
        trace.append({"tool_name": tn, "input_summary": decision.reason, "output_summary": result.summary,
                       "duration_ms": round(elapsed, 2), "success": result.success, "error": result.error})
        state["tool_trace"] = trace
        if result.success:
            for k in _STATE_KEYS & set(result.output.keys()):
                state[k] = result.output[k]
        state.setdefault("logs", []).append(f"[tool] {tn}: {result.summary}")
    return state
