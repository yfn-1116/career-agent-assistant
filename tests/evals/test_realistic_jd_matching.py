"""Realistic JD matching evals — verify that different JD types match the
correct evidence items based on skill direction, not hardcoded filenames.

All assertions are rule-based: they check skill set overlap, direction
alignment, and action thresholds — never exact scores or specific file paths.
"""

from __future__ import annotations

import pytest

from career_agent.matching.scorer import JobMatchResult, JobMatchScorer
from tests.fixtures.realistic_jobs import JOBS
from tests.fixtures.user_profile import PROFILE_ITEMS


# ---------------------------------------------------------------------------
# Skill direction sets (lowercased) — used for rule-based assertions
# ---------------------------------------------------------------------------

_AGENT_SKILLS = {
    "python", "rag", "langgraph", "langchain", "agent", "agent 编排",
    "tool calling", "prompt engineering", "chroma", "faiss",
}

_CV_SKILLS = {
    "pytorch", "opencv", "cnn", "resnet", "yolo", "图像处理",
    "目标检测", "迁移学习", "数据增强", "tensorflow",
}

_BACKEND_SKILLS = {
    "fastapi", "postgresql", "mysql", "redis", "docker", "sql",
    "rest api", "api", "flask", "django", "微服务",
}

_FRONTEND_SKILLS = {
    "react", "vue", "typescript", "javascript", "css", "html",
    "next.js", "tailwind css", "前端",
}


def _matched_lower(result: JobMatchResult) -> set[str]:
    return {s.lower() for s in result.matched_skills}


# ---------------------------------------------------------------------------
# Agent-oriented JD matching
# ---------------------------------------------------------------------------


class TestAgentJDMatching:
    """Agent / RAG JDs should match the agent/RAG-heavy profile items."""

    def test_agent_jd_matches_agent_skills(self):
        """Agent JD must find agent/RAG matching skills from the profile."""
        jd = JOBS["agent_intern"]
        scorer = JobMatchScorer()
        result = scorer.score(
            jd.job_title, jd.hard_skills, jd.bonus_skills, PROFILE_ITEMS,
        )
        matched = _matched_lower(result)
        overlap = _AGENT_SKILLS & matched
        assert len(overlap) >= 2, (
            f"Agent JD should match 2+ agent/RAG skills, "
            f"got overlap={overlap}, matched={matched}"
        )
        assert result.recommended_action != "not_priority", (
            f"Agent JD should not be not_priority, got {result.recommended_action}"
        )

    def test_agent_jd_has_strength_and_gap_output(self):
        """Every JD result must produce strengths/weaknesses/reasons."""
        jd = JOBS["agent_intern"]
        scorer = JobMatchScorer()
        result = scorer.score(
            jd.job_title, jd.hard_skills, jd.bonus_skills, PROFILE_ITEMS,
        )
        assert isinstance(result.matched_skills, list)
        assert isinstance(result.missing_skills, list)
        # At least one reason line (strength or gap)
        assert len(result.reasons) > 0, "Must have at least one reason"


# ---------------------------------------------------------------------------
# CV-oriented JD matching
# ---------------------------------------------------------------------------


class TestCVJDMatching:
    """CV JDs should match the CV-heavy profile items (chem-auto-titration,
    dog-breed-cnn) — not the frontend/backend ones."""

    def test_cv_jd_matches_cv_skills(self):
        jd = JOBS["cv_algorithm_intern"]
        scorer = JobMatchScorer()
        result = scorer.score(
            jd.job_title, jd.hard_skills, jd.bonus_skills, PROFILE_ITEMS,
        )
        matched = _matched_lower(result)
        cv_overlap = _CV_SKILLS & matched
        assert len(cv_overlap) >= 2, (
            f"CV JD should match 2+ CV/ML skills, "
            f"got overlap={cv_overlap}, matched={matched}"
        )

    def test_cv_jd_does_not_match_frontend_skills(self):
        """CV JD must not claim frontend skills as matched."""
        jd = JOBS["cv_algorithm_intern"]
        scorer = JobMatchScorer()
        result = scorer.score(
            jd.job_title, jd.hard_skills, jd.bonus_skills, PROFILE_ITEMS,
        )
        matched = _matched_lower(result)
        frontend_overlap = _FRONTEND_SKILLS & matched
        assert len(frontend_overlap) == 0, (
            f"CV JD should not match frontend skills, got {frontend_overlap}"
        )


# ---------------------------------------------------------------------------
# Backend-oriented JD matching
# ---------------------------------------------------------------------------


class TestBackendJDMatching:
    """Backend JDs should match API/database-heavy profile items."""

    def test_backend_jd_matches_backend_skills(self):
        jd = JOBS["python_backend_intern"]
        scorer = JobMatchScorer()
        result = scorer.score(
            jd.job_title, jd.hard_skills, jd.bonus_skills, PROFILE_ITEMS,
        )
        matched = _matched_lower(result)
        backend_overlap = _BACKEND_SKILLS & matched
        assert len(backend_overlap) >= 2, (
            f"Backend JD should match 2+ backend skills, "
            f"got overlap={backend_overlap}, matched={matched}"
        )


# ---------------------------------------------------------------------------
# Frontend JD matching — should score low
# ---------------------------------------------------------------------------


class TestFrontendJDMatching:
    """Frontend JD: candidate has zero frontend projects → low score."""

    def test_frontend_jd_low_match(self):
        jd = JOBS["frontend_intern"]
        scorer = JobMatchScorer()
        result = scorer.score(
            jd.job_title, jd.hard_skills, jd.bonus_skills, PROFILE_ITEMS,
        )
        assert result.match_score < 0.50, (
            f"Frontend JD should score <0.50 (candidate has no frontend projects), "
            f"got {result.match_score:.2f}"
        )
        assert result.recommended_action == "not_priority", (
            f"Frontend JD action should be not_priority, got {result.recommended_action}"
        )


# ---------------------------------------------------------------------------
# Product JD matching — should note insufficient technical evidence
# ---------------------------------------------------------------------------


class TestProductJDMatching:
    """Product JD has few technical skills → limited match, must flag gaps."""

    def test_product_jd_low_technical_match(self):
        jd = JOBS["product_intern"]
        scorer = JobMatchScorer()
        result = scorer.score(
            jd.job_title, jd.hard_skills, jd.bonus_skills, PROFILE_ITEMS,
        )
        assert result.match_score < 0.60, (
            f"Product JD should have limited technical match (<0.60), "
            f"got {result.match_score:.2f}"
        )

    def test_product_jd_identifies_gaps(self):
        jd = JOBS["product_intern"]
        scorer = JobMatchScorer()
        result = scorer.score(
            jd.job_title, jd.hard_skills, jd.bonus_skills, PROFILE_ITEMS,
        )
        # Must identify that technical relevance is insufficient
        has_gaps = bool(result.missing_skills or result.weak_skills)
        assert has_gaps, (
            f"Product JD must identify gaps or weak skills, "
            f"missing={result.missing_skills}, weak={result.weak_skills}"
        )


# ---------------------------------------------------------------------------
# Data Analyst JD matching — limited overlap
# ---------------------------------------------------------------------------


class TestDataAnalystJDMatching:
    """Data analyst: candidate has Python + some libraries but not core DA stack."""

    def test_data_analyst_jd_medium_to_low_match(self):
        jd = JOBS["data_analyst_intern"]
        scorer = JobMatchScorer()
        result = scorer.score(
            jd.job_title, jd.hard_skills, jd.bonus_skills, PROFILE_ITEMS,
        )
        # Python overlaps but core DA tools (Tableau/PowerBI/AB testing) don't
        assert result.match_score < 0.70, (
            f"Data analyst JD should score <0.70 (missing core DA tools), "
            f"got {result.match_score:.2f}"
        )


# ---------------------------------------------------------------------------
# All JDs: structural completeness
# ---------------------------------------------------------------------------


class TestAllJDsHaveRequiredFields:
    """Every JD result must include the required fields, regardless of match."""

    @pytest.mark.parametrize("jd_key", sorted(JOBS.keys()))
    def test_result_has_valid_recommendation(self, jd_key):
        jd = JOBS[jd_key]
        scorer = JobMatchScorer()
        result = scorer.score(
            jd.job_title, jd.hard_skills, jd.bonus_skills, PROFILE_ITEMS,
        )
        valid_actions = {
            "strong_apply", "apply_with_resume_adjustment",
            "apply_only_if_interested", "not_priority",
        }
        assert result.recommended_action in valid_actions, (
            f"{jd_key}: invalid recommended_action '{result.recommended_action}'"
        )

    @pytest.mark.parametrize("jd_key", sorted(JOBS.keys()))
    def test_result_has_reasons(self, jd_key):
        jd = JOBS[jd_key]
        scorer = JobMatchScorer()
        result = scorer.score(
            jd.job_title, jd.hard_skills, jd.bonus_skills, PROFILE_ITEMS,
        )
        assert len(result.reasons) > 0, (
            f"{jd_key}: must have at least one reason (strength or gap)"
        )

    @pytest.mark.parametrize("jd_key", sorted(JOBS.keys()))
    def test_result_score_in_range(self, jd_key):
        jd = JOBS[jd_key]
        scorer = JobMatchScorer()
        result = scorer.score(
            jd.job_title, jd.hard_skills, jd.bonus_skills, PROFILE_ITEMS,
        )
        assert 0.0 <= result.match_score <= 1.0, (
            f"{jd_key}: score {result.match_score} out of [0,1] range"
        )
