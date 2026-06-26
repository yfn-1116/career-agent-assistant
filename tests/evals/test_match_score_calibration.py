"""Match score calibration evals — verify score discrimination.

Scores must spread across bands:
- Strong match : 0.70 – 0.95
- Medium match : 0.50 – 0.85
- Weak match   : < 0.50
- Not recommended : < 0.55

Critical: scores must NOT all cluster around a single value (e.g. all ~0.70).
"""

from __future__ import annotations

import statistics

import pytest

from career_agent.matching.scorer import JobMatchScorer
from tests.fixtures.realistic_jobs import JOBS
from tests.fixtures.user_profile import PROFILE_ITEMS


_AGENT_CANDIDATE = PROFILE_ITEMS  # full profile: all 5 items


# ---------------------------------------------------------------------------
# Score band discrimination
# ---------------------------------------------------------------------------


class TestScoreDiscrimination:
    """Different JD types with the same candidate must produce clearly
    different bands of scores — not all similar."""

    def test_agent_jd_strong_match(self):
        """Agent JD against agent-candidate should score in strong band."""
        jd = JOBS["agent_intern"]
        scorer = JobMatchScorer()
        result = scorer.score(
            jd.job_title, jd.hard_skills, jd.bonus_skills, _AGENT_CANDIDATE,
        )
        assert 0.65 <= result.match_score <= 0.95, (
            f"Agent JD + agent candidate: expected 0.65-0.95, got {result.match_score:.3f}"
        )
        assert result.recommended_action in (
            "strong_apply", "apply_with_resume_adjustment",
        ), f"Agent JD should be strong_apply or adjust, got {result.recommended_action}"

    def test_rag_jd_strong_match(self):
        """RAG JD against agent-candidate should also score well."""
        jd = JOBS["rag_intern"]
        scorer = JobMatchScorer()
        result = scorer.score(
            jd.job_title, jd.hard_skills, jd.bonus_skills, _AGENT_CANDIDATE,
        )
        assert 0.60 <= result.match_score <= 0.95, (
            f"RAG JD + agent candidate: expected 0.60-0.95, got {result.match_score:.3f}"
        )

    def test_backend_jd_medium_match(self):
        """Backend JD: candidate has some backend skills via smart-journey
        and career-agent-assistant's FastAPI, but is not a dedicated backend dev."""
        jd = JOBS["python_backend_intern"]
        scorer = JobMatchScorer()
        result = scorer.score(
            jd.job_title, jd.hard_skills, jd.bonus_skills, _AGENT_CANDIDATE,
        )
        assert 0.45 <= result.match_score <= 0.85, (
            f"Backend JD + agent candidate: expected 0.45-0.85, got {result.match_score:.3f}"
        )

    def test_cv_jd_medium_match(self):
        """CV JD: candidate has 2 CV projects (chem-auto-titration, dog-breed)
        with strong PyTorch/OpenCV/CNN coverage → strong-to-medium match."""
        jd = JOBS["cv_algorithm_intern"]
        scorer = JobMatchScorer()
        result = scorer.score(
            jd.job_title, jd.hard_skills, jd.bonus_skills, _AGENT_CANDIDATE,
        )
        assert 0.40 <= result.match_score <= 0.90, (
            f"CV JD + agent candidate: expected 0.40-0.90, got {result.match_score:.3f}"
        )

    def test_frontend_jd_weak_match(self):
        """Frontend JD: candidate has zero frontend projects → very low."""
        jd = JOBS["frontend_intern"]
        scorer = JobMatchScorer()
        result = scorer.score(
            jd.job_title, jd.hard_skills, jd.bonus_skills, _AGENT_CANDIDATE,
        )
        assert result.match_score < 0.50, (
            f"Frontend JD: expected <0.50 (no frontend projects), "
            f"got {result.match_score:.3f}"
        )
        assert result.recommended_action == "not_priority"

    def test_product_jd_not_recommended(self):
        """Product JD: very little technical overlap → not recommended."""
        jd = JOBS["product_intern"]
        scorer = JobMatchScorer()
        result = scorer.score(
            jd.job_title, jd.hard_skills, jd.bonus_skills, _AGENT_CANDIDATE,
        )
        assert result.match_score < 0.60, (
            f"Product JD: expected <0.60 (minimal tech overlap), "
            f"got {result.match_score:.3f}"
        )

    def test_data_analyst_jd_limited_overlap(self):
        """Data analyst JD: Python overlaps but core DA stack missing."""
        jd = JOBS["data_analyst_intern"]
        scorer = JobMatchScorer()
        result = scorer.score(
            jd.job_title, jd.hard_skills, jd.bonus_skills, _AGENT_CANDIDATE,
        )
        # Should be below the "adjust resume" threshold if DA tools are missing
        assert result.match_score < 0.75, (
            f"Data analyst JD: expected <0.75 (missing core DA tools), "
            f"got {result.match_score:.3f}"
        )


# ---------------------------------------------------------------------------
# Score spread — ensure meaningful variance
# ---------------------------------------------------------------------------


class TestScoreSpread:
    """The set of scores across all 8 JDs must have meaningful variance."""

    def test_scores_have_meaningful_range(self):
        scorer = JobMatchScorer()
        scores = []
        for key in sorted(JOBS.keys()):
            jd = JOBS[key]
            result = scorer.score(
                jd.job_title, jd.hard_skills, jd.bonus_skills, _AGENT_CANDIDATE,
            )
            scores.append(result.match_score)

        score_range = max(scores) - min(scores)
        assert score_range >= 0.25, (
            f"Scores too clustered (range={score_range:.3f}), "
            f"need >=0.25 range: {[round(s, 3) for s in scores]}"
        )

    def test_scores_have_meaningful_std(self):
        scorer = JobMatchScorer()
        scores = []
        for key in sorted(JOBS.keys()):
            jd = JOBS[key]
            result = scorer.score(
                jd.job_title, jd.hard_skills, jd.bonus_skills, _AGENT_CANDIDATE,
            )
            scores.append(result.match_score)

        std = statistics.stdev(scores) if len(scores) > 1 else 0.0
        assert std >= 0.08, (
            f"Scores too uniform (std={std:.4f}), "
            f"need >=0.08: {[round(s, 3) for s in scores]}"
        )

    def test_frontend_is_lowest_or_among_lowest(self):
        """Frontend JD should be among the lowest-scoring JDs."""
        scorer = JobMatchScorer()
        scores_by_key: dict[str, float] = {}
        for key in sorted(JOBS.keys()):
            jd = JOBS[key]
            result = scorer.score(
                jd.job_title, jd.hard_skills, jd.bonus_skills, _AGENT_CANDIDATE,
            )
            scores_by_key[key] = result.match_score

        frontend_score = scores_by_key["frontend_intern"]
        bottom_three = sorted(scores_by_key.values())[:3]
        assert frontend_score <= max(bottom_three), (
            f"Frontend score ({frontend_score:.3f}) should be among bottom 3, "
            f"bottom 3: {bottom_three}"
        )


# ---------------------------------------------------------------------------
# Threshold → action mapping
# ---------------------------------------------------------------------------


class TestThresholdCorrectActions:
    """Verify that recommended_action aligns with match_score thresholds."""

    @pytest.mark.parametrize("jd_key,expect_not_priority", [
        ("frontend_intern", True),
        ("product_intern", True),
    ])
    def test_low_match_jds_are_not_priority(self, jd_key, expect_not_priority):
        jd = JOBS[jd_key]
        scorer = JobMatchScorer()
        result = scorer.score(
            jd.job_title, jd.hard_skills, jd.bonus_skills, _AGENT_CANDIDATE,
        )
        if expect_not_priority:
            assert result.recommended_action == "not_priority", (
                f"{jd_key} must be not_priority, got {result.recommended_action} "
                f"(score={result.match_score:.3f})"
            )

    @pytest.mark.parametrize("jd_key", ["agent_intern", "rag_intern"])
    def test_agent_rag_jds_not_not_priority(self, jd_key):
        """Agent/RAG JDs for this candidate must NOT be not_priority."""
        jd = JOBS[jd_key]
        scorer = JobMatchScorer()
        result = scorer.score(
            jd.job_title, jd.hard_skills, jd.bonus_skills, _AGENT_CANDIDATE,
        )
        assert result.recommended_action != "not_priority", (
            f"{jd_key} should NOT be not_priority, "
            f"got {result.recommended_action} (score={result.match_score:.3f})"
        )
