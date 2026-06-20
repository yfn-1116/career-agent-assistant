"""Build agent — produces grounded Markdown output from evidence and analysis.

Crucially, every resume bullet must be traceable to a RetrievedEvidence
item.  No fabrication.

Supports an optional ``ModelProvider`` for LLM-enhanced generation.
When it is not provided or ``use_llm`` is ``False`` (the default),
template-based logic is used, matching the Phase-1 behaviour exactly.
"""

from career_agent.agents.state import (
    GeneratedOutput,
    MatchAnalysisResult,
    ParsedJD,
)
from career_agent.models.provider import ModelProvider
from career_agent.rag.schemas import RetrievedEvidence


class BuildAgent:
    """Generate structured output from parsed JD, evidence, and analysis.

    Parameters
    ----------
    model_provider : ModelProvider | None
        Optional LLM backend.  Only used when *use_llm* is ``True``.
    use_llm : bool
        If ``True`` and *model_provider* is set, the provider is called
        for ``communication_message`` generation; other fields still use
        rule-based logic in this first integration phase.
    """

    def __init__(
        self,
        model_provider: ModelProvider | None = None,
        use_llm: bool = False,
    ) -> None:
        self.model_provider = model_provider
        self.use_llm = use_llm and model_provider is not None

    def build(
        self,
        parsed_jd: ParsedJD,
        evidence: list[RetrievedEvidence],
        match_analysis: MatchAnalysisResult,
    ) -> GeneratedOutput:
        """Produce the final ``GeneratedOutput``."""
        evidence_refs = self._collect_refs(evidence)
        resume_bullets = self._build_resume_bullets(evidence, match_analysis)
        communication = self._build_communication(parsed_jd, match_analysis, evidence)
        summary = self._build_summary(parsed_jd, match_analysis, evidence)

        return GeneratedOutput(
            resume_bullets=resume_bullets,
            communication_message=communication,
            summary=summary,
            evidence_refs=evidence_refs,
            metadata={"builder": "build_agent", "use_llm": self.use_llm},
        )

    # -- llm helpers ---------------------------------------------------------

    def _llm_communication(
        self,
        parsed_jd: ParsedJD,
        match_analysis: MatchAnalysisResult,
        evidence: list[RetrievedEvidence],
    ) -> str | None:
        """Try to generate communication via LLM; return None on failure."""
        evidence_summary = self._format_evidence_for_prompt(evidence)
        system = (
            "你是一个求职辅助助手。你需要根据用户提供的个人信息（证据）"
            "生成一段简短的 HR / mentor 联系话术。"
            "必须遵守以下规则：\n"
            "1. 只能使用下面提供的 evidence 中的信息。\n"
            "2. 不得编造用户没有的项目、技能或经历。\n"
            "3. 如果 evidence 不足以支持某个说法，省略它。\n"
            "4. 输出控制在 100 字以内，语气专业但友好。\n"
            "5. 只输出话术本身，不要加前缀或解释。"
        )
        prompt = (
            f"岗位：{parsed_jd.job_title or '未知'}\n"
            f"方向：{parsed_jd.job_direction}\n"
            f"匹配优势：{'、'.join(match_analysis.strengths[:5])}\n"
            f"推荐项目：{'、'.join(match_analysis.recommended_projects[:3])}\n"
            f"Evidence：\n{evidence_summary}"
        )
        try:
            assert self.model_provider is not None  # guarded by self.use_llm
            return self.model_provider.generate(
                prompt, system_prompt=system
            ).strip()
        except Exception:
            return None

    @staticmethod
    def _format_evidence_for_prompt(
        evidence: list[RetrievedEvidence],
    ) -> str:
        lines: list[str] = []
        for i, ev in enumerate(evidence, 1):
            snippet = ev.content[:200].replace("\n", " ")
            lines.append(
                f"[{i}] {ev.title} (source: {ev.source_path}, "
                f"keywords: {', '.join(ev.matched_keywords)})\n"
                f"    {snippet}"
            )
        return "\n".join(lines) if lines else "（无 evidence）"

    # -- template helpers (unchanged from Phase 1) ----------------------------

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

        for s in analysis.strengths[:3]:
            if "「" in s:
                bullets.append(f"- {s}")

        return bullets

    def _build_communication(
        self,
        parsed_jd: ParsedJD,
        analysis: MatchAnalysisResult,
        evidence: list[RetrievedEvidence],
    ) -> str:
        if self.use_llm:
            llm_result = self._llm_communication(parsed_jd, analysis, evidence)
            if llm_result:
                return llm_result
            # fall through to rule-based on failure

        return self._template_communication(parsed_jd, analysis)

    @staticmethod
    def _template_communication(
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
        text = content.replace("\n", " ").strip()
        if len(text) <= max_len:
            return text
        return text[:max_len] + "…"
