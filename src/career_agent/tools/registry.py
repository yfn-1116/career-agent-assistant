"""Tool Registry — all agent capabilities must be registered here.

No tool may be called outside the registry.
"""

from __future__ import annotations

import time
from typing import Any

from career_agent.tools.base import Tool, ToolResult


class ToolRegistry:
    """Central registry for all agent tools.

    Usage::

        reg = ToolRegistry()
        reg.register(ParseJDTool())
        tool = reg.get("parse_jd")
        result = tool.run(raw_jd="...")
    """

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool.  Raises ValueError on duplicate name."""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        """Get a tool by name.  Raises KeyError if not found."""
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry. Available: {sorted(self._tools.keys())}")
        return self._tools[name]

    def has(self, name: str) -> bool:
        return name in self._tools

    def list_tools(self) -> list[str]:
        return sorted(self._tools.keys())

    @property
    def tool_count(self) -> int:
        return len(self._tools)

    def invoke(self, name: str, **kwargs: Any) -> ToolResult:
        """Invoke a registered tool with timing and error handling.

        Never crashes — returns ``ToolResult(success=False, error=...)``
        on failure.
        """
        try:
            tool = self.get(name)
        except KeyError as e:
            return ToolResult(success=False, error=str(e), summary=f"tool '{name}' not found")

        start = time.perf_counter()
        try:
            result = tool.run(**kwargs)
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            return ToolResult(
                success=False,
                error=f"{type(exc).__name__}: {exc}",
                summary=f"tool '{name}' raised exception",
                duration_ms=round(elapsed, 2),
            )

        elapsed = (time.perf_counter() - start) * 1000
        result.duration_ms = round(elapsed, 2)
        if not result.summary:
            result.summary = f"tool '{name}' {'ok' if result.success else 'failed'}"
        return result


# ---------------------------------------------------------------------------
# Standard tool implementations
# ---------------------------------------------------------------------------


class ParseJDTool(Tool):
    name = "parse_jd"
    description = "Parse a raw job description into structured ParsedJD"

    def run(self, raw_jd: str = "", **kwargs: Any) -> ToolResult:  # noqa: ARG002
        from career_agent.agents.jd_parser import JDParserAgent
        agent = JDParserAgent()
        pj = agent.parse(raw_jd)
        return ToolResult(
            success=True,
            output={"parsed_jd": pj},
            summary=f"parsed JD: title={pj.job_title}, direction={pj.job_direction}",
            state_changes=["parsed_jd"],
        )

    @property
    def safety_notes(self) -> list[str]:
        return ["只解析 JD 文本，不调用外部 API（规则模式）"]


class PlanQueriesTool(Tool):
    name = "plan_queries"
    description = "Generate retrieval queries from a parsed JD"

    def run(self, parsed_jd: Any = None, **kwargs: Any) -> ToolResult:  # noqa: ARG002
        from career_agent.agents.rag_retrieve_agent import RAGRetrieveAgent
        if parsed_jd is None:
            return ToolResult(success=False, error="parsed_jd is required", summary="missing input")
        agent = RAGRetrieveAgent()
        query = agent.build_query_from_parsed_jd(parsed_jd)
        return ToolResult(
            success=True,
            output={"queries": [query]},
            summary=f"planned query: {query[:100]}",
            state_changes=["queries"],
        )

    @property
    def safety_notes(self) -> list[str]:
        return ["查询基于 JD 技能生成，不引入外部信息"]


class RewriteQueryTool(Tool):
    name = "rewrite_query"
    description = "Rewrite a retrieval query targeting missing keywords"

    def run(
        self, parsed_jd: Any = None, missing_keywords: list[str] | None = None,
        previous_query: str = "", retry_count: int = 0, **kwargs: Any,
    ) -> ToolResult:
        from career_agent.agents.rag_retrieve_agent import RAGRetrieveAgent
        if parsed_jd is None:
            return ToolResult(success=False, error="parsed_jd is required", summary="missing input")
        agent = RAGRetrieveAgent()
        base = agent.build_query_from_parsed_jd(parsed_jd)
        missing = missing_keywords or []
        query = f"{base} {' '.join(missing[:5])}" if missing else base
        return ToolResult(
            success=True,
            output={"queries": [query], "retry_count": retry_count + 1},
            summary=f"rewritten query (retry #{retry_count + 1}): {query[:100]}",
            state_changes=["queries", "retry_count"],
        )


class RetrieveProfileTool(Tool):
    name = "retrieve_profile"
    description = "Retrieve relevant chunks from user profile using Hybrid RAG"

    def run(
        self, queries: list[str] | None = None, top_k: int = 5,
        profile_dir: str = "", **kwargs: Any,
    ) -> ToolResult:
        if not queries or not queries[0]:
            return ToolResult(success=False, error="queries is empty", summary="no queries")
        from career_agent.rag.pipeline import RAGPipeline
        pipeline = RAGPipeline()
        if profile_dir:
            pipeline.build_index(profile_dir)
        chunks = pipeline.retrieve(queries[0], top_k=top_k)
        return ToolResult(
            success=True,
            output={"retrieved_chunks": chunks},
            summary=f"retrieved {len(chunks)} chunks for query: {queries[0][:80]}",
            state_changes=["retrieved_chunks"],
        )

    @property
    def safety_notes(self) -> list[str]:
        return ["只检索用户本地资料库，不访问外部数据"]


class RerankChunksTool(Tool):
    name = "rerank_chunks"
    description = "Re-rank retrieved chunks by quality signals"

    def run(
        self, retrieved_chunks: list[Any] | None = None,
        parsed_jd: Any = None, **kwargs: Any,
    ) -> ToolResult:
        if not retrieved_chunks:
            return ToolResult(success=False, error="retrieved_chunks is empty", summary="no chunks to rerank")
        from career_agent.domain.schemas import RetrievedChunk
        from career_agent.rag.reranker import LightweightReranker

        domain_chunks = []
        for ev in retrieved_chunks:
            domain_chunks.append(RetrievedChunk(
                chunk_id=ev.chunk_id, source=ev.source_path, content=ev.content,
                summary=ev.content[:120], final_hybrid_score=ev.score,
                matched_skills=list(ev.matched_keywords) if ev.matched_keywords else [],
            ))
        jd_skills = set()
        if parsed_jd is not None:
            for s in (parsed_jd.hard_skills + parsed_jd.keywords):
                if s.strip():
                    jd_skills.add(s.strip().lower())
        reranker = LightweightReranker(top_k=len(domain_chunks))
        reranked = reranker.rerank(domain_chunks, jd_skills=jd_skills if jd_skills else None)
        return ToolResult(
            success=True,
            output={"reranked_chunks": reranked},
            summary=f"reranked {len(reranked)} chunks",
            state_changes=["reranked_chunks"],
        )


class GradeRetrievalTool(Tool):
    name = "grade_retrieval"
    description = "Evaluate retrieval quality with 5-dimension scoring"

    def run(
        self, query: str = "", evidence: list[Any] | None = None,
        parsed_jd: Any = None, top_k: int = 5, **kwargs: Any,
    ) -> ToolResult:
        from career_agent.rag.grading import grade_retrieval
        ev = evidence or []
        report = grade_retrieval(query=query, parsed_jd=parsed_jd, evidence=ev, top_k=top_k)
        return ToolResult(
            success=True,
            output={"retrieval_scores": report},
            summary=f"grade={report.grade} score={report.metadata.get('total_score', 0):.2f}",
            state_changes=["retrieval_scores"],
        )


class SelectEvidenceTool(Tool):
    name = "select_evidence"
    description = "Select best evidence items for generation grounding"

    def run(
        self, retrieved_chunks: list[Any] | None = None,
        retrieval_scores: Any = None, **kwargs: Any,
    ) -> ToolResult:
        chunks = retrieved_chunks or []
        selected = []
        for ev in chunks:
            score = getattr(ev, "score", 0)
            if score >= 0.3:  # min threshold
                selected.append({
                    "evidence_id": getattr(ev, "evidence_id", ev.chunk_id),
                    "chunk_id": ev.chunk_id,
                    "source": ev.source_path if hasattr(ev, "source_path") else "",
                    "content": ev.content[:200],
                    "score": score,
                })
        return ToolResult(
            success=True,
            output={"selected_evidence": selected},
            summary=f"selected {len(selected)}/{len(chunks)} evidence items",
            state_changes=["selected_evidence"],
        )


class AnalyzeMatchTool(Tool):
    name = "analyze_match"
    description = "Compare JD requirements against retrieved evidence"

    def run(
        self, parsed_jd: Any = None, retrieved_chunks: list[Any] | None = None, **kwargs: Any,
    ) -> ToolResult:
        from career_agent.agents.match_analysis_agent import MatchAnalysisAgent
        agent = MatchAnalysisAgent()
        result = agent.analyze(parsed_jd, retrieved_chunks or [])
        return ToolResult(
            success=True,
            output={"match_analysis": result},
            summary=f"strengths={len(result.strengths)} weaknesses={len(result.weaknesses)}",
            state_changes=["match_analysis"],
        )


class GenerateGroundedAnswerTool(Tool):
    name = "generate_grounded_answer"
    description = "Generate resume bullets and communication script from evidence"

    def run(
        self, parsed_jd: Any = None, retrieved_chunks: list[Any] | None = None,
        match_analysis: Any = None, **kwargs: Any,
    ) -> ToolResult:
        from career_agent.agents.build_agent import BuildAgent
        from career_agent.agents.state import MatchAnalysisResult, ParsedJD
        agent = BuildAgent()
        pj = parsed_jd or ParsedJD()
        ma = match_analysis or MatchAnalysisResult()
        result = agent.build(pj, retrieved_chunks or [], ma)
        return ToolResult(
            success=True,
            output={"generated_result": result},
            summary=f"bullets={len(result.resume_bullets)} refs={len(result.evidence_refs)}",
            state_changes=["generated_result"],
        )

    @property
    def safety_notes(self) -> list[str]:
        return ["所有声称必须有 evidence_refs 支持", "不编造用户没有的经历"]


class CheckFaithfulnessTool(Tool):
    name = "check_faithfulness"
    description = "Verify generated content is grounded in evidence"

    def run(
        self, generated_result: Any = None, retrieved_chunks: list[Any] | None = None, **kwargs: Any,
    ) -> ToolResult:
        from career_agent.domain.schemas import Evidence, GeneratedBullet
        from career_agent.evaluation.faithfulness import FaithfulnessChecker

        if generated_result is None:
            return ToolResult(success=False, error="generated_result is required", summary="missing input")

        # Build evidence map from retrieved chunks
        chunk_map = {}
        for ev in (retrieved_chunks or []):
            cid = getattr(ev, "chunk_id", "")
            chunk_map[cid] = ev
            if hasattr(ev, "evidence_id"):
                chunk_map[ev.evidence_id] = ev

        refs = getattr(generated_result, "evidence_refs", [])
        evidences = []
        for ref in refs:
            cv = chunk_map.get(ref)
            if cv is not None:
                evidences.append(Evidence(
                    evidence_id=ref, chunk_id=cv.chunk_id,
                    source=getattr(cv, "source_path", ""), content=getattr(cv, "content", ""),
                ))
            else:
                evidences.append(Evidence(evidence_id=ref, chunk_id=ref))

        bullets = [
            GeneratedBullet(text=b, evidence_ids=list(refs))
            for b in getattr(generated_result, "resume_bullets", [])
        ]

        checker = FaithfulnessChecker()
        report = checker.check(bullets, evidences)
        return ToolResult(
            success=True,
            output={"faithfulness_report": report},
            summary=f"score={report.faithfulness_score:.2f} decision={report.decision}",
            state_changes=["faithfulness_report"],
        )

    @property
    def safety_notes(self) -> list[str]:
        return ["检查生成内容是否有证据支持", "score < 0.75 时禁止作为最终输出"]


class FallbackTool(Tool):
    name = "fallback"
    description = "Handle exhausted retries — produce safe output without fabrication"

    def run(
        self, missing_keywords: list[str] | None = None,
        retry_count: int = 0, max_retries: int = 2,
        output_dir: str = "/tmp", **kwargs: Any,
    ) -> ToolResult:
        missing = missing_keywords or []
        reason = (
            f"经过 {retry_count} 轮检索（最多 {max_retries} 轮），检索质量未达标。"
        )
        if missing:
            reason += f" 未覆盖技能：{', '.join(missing[:10])}。"
        return ToolResult(
            success=True,
            output={
                "decision": "fallback",
                "fallback_reason": reason,
                "suggested_inputs": [f"{kw} 相关项目经历或技能说明" for kw in missing[:5]],
                "safe_message": "当前资料不足以支持完整匹配分析，建议补充相关材料。",
                "insufficient_evidence": True,
            },
            summary=f"fallback: {len(missing)} missing keywords",
            state_changes=["decision", "fallback_reason"],
        )

    @property
    def safety_notes(self) -> list[str]:
        return ["绝对不编造用户经历", "诚实告知资料不足", "不生成虚假简历"]


class WriteReportTool(Tool):
    name = "write_report"
    description = "Write the final Markdown diagnostics report"

    def run(self, state: dict[str, Any] | None = None, output_dir: str = "outputs/demo", **kwargs: Any) -> ToolResult:
        from pathlib import Path
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        trace_id = (state or {}).get("trace_id", "unknown")
        path = Path(output_dir) / f"agent_report_{trace_id}.md"
        lines = ["# Agent Run Report", "", f"Trace: `{trace_id}`"]
        path.write_text("\n".join(lines), encoding="utf-8")
        return ToolResult(
            success=True,
            output={"report_path": str(path)},
            summary=f"report written to {path}",
            state_changes=["report_path"],
        )


class WriteDiagnosticsTool(Tool):
    name = "write_diagnostics"
    description = "Write diagnostics JSON for the run"

    def run(self, state: dict[str, Any] | None = None, output_dir: str = "outputs/diagnostics", **kwargs: Any) -> ToolResult:
        from pathlib import Path
        from career_agent.evaluation.diagnostics import write_diagnostics
        path = write_diagnostics(state or {}, output_dir=output_dir)
        return ToolResult(
            success=True,
            output={"diagnostics_path": str(path)},
            summary=f"diagnostics written to {path}",
            state_changes=["diagnostics_path"],
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_standard_registry() -> ToolRegistry:
    """Create a ToolRegistry with all 13 standard tools registered."""
    reg = ToolRegistry()
    for tool_cls in [
        ParseJDTool, PlanQueriesTool, RewriteQueryTool, RetrieveProfileTool,
        RerankChunksTool, GradeRetrievalTool, SelectEvidenceTool,
        AnalyzeMatchTool, GenerateGroundedAnswerTool, CheckFaithfulnessTool,
        FallbackTool, WriteReportTool, WriteDiagnosticsTool,
    ]:
        reg.register(tool_cls())
    return reg
