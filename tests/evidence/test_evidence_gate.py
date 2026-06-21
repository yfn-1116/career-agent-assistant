"""Tests for evidence gate."""

from career_agent.evidence.gate import EvidenceGate
from career_agent.profile.schema import (
    STATUS_DESIGNED, STATUS_IMPLEMENTED, STATUS_PLANNED, STATUS_UNCERTAIN,
)


class TestEvidenceGate:
    def test_implemented_allows_build_claim(self):
        gate = EvidenceGate()
        r = gate.validate("基于 LangGraph 构建了 Agent workflow", STATUS_IMPLEMENTED)
        assert r.allowed

    def test_designed_rejects_implemented_verb(self):
        gate = EvidenceGate()
        r = gate.validate("完整实现了 MCP 协议和工具调用系统", STATUS_DESIGNED)
        assert not r.allowed
        assert r.blocked_reason

    def test_designed_downgrades_text(self):
        gate = EvidenceGate()
        r = gate.validate("构建了 MCP 系统", STATUS_DESIGNED)
        assert r.downgraded_text
        assert "设计" in r.downgraded_text or "规划" in r.downgraded_text

    def test_planned_blocked(self):
        gate = EvidenceGate()
        r = gate.validate("完成了 Docker 部署", STATUS_PLANNED)
        assert not r.allowed

    def test_uncertain_blocked(self):
        gate = EvidenceGate()
        r = gate.validate("实现了 CI/CD pipeline", STATUS_UNCERTAIN)
        assert not r.allowed

    def test_no_evidence_blocked(self):
        gate = EvidenceGate()
        r = gate.block_unsupported("掌握了 K8s 集群管理")
        assert not r.allowed
        assert "无 evidence" in r.blocked_reason

    def test_exaggeration_warns(self):
        gate = EvidenceGate()
        r = gate.validate("完整实现了 MCP 协议", STATUS_IMPLEMENTED)
        assert r.allowed  # implemented allows it
        assert len(r.warnings) > 0  # but warns about exaggeration

    def test_local_demo_not_production(self):
        """If evidence only says '本地 demo', claiming '生产级部署' should be blocked."""
        gate = EvidenceGate()
        r = gate.validate("完成生产级部署上线", STATUS_PLANNED)
        assert not r.allowed
