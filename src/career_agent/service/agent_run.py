"""Unified Agent Run Service — single entry point for all UI/clients.

UI never calls RAG or Agent internals directly.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from career_agent.workflows.langgraph_workflow import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_MIN_RETRIEVAL_SCORE,
    run_langgraph_workflow,
)


@dataclass
class AgentRunRequest:
    """Input to the Agent Run Service."""

    user_message: str = ""
    raw_jd: str = ""
    mode: str = "analyze_job"  # analyze_job / discover_jobs / generate_message / tailor_resume / handle_hr_reply
    profile_scope: str = ""
    hr_message: str = ""  # for handle_hr_reply mode
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentRunResult:
    """Output from the Agent Run Service."""

    trace_id: str = ""
    final_answer: str = ""
    match_summary: dict[str, Any] = field(default_factory=dict)
    match_score: float = 0.0
    recommended_action: str = ""
    generated_bullets: list[str] = field(default_factory=list)
    communication_script: str = ""
    message_draft: dict[str, Any] | None = None
    evidence_sources: list[str] = field(default_factory=list)
    can_write_claims: list[str] = field(default_factory=list)
    cannot_write_claims: list[str] = field(default_factory=list)
    retrieval_grade: str = ""
    retrieval_total_score: float = 0.0
    retry_count: int = 0
    decision: str = ""
    report_path: str = ""
    diagnostics_path: str = ""
    approval_required: bool = False
    application_record_id: str = ""
    status: str = "running"
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentRunService:
    """Run the full Agentic RAG pipeline and return a structured result.

    Parameters
    ----------
    profile_dir : str
        Path to user profile Markdown directory.
    max_retries : int
        Max query rewrite retries (default 2).
    min_score : float
        Min retrieval score to pass (default 0.65).
    """

    def __init__(
        self,
        profile_dir: str = "data/samples/profile",
        max_retries: int = DEFAULT_MAX_RETRIES,
        min_score: float = DEFAULT_MIN_RETRIEVAL_SCORE,
    ) -> None:
        self.profile_dir = profile_dir
        self.max_retries = max_retries
        self.min_score = min_score

    def run(
        self,
        request: AgentRunRequest,
        output_dir: str = "outputs/demo",
    ) -> AgentRunResult:
        """Execute the workflow and return structured result."""
        mode = request.mode

        if mode == "discover_jobs":
            return self._run_discovery(request, output_dir)
        elif mode == "generate_message":
            return self._run_message(request, output_dir)
        elif mode == "handle_hr_reply":
            return self._run_hr_reply(request, output_dir)
        else:
            return self._run_analyze(request, output_dir)

    def _run_analyze(self, request: AgentRunRequest, output_dir: str) -> AgentRunResult:
        """Analyze a single job posting."""
        jd = request.raw_jd or request.user_message
        state = run_langgraph_workflow(
            raw_jd=jd, top_k=5, profile_dir=self.profile_dir, output_dir=output_dir,
        )

        # Build result from state
        warnings: list[str] = []
        if state["decision"] == "fallback":
            warnings.append(
                f"检索未达标 (score < {self.min_score}), 建议补充资料"
            )

        # Build final answer
        final_answer = self._build_final_answer(state, request.mode, warnings)

        # Extract evidence sources
        sources: list[str] = []
        for ev in state.get("retrieved_chunks", []):
            src = getattr(ev, "source_path", "")
            if src and src not in sources:
                sources.append(src)

        # Extract generated bullets
        gr = state.get("generated_result")
        bullets = list(gr.resume_bullets) if gr is not None else []

        # Communication script
        comm = gr.communication_message if gr is not None else ""

        # Retrieval grade
        rs = state.get("retrieval_scores")
        grade = rs.grade if rs is not None else "unknown"
        total = rs.metadata.get("total_score", 0) if rs is not None else 0.0

        from career_agent.matching.scorer import JobMatchScorer
        from career_agent.profile.loader import ProfileLoader
        from career_agent.rag.loaders.markdown_loader import MarkdownProfileLoader
        try:
            p_items = ProfileLoader().load_documents(MarkdownProfileLoader().load_directory(self.profile_dir))
            pj = state.get("parsed_jd")
            scorer = JobMatchScorer()
            match_result = scorer.score(
                pj.job_title if pj else "", pj.hard_skills if pj else [],
                pj.bonus_skills if pj else [], p_items,
            )
            _match_score = match_result.match_score
            _action = match_result.recommended_action
            _matched = match_result.matched_skills
            _missing = match_result.missing_skills
        except Exception:
            _match_score = 0.0; _action = ""; _matched = []; _missing = []

        return AgentRunResult(
            trace_id=state["trace_id"],
            final_answer=final_answer,
            match_score=_match_score,
            recommended_action=_action or decision,
            match_summary={
                "decision": state["decision"],
                "retry_count": state.get("retry_count", 0),
                "missing_keywords": state.get("missing_keywords", []),
                "matched_skills": _matched,
                "missing_skills": _missing,
            },
            generated_bullets=bullets,
            communication_script=comm,
            evidence_sources=sources,
            retrieval_grade=grade,
            retrieval_total_score=total,
            retry_count=state.get("retry_count", 0),
            decision=state["decision"],
            report_path=state.get("report_path", ""),
            status=state["status"],
            warnings=warnings,
        )

    @staticmethod
    def _build_final_answer(
        state: dict,
        mode: str,
        warnings: list[str],
    ) -> str:
        """Build a natural-language final answer from workflow state."""
        pj = state.get("parsed_jd")
        ma = state.get("match_analysis")
        gr = state.get("generated_result")
        rs = state.get("retrieval_scores")
        decision = state.get("decision", "unknown")

        if decision == "fallback":
            return (
                "抱歉，当前用户资料库不足以支持该岗位的完整分析。\n\n"
                f"缺失技能：{', '.join(state.get('missing_keywords', [])[:10])}\n\n"
                "建议补充相关项目经历或技能说明后重新运行。"
            )

        lines = []
        # JD summary
        if pj is not None:
            lines.append(f"岗位 **{pj.job_title or '未识别'}** ({pj.job_direction}方向)")
            if pj.hard_skills:
                lines.append(f"核心要求：{', '.join(pj.hard_skills[:8])}")
        lines.append("")

        # Match
        if ma is not None and ma.strengths:
            lines.append("### 匹配优势")
            for s in ma.strengths[:5]:
                lines.append(f"- {s}")
            lines.append("")

        if ma is not None and ma.weaknesses:
            lines.append("### 待补充")
            for w in ma.weaknesses[:5]:
                lines.append(f"- {w}")
            lines.append("")

        # Bullets
        if gr is not None and gr.resume_bullets:
            lines.append("### 建议简历描述")
            for b in gr.resume_bullets[:3]:
                lines.append(f"- {b}")
            lines.append("")

        # Communication
        if gr is not None and gr.communication_message:
            lines.append("### HR 沟通话术")
            lines.append(f"> {gr.communication_message}")
            lines.append("")

        # Score
        if rs is not None:
            lines.append(
                f"检索质量：{rs.grade} (score={rs.metadata.get('total_score', 0):.2f})"
            )

        if warnings:
            lines.append("")
            lines.append("### ⚠️ 提示")
            for w in warnings:
                lines.append(f"- {w}")

        return "\n".join(lines)

    def _run_discovery(self, request: AgentRunRequest, output_dir: str) -> AgentRunResult:
        """Batch screen multiple jobs from text."""
        from career_agent.job_sources.parser import JobPostingParser
        from career_agent.discovery.ranker import JobRanker
        from career_agent.profile.loader import ProfileLoader
        from career_agent.rag.loaders.markdown_loader import MarkdownProfileLoader
        from career_agent.rag.chunking.text_chunker import TextChunker

        parser = JobPostingParser()
        postings = parser.parse_batch(request.user_message)
        loader = ProfileLoader()
        md_loader = MarkdownProfileLoader()
        chunker = TextChunker()
        docs = md_loader.load_directory(self.profile_dir)
        items = loader.load_documents(docs)

        ranker = JobRanker()
        ranked = ranker.rank(postings, items)

        lines = [f"共分析 {len(ranked)} 个岗位：", ""]
        for i, rj in enumerate(ranked[:5], 1):
            action_emoji = {"strong_apply": "🟢", "apply_with_resume_adjustment": "🟡",
                            "apply_only_if_interested": "🟠", "skip": "🔴", "not_priority": "🔴"}
            emoji = action_emoji.get(rj.recommended_action, "")
            jp = rj.job_posting
            lines.append(f"### {i}. {emoji} {jp.job_title or '未知岗位'} (score={rj.match_score:.2f})")
            lines.append(f"- 公司: {jp.company or '未知'} | {jp.location or ''}")
            lines.append(f"- 匹配: {', '.join(rj.matched_skills[:5]) or '无'}")
            lines.append(f"- 缺失: {', '.join(rj.missing_skills[:5]) or '无'}")
            lines.append(f"- 建议: {rj.recommended_action}")
            lines.append("")

        return AgentRunResult(
            trace_id=uuid.uuid4().hex[:12],
            final_answer="\n".join(lines),
            match_score=ranked[0].match_score if ranked else 0.0,
            recommended_action=ranked[0].recommended_action if ranked else "skip",
            status="completed",
        )

    def _run_message(self, request: AgentRunRequest, output_dir: str) -> AgentRunResult:
        """Generate communication script."""
        from career_agent.messages.agent import MessageAgent
        agent = MessageAgent()
        draft = agent.generate("boss_greeting", job_title="该岗位")
        approval = False
        if draft.risk_warnings:
            approval = True
        return AgentRunResult(
            trace_id=uuid.uuid4().hex[:12],
            final_answer=f"**建议话术**：\n\n{draft.text}",
            communication_script=draft.text,
            message_draft=draft.to_dict(),
            approval_required=approval,
            warnings=draft.risk_warnings,
            status="completed",
        )

    def _run_hr_reply(self, request: AgentRunRequest, output_dir: str) -> AgentRunResult:
        """Generate HR reply suggestion."""
        from career_agent.conversation.reply import HRReplyAssistant
        assistant = HRReplyAssistant()
        reply = assistant.suggest(request.hr_message or request.user_message)
        approval = True  # HR replies always need approval
        return AgentRunResult(
            trace_id=uuid.uuid4().hex[:12],
            final_answer=f"**建议回复**：\n\n{reply.suggested_reply}",
            communication_script=reply.suggested_reply,
            approval_required=approval,
            warnings=reply.risk_warnings,
            status="completed",
        )
