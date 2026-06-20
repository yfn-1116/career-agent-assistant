"""Match analysis agent — rule-based with optional LLM enhancement."""

from career_agent.agents.state import MatchAnalysisResult, ParsedJD
from career_agent.models.provider import ModelProvider
from career_agent.rag.schemas import RetrievedEvidence


class MatchAnalysisAgent:
    """Compare parsed JD requirements against retrieved user evidence.

    Uses rule logic by default.  When *model_provider* and *use_llm*
    are both set, the LLM is used for deeper analysis with rule-based
    fallback on failure.
    """

    def __init__(
        self,
        model_provider: ModelProvider | None = None,
        use_llm: bool = False,
    ) -> None:
        self.model_provider = model_provider
        self.use_llm = use_llm and model_provider is not None

    def analyze(
        self,
        parsed_jd: ParsedJD,
        evidence: list[RetrievedEvidence],
    ) -> MatchAnalysisResult:
        """Run the match analysis and return a structured result."""
        if self.use_llm and evidence:
            llm_result = self._llm_analyze(parsed_jd, evidence)
            if llm_result is not None:
                return llm_result
            # fall through to rule-based

        return self._rule_analyze(parsed_jd, evidence)

    # -- LLM path ------------------------------------------------------------

    def _llm_analyze(
        self, parsed_jd: ParsedJD, evidence: list[RetrievedEvidence]
    ) -> MatchAnalysisResult | None:
        evidence_text = self._format_evidence(evidence)
        system = (
            "你是一个求职匹配分析助手。根据 JD 要求和用户 evidence，"
            "输出结构化的匹配分析。\n"
            "严格规则：\n"
            "1. 只能基于提供的 evidence 判断，不得编造。\n"
            "2. 如果 evidence 中没有某个技能的证据，诚实标注为未覆盖。\n"
            "3. 用中文输出。"
        )
        prompt = (
            f"【岗位 JD 解析结果】\n"
            f"标题：{parsed_jd.job_title}\n"
            f"方向：{parsed_jd.job_direction}\n"
            f"硬技能要求：{', '.join(parsed_jd.hard_skills)}\n"
            f"加分技能：{', '.join(parsed_jd.bonus_skills)}\n"
            f"软技能：{', '.join(parsed_jd.soft_skills)}\n\n"
            f"【用户 Evidence】\n{evidence_text}\n\n"
            "请返回以下 JSON（只返回 JSON，不要 markdown 标记）：\n"
            "{\n"
            '  "strengths": ["优势1：具体说明为什么匹配"],\n'
            '  "weaknesses": ["不足1：JD要求但evidence未覆盖的技能"],\n'
            '  "recommended_projects": ["项目名1"],\n'
            '  "suggestions": ["建议1：如何改进简历或补充经历"],\n'
            '  "matched_keywords": ["匹配的关键词"]\n'
            "}"
        )
        try:
            import json
            assert self.model_provider is not None
            raw = self.model_provider.generate(prompt, system_prompt=system).strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1]
                if raw.endswith("```"):
                    raw = raw[:-3]
            data = json.loads(raw)
            return MatchAnalysisResult(
                strengths=list(data.get("strengths", [])),
                weaknesses=list(data.get("weaknesses", [])),
                recommended_projects=list(data.get("recommended_projects", [])),
                matched_keywords=list(data.get("matched_keywords", [])),
                suggestions=list(data.get("suggestions", [])),
                metadata={"analyzer": "match_analysis_agent_llm"},
            )
        except Exception:
            return None

    @staticmethod
    def _format_evidence(evidence: list[RetrievedEvidence]) -> str:
        lines: list[str] = []
        for i, ev in enumerate(evidence, 1):
            snippet = ev.content[:250].replace("\n", " ")
            lines.append(
                f"[{i}] {ev.title} (keywords: {', '.join(ev.matched_keywords)})\n"
                f"    {snippet}"
            )
        return "\n".join(lines)

    # -- rule-based path -----------------------------------------------------

    def _rule_analyze(
        self, parsed_jd: ParsedJD, evidence: list[RetrievedEvidence]
    ) -> MatchAnalysisResult:
        all_matched: set[str] = set()
        for ev in evidence:
            all_matched.update(ev.matched_keywords)

        strengths: list[str] = []
        for skill in parsed_jd.hard_skills:
            if skill in all_matched:
                strengths.append(f"具备 {skill} 相关经验")
        for skill in parsed_jd.bonus_skills:
            if skill in all_matched:
                strengths.append(f"加分项 {skill} 有对应经历")

        seen_titles: set[str] = set()
        for ev in evidence:
            if ev.title and ev.title not in seen_titles:
                seen_titles.add(ev.title)
                strengths.append(f"有「{ev.title}」项目经历")

        weaknesses: list[str] = []
        for skill in parsed_jd.hard_skills:
            if skill not in all_matched:
                weaknesses.append(f"JD 要求 {skill}，当前知识库未检索到相关证据")
        for skill in parsed_jd.bonus_skills:
            if skill not in all_matched:
                weaknesses.append(f"加分项 {skill} 暂时未覆盖")

        recommended: list[str] = []
        for ev in evidence:
            if ev.title and ev.title not in recommended:
                recommended.append(ev.title)

        suggestions: list[str] = []
        if weaknesses:
            suggestions.append("建议在简历中补充或突出上述缺失技能的相关经历")
        if len(evidence) < 3:
            suggestions.append("知识库检索证据较少，建议补充更多项目或实习资料")
        if parsed_jd.job_direction and parsed_jd.job_direction != "general":
            suggestions.append(
                f"岗位方向为 {parsed_jd.job_direction}，"
                "可重点突出该方向的匹配经历"
            )
        if strengths:
            suggestions.append("简历 bullet 应优先引用上述 strengths 中的经历")

        return MatchAnalysisResult(
            strengths=strengths,
            weaknesses=weaknesses,
            recommended_projects=recommended,
            matched_keywords=sorted(all_matched),
            suggestions=suggestions,
            metadata={"analyzer": "match_analysis_agent"},
        )
