"""Match analysis agent — rule-based JD-vs-evidence comparison."""

from career_agent.agents.state import MatchAnalysisResult, ParsedJD
from career_agent.rag.schemas import RetrievedEvidence


class MatchAnalysisAgent:
    """Compare parsed JD requirements against retrieved user evidence.

    Produces a structured ``MatchAnalysisResult`` with strengths,
    weaknesses, project recommendations, and suggestions.
    Uses pure rule logic — no LLM calls.
    """

    def analyze(
        self,
        parsed_jd: ParsedJD,
        evidence: list[RetrievedEvidence],
    ) -> MatchAnalysisResult:
        """Run the match analysis and return a structured result."""

        # Collect all matched keywords from evidence
        all_matched: set[str] = set()
        for ev in evidence:
            all_matched.update(ev.matched_keywords)

        # Strengths: skills found both in JD and evidence
        strengths: list[str] = []
        for skill in parsed_jd.hard_skills:
            if skill in all_matched:
                strengths.append(f"具备 {skill} 相关经验")

        for skill in parsed_jd.bonus_skills:
            if skill in all_matched:
                strengths.append(f"加分项 {skill} 有对应经历")

        # If evidence titles are available, highlight them
        seen_titles: set[str] = set()
        for ev in evidence:
            if ev.title and ev.title not in seen_titles:
                seen_titles.add(ev.title)
                strengths.append(f"有「{ev.title}」项目经历")

        # Weaknesses: hard skills mentioned in JD but NOT in evidence
        weaknesses: list[str] = []
        for skill in parsed_jd.hard_skills:
            if skill not in all_matched:
                weaknesses.append(f"JD 要求 {skill}，当前知识库未检索到相关证据")
        for skill in parsed_jd.bonus_skills:
            if skill not in all_matched:
                weaknesses.append(f"加分项 {skill} 暂时未覆盖")

        # Recommended projects from evidence titles
        recommended: list[str] = []
        for ev in evidence:
            if ev.title and ev.title not in recommended:
                recommended.append(ev.title)

        # Suggestions
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
