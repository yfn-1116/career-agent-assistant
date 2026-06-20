"""Build agent — produces grounded Markdown output from evidence and analysis.

Crucially, every resume bullet must be traceable to a RetrievedEvidence
item.  No fabrication.
"""

from career_agent.agents.state import (
    GeneratedOutput,
    MatchAnalysisResult,
    ParsedJD,
)
from career_agent.rag.schemas import RetrievedEvidence


class BuildAgent:
    """Generate structured output from parsed JD, evidence, and analysis.

    Uses template-based generation — no LLM calls.
    """

    def build(
        self,
        parsed_jd: ParsedJD,
        evidence: list[RetrievedEvidence],
        match_analysis: MatchAnalysisResult,
    ) -> GeneratedOutput:
        """Produce the final ``GeneratedOutput``."""
        evidence_refs = self._collect_refs(evidence)
        resume_bullets = self._build_resume_bullets(evidence, match_analysis)
        communication = self._build_communication(parsed_jd, match_analysis)
        summary = self._build_summary(parsed_jd, match_analysis, evidence)

        return GeneratedOutput(
            resume_bullets=resume_bullets,
            communication_message=communication,
            summary=summary,
            evidence_refs=evidence_refs,
            metadata={"builder": "build_agent"},
        )

    # -- internal -----------------------------------------------------------

    @staticmethod
    def _collect_refs(evidence: list[RetrievedEvidence]) -> list[str]:
        return [ev.evidence_id for ev in evidence]

    def _build_resume_bullets(
        self,
        evidence: list[RetrievedEvidence],
        analysis: MatchAnalysisResult,
    ) -> list[str]:
        if not evidence:
            return ["（当前知识库中暂无足够证据生成简历 bullet，请补充个人资料。）"]

        bullets: list[str] = []
        for ev in evidence:
            if ev.title:
                bullets.append(
                    f"- 参与「{ev.title}」项目：{self._snippet(ev.content)} "
                    f"（来源：{ev.source_path}）"
                )
            else:
                bullets.append(
                    f"- {self._snippet(ev.content)} （来源：{ev.source_path}）"
                )

        # Add a bullet from strengths if available
        for s in analysis.strengths[:3]:
            if "「" in s:
                bullets.append(f"- {s}")

        return bullets

    @staticmethod
    def _build_communication(
        parsed_jd: ParsedJD,
        analysis: MatchAnalysisResult,
    ) -> str:
        job = parsed_jd.job_title or "该岗位"
        if analysis.strengths:
            top = "、".join(
                s.replace("具备 ", "").replace(" 相关经验", "")
                for s in analysis.strengths[:3]
            )
            return (
                f"您好，我对{job}非常感兴趣。"
                f"我的经历与岗位要求在以下方面匹配：{top}。"
                f"期待有机会进一步沟通！"
            )
        return (
            f"您好，我对{job}很感兴趣。"
            f"虽然当前知识库证据有限，但我愿意提供更多信息以供评估。"
        )

    @staticmethod
    def _build_summary(
        parsed_jd: ParsedJD,
        analysis: MatchAnalysisResult,
        evidence: list[RetrievedEvidence],
    ) -> str:
        job = parsed_jd.job_title or "目标岗位"
        hit = len(analysis.strengths)
        miss = len(analysis.weaknesses)
        ev_count = len(evidence)
        return (
            f"针对「{job}」的匹配分析完成。"
            f"命中匹配项 {hit} 条，未覆盖项 {miss} 条，"
            f"基于 {ev_count} 条检索证据生成输出。"
        )

    @staticmethod
    def _snippet(content: str, max_len: int = 80) -> str:
        """Return a short snippet from content."""
        text = content.replace("\n", " ").strip()
        if len(text) <= max_len:
            return text
        return text[:max_len] + "…"
