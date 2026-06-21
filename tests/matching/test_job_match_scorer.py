"""Tests for job matching scorer."""

from career_agent.matching.scorer import JobMatchScorer
from career_agent.profile.schema import STATUS_DESIGNED, STATUS_IMPLEMENTED, ProfileItem


def _item(skills: list[str], status: str = STATUS_IMPLEMENTED, source: str = "projects.md") -> ProfileItem:
    return ProfileItem(source_path=source, skills=skills, status=status, claims=["test"], confidence=0.8)


class TestJobMatchScorer:
    def test_all_skills_matched_high_score(self):
        items = [_item(["Python", "RAG", "LangGraph", "FastAPI"])]
        scorer = JobMatchScorer()
        result = scorer.score("Agent Intern", ["Python", "RAG", "LangGraph"], ["FastAPI"], items)
        assert result.match_score >= 0.7
        assert result.recommended_action in ("strong_apply", "apply_with_resume_adjustment")

    def test_missing_key_skills_lowers_score(self):
        items = [_item(["Python"])]
        scorer = JobMatchScorer()
        result = scorer.score("K8s Engineer", ["Kubernetes", "Docker", "Helm"], [], items)
        assert result.match_score < 0.5
        assert "kubernetes" in result.missing_skills

    def test_weak_evidence_not_strong(self):
        items = [_item(["LangGraph"], status=STATUS_DESIGNED)]
        scorer = JobMatchScorer()
        result = scorer.score("Agent Intern", ["LangGraph"], [], items)
        assert "LangGraph" not in result.matched_skills or "LangGraph" in result.weak_skills

    def test_missing_skills_in_result(self):
        items = [_item(["Python"])]
        scorer = JobMatchScorer()
        result = scorer.score("DevOps", ["Docker", "Kubernetes"], [], items)
        assert len(result.missing_skills) >= 1

    def test_skill_evidence_map(self):
        items = [_item(["Python", "RAG"], source="projects.md")]
        scorer = JobMatchScorer()
        result = scorer.score("Agent", ["Python"], [], items)
        assert "python" in result.skill_evidence_map

    def test_recommended_action_thresholds(self):
        items = [_item(["Python", "RAG", "LangGraph", "FastAPI", "Docker"])]
        scorer = JobMatchScorer()
        r = scorer.score("Agent", ["Python", "RAG", "LangGraph", "FastAPI"], ["Docker"], items)
        assert r.recommended_action == "strong_apply"
