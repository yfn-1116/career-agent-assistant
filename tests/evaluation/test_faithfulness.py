"""Tests for faithfulness / grounding checker."""

import pytest

from career_agent.domain.schemas import Evidence, GeneratedBullet
from career_agent.evaluation.faithfulness import (
    FaithfulnessChecker,
    FaithfulnessReport,
    check_bullet_grounding,
)


# ---------------------------------------------------------------------------
# Bullet grounding
# ---------------------------------------------------------------------------


class TestBulletGrounding:
    def test_bullet_with_evidence_passes(self):
        gb = GeneratedBullet(
            text="Built RAG pipeline with Chroma",
            evidence_ids=["ev-1"],
            confidence=0.9,
        )
        evidences = [
            Evidence(
                evidence_id="ev-1", chunk_id="c1", source="projects.md",
                content="Built a RAG pipeline using Chroma and LangChain",
                confidence=0.9,
            )
        ]
        result = check_bullet_grounding(gb, evidences)
        assert result["grounded"] is True
        assert result["score"] >= 0.5

    def test_bullet_without_evidence_fails(self):
        gb = GeneratedBullet(text="I know everything", evidence_ids=[], source_paths=[])
        result = check_bullet_grounding(gb, [])
        assert result["grounded"] is False
        assert result["score"] == 0.0

    def test_bullet_with_missing_evidence_ref_fails(self):
        gb = GeneratedBullet(
            text="Built MCP server",
            evidence_ids=["ev-999"],  # doesn't exist
        )
        evidences = [
            Evidence(evidence_id="ev-1", chunk_id="c1", source="a.md", content="RAG pipeline")
        ]
        result = check_bullet_grounding(gb, evidences)
        assert result["grounded"] is False

    def test_bullet_skills_in_evidence(self):
        gb = GeneratedBullet(
            text="Built FastAPI backend with RAG",
            evidence_ids=["ev-1"],
        )
        evidences = [
            Evidence(
                evidence_id="ev-1", chunk_id="c1", source="projects.md",
                content="Developed FastAPI backend and RAG retrieval system",
            )
        ]
        result = check_bullet_grounding(gb, evidences)
        assert result["grounded"] is True
        assert result["matched_terms"]  # should find FastAPI, RAG


# ---------------------------------------------------------------------------
# Exaggeration detection
# ---------------------------------------------------------------------------


class TestExaggerationDetection:
    def test_exaggerated_claim_flagged(self):
        """Claiming 'complete implementation' when evidence says 'reserved interface'."""
        gb = GeneratedBullet(
            text="完整实现了 MCP 协议和工具调用系统",
            evidence_ids=["ev-1"],
        )
        evidences = [
            Evidence(
                evidence_id="ev-1", chunk_id="c1", source="design.md",
                content="预留了 MCP 接入接口，后续可扩展 tool calling",
            )
        ]
        result = check_bullet_grounding(gb, evidences)
        # Should detect the exaggeration
        assert result["exaggerated"] is True or result["score"] < 0.7

    def test_modest_claim_not_flagged(self):
        gb = GeneratedBullet(
            text="学习了 LangGraph 基础并搭建了简易 workflow",
            evidence_ids=["ev-1"],
        )
        evidences = [
            Evidence(
                evidence_id="ev-1", chunk_id="c1", source="projects.md",
                content="使用 LangGraph 实现了基础的 StateGraph workflow",
            )
        ]
        result = check_bullet_grounding(gb, evidences)
        assert result["exaggerated"] is False


# ---------------------------------------------------------------------------
# FaithfulnessChecker
# ---------------------------------------------------------------------------


class TestFaithfulnessChecker:
    def test_all_bullets_grounded_high_score(self):
        checker = FaithfulnessChecker()
        bullets = [
            GeneratedBullet(text="Built RAG pipeline", evidence_ids=["ev-1"], confidence=0.9),
            GeneratedBullet(text="Used FastAPI", evidence_ids=["ev-2"], confidence=0.85),
        ]
        evidences = [
            Evidence(evidence_id="ev-1", chunk_id="c1", source="a.md", content="RAG pipeline"),
            Evidence(evidence_id="ev-2", chunk_id="c2", source="b.md", content="FastAPI backend"),
        ]
        report = checker.check(bullets, evidences)
        assert isinstance(report, FaithfulnessReport)
        assert report.faithfulness_score >= 0.7
        assert report.decision == "pass"

    def test_mixed_bullets_medium_score(self):
        checker = FaithfulnessChecker()
        bullets = [
            GeneratedBullet(text="Good claim", evidence_ids=["ev-1"], confidence=0.9),
            GeneratedBullet(text="No evidence claim", evidence_ids=[], source_paths=[]),
        ]
        evidences = [
            Evidence(evidence_id="ev-1", chunk_id="c1", source="a.md", content="Good content"),
        ]
        report = checker.check(bullets, evidences)
        assert report.faithfulness_score < 0.75
        assert report.decision == "revise_required"
        assert len(report.unsupported_claims) > 0

    def test_no_bullets_pass(self):
        checker = FaithfulnessChecker()
        report = checker.check([], [])
        assert report.faithfulness_score == 1.0
        assert report.decision == "pass"

    def test_all_ungrounded_fails(self):
        checker = FaithfulnessChecker()
        bullets = [
            GeneratedBullet(text="Claim A"),
            GeneratedBullet(text="Claim B"),
        ]
        report = checker.check(bullets, [])
        assert report.faithfulness_score < 0.5
        assert report.decision == "revise_required"
        assert len(report.unsupported_claims) == 2


# ---------------------------------------------------------------------------
# FaithfulnessReport
# ---------------------------------------------------------------------------


class TestFaithfulnessReport:
    def test_report_to_dict(self):
        report = FaithfulnessReport(
            faithfulness_score=0.85,
            decision="pass",
            unsupported_claims=[],
            details=[{"bullet": 0, "score": 0.9, "grounded": True}],
        )
        d = report.to_dict()
        assert d["faithfulness_score"] == 0.85
        assert d["decision"] == "pass"
