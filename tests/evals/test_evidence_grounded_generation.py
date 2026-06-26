"""Evidence-grounded generation evals — verify that generated content
respects evidence status constraints (implemented / designed / planned).

Uses EvidenceGate, FaithfulnessChecker, and check_bullet_grounding to
verify that:
- No evidence → no exaggerated bullets
- planned → only planning verbs, blocked from claiming completion
- designed → blocks implementation verbs, allows design verbs
- implemented → allows full claims, warns on exaggeration
- Generated content must reference evidence
- Cannot mention tech keywords absent from evidence
"""

from __future__ import annotations

import pytest

from career_agent.domain.schemas import Evidence, GeneratedBullet
from career_agent.evaluation.faithfulness import (
    FaithfulnessChecker,
    FaithfulnessReport,
    check_bullet_grounding,
)
from career_agent.evidence.gate import EvidenceGate, EvidenceResult
from career_agent.profile.schema import (
    STATUS_DESIGNED,
    STATUS_IMPLEMENTED,
    STATUS_PLANNED,
    STATUS_UNCERTAIN,
)

# ---------------------------------------------------------------------------
# Shared evidence fixtures
# ---------------------------------------------------------------------------


def _impl_evidence() -> Evidence:
    return Evidence(
        evidence_id="ev-impl-1",
        chunk_id="c1",
        source="projects/career-agent-assistant.md",
        content=(
            "基于 LangGraph 实现了完整的 Agent workflow，"
            "支持 tool calling 和状态管理。使用 Chroma 作为向量数据库，"
            "实现了 Hybrid 检索（关键词 + embedding 融合）。"
        ),
        confidence=0.92,
    )


def _designed_evidence() -> Evidence:
    return Evidence(
        evidence_id="ev-designed-1",
        chunk_id="c2",
        source="docs/mcp-design.md",
        content=(
            "设计了 MCP 协议接入方案，预留了外部工具扩展接口。"
            "架构文档中描述了统一的 Tool Registry 接口定义。"
        ),
        confidence=0.70,
    )


def _planned_evidence() -> Evidence:
    return Evidence(
        evidence_id="ev-planned-1",
        chunk_id="c3",
        source="docs/roadmap.md",
        content=(
            "计划后续支持分布式的多 Agent 部署架构，"
            "拟引入消息队列进行 Agent 间异步通信。"
        ),
        confidence=0.35,
    )


# ---------------------------------------------------------------------------
# No evidence → no fabrication
# ---------------------------------------------------------------------------


class TestNoEvidenceNoExaggeration:
    """Without evidence, generation must not produce exaggerated claims."""

    def test_gate_blocks_claim_with_no_evidence(self):
        gate = EvidenceGate()
        result = gate.block_unsupported("掌握了 Kubernetes 集群管理和大规模部署")
        assert isinstance(result, EvidenceResult)
        assert not result.allowed
        assert len(result.blocked_reason) > 0

    def test_faithfulness_scores_zero_for_unevidenced_bullet(self):
        bullet = GeneratedBullet(
            text="Built a complete distributed RAG system",
            evidence_ids=[],
        )
        result = check_bullet_grounding(bullet, [])
        assert result["grounded"] is False
        assert result["score"] == 0.0


# ---------------------------------------------------------------------------
# planned evidence constraints
# ---------------------------------------------------------------------------


class TestPlannedEvidenceConstraints:
    """planced evidence → blocked from resume claims entirely."""

    def test_planned_status_blocks_all_claims(self):
        gate = EvidenceGate()
        claims = [
            "实现了完整的 CI/CD pipeline",
            "构建了基于 K8s 的集群管理",
            "开发了自动化部署脚本",
        ]
        for claim in claims:
            result = gate.validate(claim, STATUS_PLANNED)
            assert not result.allowed, (
                f"planned evidence must block: '{claim}'"
            )

    def test_planned_even_modest_claim_blocked(self):
        gate = EvidenceGate()
        result = gate.validate("计划后续完善日志和监控体系", STATUS_PLANNED)
        # planned evidence cannot produce any resume claim
        assert not result.allowed

    def test_faithfulness_penalizes_planned_based_bullets(self):
        checker = FaithfulnessChecker()
        bullets = [
            GeneratedBullet(
                text="Deployed a distributed multi-agent system with message queue",
                evidence_ids=["ev-planned-1"],
            ),
        ]
        evidences = [_planned_evidence()]
        report = checker.check(bullets, evidences)
        # The planned evidence doesn't support the grandiose claim
        assert report.faithfulness_score < 0.80, (
            f"planned-based grandiose claim should score <0.80, "
            f"got {report.faithfulness_score:.2f}"
        )


# ---------------------------------------------------------------------------
# designed evidence constraints
# ---------------------------------------------------------------------------


class TestDesignedEvidenceConstraints:
    """designed evidence → must downgrade implementation verbs to design verbs."""

    def test_designed_blocks_implemented_verb(self):
        gate = EvidenceGate()
        result = gate.validate("构建了一个完整的 RAG 知识库系统", STATUS_DESIGNED)
        assert not result.allowed

    def test_designed_downgrade_preserves_tech_terms(self):
        gate = EvidenceGate()
        result = gate.validate("实现了 MCP 协议支持", STATUS_DESIGNED)
        assert result.downgraded_text, "Should produce downgraded version"
        # Downgraded text should still mention the technology
        assert "MCP" in result.downgraded_text or "设计" in result.downgraded_text, (
            f"downgraded text should retain tech terms: '{result.downgraded_text}'"
        )

    def test_designed_allows_design_verbs(self):
        gate = EvidenceGate()
        allowed_claims = [
            "设计了基于 LangGraph 的多 Agent 架构方案",
            "规划了 MCP 协议接入的技术路径",
        ]
        for claim in allowed_claims:
            result = gate.validate(claim, STATUS_DESIGNED)
            assert result.allowed, f"designed evidence should allow: '{claim}'"

    def test_designed_faithfulness_with_appropriate_claim(self):
        bullet = GeneratedBullet(
            text="Designed MCP protocol integration architecture",
            evidence_ids=["ev-designed-1"],
            confidence=0.70,
        )
        result = check_bullet_grounding(bullet, [_designed_evidence()])
        assert result["grounded"] is True


# ---------------------------------------------------------------------------
# implemented evidence — full claims allowed
# ---------------------------------------------------------------------------


class TestImplementedEvidenceAllowsFullClaims:
    """implemented evidence → 实现/完成/开发/构建 all allowed."""

    def test_implemented_allows_build_verbs(self):
        gate = EvidenceGate()
        allowed_claims = [
            "基于 LangGraph 实现了 Agent workflow 模块",
            "完成了 RAG pipeline 的开发与测试",
            "使用 FastAPI 开发了 RESTful API 接口",
            "构建了 Hybrid 检索系统支持关键词和向量搜索",
        ]
        for claim in allowed_claims:
            result = gate.validate(claim, STATUS_IMPLEMENTED)
            assert result.allowed, f"implemented evidence should allow: '{claim}'"

    def test_implemented_warns_on_exaggeration(self):
        gate = EvidenceGate()
        result = gate.validate(
            "生产级部署了完整的大规模 Agent 平台，服务全球百万用户",
            STATUS_IMPLEMENTED,
        )
        # Allowed (evidence is implemented) but should warn
        assert result.allowed, "implemented evidence allows claims"
        assert len(result.warnings) > 0, (
            "excessive claims should trigger warnings even for implemented evidence"
        )


# ---------------------------------------------------------------------------
# Evidence reference integrity
# ---------------------------------------------------------------------------


class TestGeneratedContentReferencesEvidence:
    """Generated bullets must reference their evidence."""

    def test_bullet_with_evidence_ids_is_grounded(self):
        bullet = GeneratedBullet(
            text="Built RAG pipeline with LangGraph",
            evidence_ids=["ev-impl-1"],
            confidence=0.85,
        )
        result = check_bullet_grounding(bullet, [_impl_evidence()])
        assert result["grounded"] is True

    def test_bullet_missing_evidence_ref_fails(self):
        bullet = GeneratedBullet(
            text="Deployed to production on AWS with K8s",
            evidence_ids=["ev-nonexistent"],
        )
        result = check_bullet_grounding(bullet, [_impl_evidence()])
        assert result["grounded"] is False


# ---------------------------------------------------------------------------
# No foreign tech keywords
# ---------------------------------------------------------------------------


class TestNoForeignTechKeywords:
    """Generated content must not mention tech not present in evidence."""

    def test_unmentioned_tech_not_matched(self):
        bullet = GeneratedBullet(
            text="Built a system using Kubernetes, Helm, Terraform, and Kafka",
            evidence_ids=["ev-impl-1"],
        )
        # Evidence only mentions: LangGraph, tool calling, Chroma, Hybrid search
        result = check_bullet_grounding(bullet, [_impl_evidence()])
        matched = {t.lower() for t in result.get("matched_terms", [])}
        for foreign in ["kubernetes", "helm", "terraform", "kafka"]:
            assert foreign not in matched, (
                f"'{foreign}' not in evidence, should not appear in matched_terms"
            )

    def test_evidence_tech_appears_in_matched_terms(self):
        bullet = GeneratedBullet(
            text="Implemented hybrid retrieval using LangGraph and Chroma",
            evidence_ids=["ev-impl-1"],
        )
        result = check_bullet_grounding(bullet, [_impl_evidence()])
        matched = {t.lower() for t in result.get("matched_terms", [])}
        # These ARE in the evidence and should match
        expected_present = {"langgraph", "chroma"}
        found = expected_present & matched
        assert found, (
            f"Tech present in evidence should be matched, "
            f"expected {expected_present}, got matched={matched}"
        )


# ---------------------------------------------------------------------------
# FaithfulnessChecker aggregate scoring
# ---------------------------------------------------------------------------


class TestFaithfulnessCheckerWithMixedStatus:
    """Full faithfulness check across mixed evidence statuses."""

    def test_mixed_status_scores_appropriately(self):
        checker = FaithfulnessChecker(pass_threshold=0.75)
        bullets = [
            GeneratedBullet(
                text="Built RAG pipeline with LangGraph and Chroma",
                evidence_ids=["ev-impl-1"],
                confidence=0.90,
            ),
            GeneratedBullet(
                text="Designed MCP protocol integration for external tools",
                evidence_ids=["ev-designed-1"],
                confidence=0.70,
            ),
            GeneratedBullet(
                text="Deployed distributed multi-agent system with Kafka",
                evidence_ids=["ev-planned-1"],
                confidence=0.30,
            ),
        ]
        evidences = [_impl_evidence(), _designed_evidence(), _planned_evidence()]
        report = checker.check(bullets, evidences)

        assert isinstance(report, FaithfulnessReport)
        assert isinstance(report.faithfulness_score, float)
        assert 0.0 <= report.faithfulness_score <= 1.0
        # The planned evidence bullet should drag down the score
        assert report.faithfulness_score < 0.90, (
            f"Mixed-status bullets should score <0.90, "
            f"got {report.faithfulness_score:.2f}"
        )
        assert len(report.details) == 3, (
            f"Should report on all 3 bullets, got {len(report.details)}"
        )

    def test_all_grounded_bullets_pass(self):
        checker = FaithfulnessChecker(pass_threshold=0.75)
        bullets = [
            GeneratedBullet(
                text="Implemented Agent workflow with LangGraph",
                evidence_ids=["ev-impl-1"],
                confidence=0.90,
            ),
            GeneratedBullet(
                text="Built hybrid retrieval combining keyword and embedding",
                evidence_ids=["ev-impl-1"],
                confidence=0.85,
            ),
        ]
        evidences = [_impl_evidence()]
        report = checker.check(bullets, evidences)
        assert report.decision == "pass", (
            f"All-grounded bullets should pass, got decision={report.decision}"
        )
        assert report.faithfulness_score >= 0.75, (
            f"All-grounded bullets should score >=0.75, got {report.faithfulness_score:.2f}"
        )

    def test_empty_bullets_pass_with_perfect_score(self):
        checker = FaithfulnessChecker()
        report = checker.check([], [])
        assert report.faithfulness_score == 1.0
        assert report.decision == "pass"
        assert report.unsupported_claims == []

    def test_all_ungrounded_bullets_fail(self):
        checker = FaithfulnessChecker()
        bullets = [
            GeneratedBullet(
                text="Claim A without evidence",
                evidence_ids=["ev-fake-1"],
            ),
            GeneratedBullet(
                text="Claim B without evidence",
                evidence_ids=["ev-fake-2"],
            ),
        ]
        report = checker.check(bullets, [_impl_evidence()])
        assert report.faithfulness_score < 0.50, (
            f"All-ungrounded bullets should score <0.50, "
            f"got {report.faithfulness_score:.2f}"
        )
        assert report.decision == "revise_required"
        assert len(report.unsupported_claims) == 2
