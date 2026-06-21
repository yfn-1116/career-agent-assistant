"""LangGraph-based job match workflow.

Migrates the existing ``JobMatchWorkflow`` to a LangGraph ``StateGraph``
while reusing all existing agent / service logic without rewriting it.

Node order (linear, this task)::

    parse_jd -> rewrite_query -> retrieve_context -> grade_retrieval
    -> analyze_match -> build_output -> write_report -> END
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
from career_agent.rag.grading import GRADE_FAILED, RetrievalGradeReport, grade_retrieval
from career_agent.rag.pipeline import RAGPipeline
from career_agent.rag.schemas import RetrievedEvidence


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


class JobMatchState(TypedDict):
    """LangGraph state for the job-match workflow."""

    raw_jd: str
    parsed_jd: ParsedJD | None
    queries: list[str]
    retrieved_chunks: list[RetrievedEvidence]
    retrieval_scores: RetrievalGradeReport | None
    missing_keywords: list[str]
    decision: str
    match_analysis: MatchAnalysisResult | None
    generated_result: GeneratedOutput | None
    report_path: str
    trace_id: str
    logs: list[str]
    retry_count: int
    next_action: str
    top_k: int
    profile_dir: str
    output_dir: str
    status: str
    error_message: str


def _initial_state(
    *,
    raw_jd: str = "",
    top_k: int = 5,
    profile_dir: str = "",
    output_dir: str = "",
) -> JobMatchState:
    return JobMatchState(
        raw_jd=raw_jd,
        parsed_jd=None,
        queries=[],
        retrieved_chunks=[],
        retrieval_scores=None,
        missing_keywords=[],
        decision="continue",
        match_analysis=None,
        generated_result=None,
        report_path="",
        trace_id=uuid.uuid4().hex[:12],
        logs=[],
        retry_count=0,
        next_action="parse_jd",
        top_k=top_k,
        profile_dir=profile_dir,
        output_dir=output_dir,
        status="running",
        error_message="",
    )


# ---------------------------------------------------------------------------
# Context passed through nodes via a simple carrier
# ---------------------------------------------------------------------------


class _WorkflowContext:
    """Shared resources created once and threaded through all nodes.

    Not part of the serialisable state — we attach it to the compiled
    graph at construction time and pass it via the *config* kwarg.
    """

    def __init__(
        self,
        jd_parser: JDParserAgent | None = None,
        rag_pipeline: RAGPipeline | None = None,
        match_agent: MatchAnalysisAgent | None = None,
        build_agent: BuildAgent | None = None,
    ) -> None:
        self.jd_parser = jd_parser or JDParserAgent()
        self.rag_pipeline = rag_pipeline or RAGPipeline()
        self.rag_retriever = RAGRetrieveAgent(pipeline=self.rag_pipeline)
        self.match_agent = match_agent or MatchAnalysisAgent()
        self.build_agent = build_agent or BuildAgent()


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def parse_jd_node(state: JobMatchState, *, ctx: _WorkflowContext) -> dict[str, Any]:
    _log(state, "parse_jd_node")
    parsed = ctx.jd_parser.parse(state["raw_jd"])
    state["logs"].append(f"parse_jd: title={parsed.job_title}, direction={parsed.job_direction}")
    return {"parsed_jd": parsed, "next_action": "rewrite_query"}


def rewrite_query_node(state: JobMatchState, *, ctx: _WorkflowContext) -> dict[str, Any]:
    _log(state, "rewrite_query_node")
    pj = state["parsed_jd"]
    if pj is None:
        state["logs"].append("rewrite_query: parsed_jd is None, skipping")
        return {"queries": [], "next_action": "retrieve_context"}
    query = ctx.rag_retriever.build_query_from_parsed_jd(pj)
    state["logs"].append(f"rewrite_query: query='{query[:120]}'")
    return {"queries": [query], "next_action": "retrieve_context"}


def retrieve_context_node(state: JobMatchState, *, ctx: _WorkflowContext) -> dict[str, Any]:
    _log(state, "retrieve_context_node")
    queries = state.get("queries", [])
    if not queries or not queries[0]:
        state["logs"].append("retrieve_context: no queries, returning empty")
        return {"retrieved_chunks": [], "next_action": "grade_retrieval"}

    query = queries[0]
    if state["profile_dir"]:
        ctx.rag_pipeline.build_index(state["profile_dir"])
    chunks = ctx.rag_pipeline.retrieve(query, top_k=state["top_k"])
    state["logs"].append(f"retrieve_context: retrieved {len(chunks)} chunks")
    return {"retrieved_chunks": chunks, "next_action": "grade_retrieval"}


def grade_retrieval_node(state: JobMatchState, *, ctx: _WorkflowContext) -> dict[str, Any]:  # noqa: ARG001
    _log(state, "grade_retrieval_node")
    queries = state.get("queries", [])
    query = queries[0] if queries else ""
    chunks = state.get("retrieved_chunks", [])
    top_k = state["top_k"]

    report = grade_retrieval(
        query=query,
        parsed_jd=state["parsed_jd"],
        evidence=chunks,
        top_k=top_k,
    )

    # Collect missing keywords
    missing = _collect_missing_keywords(report, state["parsed_jd"])
    decision = _decide_from_grade(report)

    state["logs"].append(
        f"grade_retrieval: grade={report.grade}, "
        f"score={report.metadata.get('total_score', 0):.2f}, "
        f"coverage={report.keyword_coverage:.2f}, "
        f"decision={decision}"
    )

    return {
        "retrieval_scores": report,
        "missing_keywords": missing,
        "decision": decision,
        "next_action": "analyze_match",
    }


def analyze_match_node(state: JobMatchState, *, ctx: _WorkflowContext) -> dict[str, Any]:
    _log(state, "analyze_match_node")
    pj = state["parsed_jd"]
    chunks = state.get("retrieved_chunks", [])
    if pj is None:
        state["logs"].append("analyze_match: parsed_jd is None, skipping")
        return {"match_analysis": None, "next_action": "build_output"}
    result = ctx.match_agent.analyze(pj, chunks)
    state["logs"].append(
        f"analyze_match: strengths={len(result.strengths)}, "
        f"weaknesses={len(result.weaknesses)}"
    )
    return {"match_analysis": result, "next_action": "build_output"}


def build_output_node(state: JobMatchState, *, ctx: _WorkflowContext) -> dict[str, Any]:
    _log(state, "build_output_node")
    pj = state["parsed_jd"] or ParsedJD()
    chunks = state.get("retrieved_chunks", [])
    analysis = state.get("match_analysis") or MatchAnalysisResult()
    result = ctx.build_agent.build(pj, chunks, analysis)
    state["logs"].append(
        f"build_output: bullets={len(result.resume_bullets)}, "
        f"refs={len(result.evidence_refs)}"
    )
    return {"generated_result": result, "next_action": "write_report"}


def write_report_node(state: JobMatchState, *, ctx: _WorkflowContext) -> dict[str, Any]:  # noqa: ARG001
    _log(state, "write_report_node")
    output_dir = Path(state["output_dir"]) if state["output_dir"] else Path("outputs/demo")
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"langgraph_result_{state['trace_id']}.md"
    # Set status before rendering so the report shows "completed"
    state["status"] = "completed"
    state["next_action"] = "end"
    report_path.write_text(_render_langgraph_report(state), encoding="utf-8")
    state["logs"].append(f"write_report: {report_path}")
    return {
        "report_path": str(report_path),
        "status": "completed",
        "next_action": "end",
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _log(state: JobMatchState, node: str) -> None:
    state.setdefault("logs", []).append(f"[{datetime.now(timezone.utc).isoformat()}] {node}")


def _collect_missing_keywords(
    report: RetrievalGradeReport, parsed_jd: ParsedJD | None
) -> list[str]:
    if parsed_jd is None:
        return []
    all_matched: set[str] = set()
    for ev_summary in report.evidence_summaries:
        for kw in ev_summary.get("matched_keywords", []):
            all_matched.add(kw.lower())
    expected = set(
        kw.lower()
        for kw in (parsed_jd.hard_skills + parsed_jd.bonus_skills + parsed_jd.keywords)
    )
    return sorted(expected - all_matched)


def _decide_from_grade(report: RetrievalGradeReport) -> str:
    if report.grade == GRADE_FAILED:
        return "retry"
    if report.grade == "weak":
        return "retry"  # reserved for future retry loop
    return "continue"


def _render_langgraph_report(state: JobMatchState) -> str:
    lines: list[str] = []
    L = lines.append  # noqa: E741

    L("# LangGraph Job Match Workflow 结果")
    L("")
    L(f"- Trace ID: `{state['trace_id']}`")
    L(f"- Status: {state['status']}")
    L(f"- Decision: {state['decision']}")
    L(f"- Retry Count: {state['retry_count']}")
    L(f"- Next Action: {state['next_action']}")
    L("")

    # --- Parsed JD ---
    pj = state["parsed_jd"]
    L("## 1. Parsed JD")
    if pj is not None:
        L(f"- 岗位标题：{pj.job_title or '（未识别）'}")
        L(f"- 岗位方向：{pj.job_direction}")
        L(f"- 硬技能：{', '.join(pj.hard_skills) if pj.hard_skills else '（无）'}")
        L(f"- 加分技能：{', '.join(pj.bonus_skills) if pj.bonus_skills else '（无）'}")
        L(f"- 关键词：{', '.join(pj.keywords) if pj.keywords else '（无）'}")
    else:
        L("（无结果）")
    L("")

    # --- Rewritten Queries ---
    L("## 2. Rewritten Queries")
    for i, q in enumerate(state.get("queries", []), 1):
        L(f"- [{i}] `{q}`")
    if not state.get("queries"):
        L("（无）")
    L("")

    # --- Retrieved Chunks ---
    L("## 3. Retrieved Chunks")
    L(f"共 {len(state.get('retrieved_chunks', []))} 条：")
    for i, ev in enumerate(state.get("retrieved_chunks", []), 1):
        L(f"- [{i}] {ev.title or ev.evidence_id} `score={ev.score:.2f}` `source={ev.source_path}`")
    L("")

    # --- Retrieval Scores ---
    L("## 4. Retrieval Scores")
    rs = state.get("retrieval_scores")
    if rs is not None:
        L(f"- Grade: **{rs.grade}** (total_score={rs.metadata.get('total_score', rs.average_score):.2f})")
        L(f"- Evidence Count: {rs.evidence_count}/{rs.top_k}")
        L(f"- Average Score: {rs.average_score:.2f}")
        L(f"- Keyword Coverage: {rs.keyword_coverage:.2f}")
        L(f"- Source Diversity: {rs.source_diversity}")
        for item in rs.items:
            L(f"  - {item.name}: {'✅' if item.passed else '❌'} {item.message}")
    else:
        L("（无）")
    L("")

    # --- Missing Keywords ---
    L("## 5. Missing Keywords")
    mk = state.get("missing_keywords", [])
    if mk:
        L(", ".join(mk))
    else:
        L("（全部覆盖）")
    L("")

    # --- Decision ---
    L("## 6. Decision")
    L(f"**{state.get('decision', 'N/A')}**")
    L("")

    # --- Match Analysis ---
    ma = state.get("match_analysis")
    L("## 7. Match Analysis")
    if ma is not None:
        L("### Strengths")
        for s in ma.strengths:
            L(f"- {s}")
        L("### Weaknesses")
        for w in ma.weaknesses:
            L(f"- {w}")
        L("### Suggestions")
        for s in ma.suggestions:
            L(f"- {s}")
    else:
        L("（无）")
    L("")

    # --- Generated Result ---
    gr = state.get("generated_result")
    L("## 8. Generated Result")
    if gr is not None:
        L("### Resume Bullets")
        for b in gr.resume_bullets:
            L(f"- {b}")
        L("### Communication")
        L(gr.communication_message)
        L("### Summary")
        L(gr.summary)
    else:
        L("（无）")
    L("")

    # --- Logs ---
    L("## 9. Execution Logs")
    for log_entry in state.get("logs", []):
        L(f"- {log_entry}")
    L("")

    L("## 10. Report Path")
    L(f"`{state.get('report_path', '')}`")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------


def create_langgraph_workflow(
    jd_parser: JDParserAgent | None = None,
    rag_pipeline: RAGPipeline | None = None,
    match_agent: MatchAnalysisAgent | None = None,
    build_agent: BuildAgent | None = None,
    profile_dir: str | Path = "",
) -> Any:
    """Build and compile a LangGraph ``StateGraph`` for the job-match flow.

    Returns a compiled graph ready for ``.invoke(initial_state)``.
    """
    ctx = _WorkflowContext(
        jd_parser=jd_parser,
        rag_pipeline=rag_pipeline,
        match_agent=match_agent,
        build_agent=build_agent,
    )
    if profile_dir:
        ctx.rag_pipeline.build_index(profile_dir)

    graph = StateGraph(JobMatchState)

    # Register nodes — lambda wraps to inject *ctx*
    graph.add_node("parse_jd", lambda s: parse_jd_node(s, ctx=ctx))
    graph.add_node("rewrite_query", lambda s: rewrite_query_node(s, ctx=ctx))
    graph.add_node("retrieve_context", lambda s: retrieve_context_node(s, ctx=ctx))
    graph.add_node("grade_retrieval", lambda s: grade_retrieval_node(s, ctx=ctx))
    graph.add_node("analyze_match", lambda s: analyze_match_node(s, ctx=ctx))
    graph.add_node("build_output", lambda s: build_output_node(s, ctx=ctx))
    graph.add_node("write_report", lambda s: write_report_node(s, ctx=ctx))

    # Linear edges
    graph.add_edge(START, "parse_jd")
    graph.add_edge("parse_jd", "rewrite_query")
    graph.add_edge("rewrite_query", "retrieve_context")
    graph.add_edge("retrieve_context", "grade_retrieval")
    graph.add_edge("grade_retrieval", "analyze_match")
    graph.add_edge("analyze_match", "build_output")
    graph.add_edge("build_output", "write_report")
    graph.add_edge("write_report", END)

    return graph.compile()


# Convenience runner
def run_langgraph_workflow(
    raw_jd: str,
    *,
    top_k: int = 5,
    profile_dir: str | Path = "",
    output_dir: str | Path = "outputs/demo",
    jd_parser: JDParserAgent | None = None,
    rag_pipeline: RAGPipeline | None = None,
    match_agent: MatchAnalysisAgent | None = None,
    build_agent: BuildAgent | None = None,
) -> JobMatchState:
    """Run the full LangGraph workflow and return the final state."""
    app = create_langgraph_workflow(
        jd_parser=jd_parser,
        rag_pipeline=rag_pipeline,
        match_agent=match_agent,
        build_agent=build_agent,
        profile_dir=profile_dir,
    )
    initial = _initial_state(
        raw_jd=raw_jd,
        top_k=top_k,
        profile_dir=str(profile_dir),
        output_dir=str(output_dir),
    )
    return app.invoke(initial)
