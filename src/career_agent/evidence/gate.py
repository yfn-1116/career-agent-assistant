"""Evidence Gate — prevents claiming "implemented" for "designed/planned" things."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from career_agent.profile.schema import (
    STATUS_DESIGNED,
    STATUS_IMPLEMENTED,
    STATUS_PLANNED,
    STATUS_UNCERTAIN,
)

# Claim → allowed verbs per status
_ALLOWED_VERBS = {
    STATUS_IMPLEMENTED: ["实现", "构建", "完成", "开发", "部署", "上线", "built", "implemented", "developed", "deployed"],
    STATUS_DESIGNED: ["设计", "规划", "架构", "预留", "designed", "architected", "planned", "reserved"],
    STATUS_PLANNED: ["计划", "后续", "planned", "roadmap", "future"],
    STATUS_UNCERTAIN: [],
}

# Exaggeration patterns to detect
_EXAGGERATION_PATTERNS = [
    (r"完整(?:实现|开发|部署)", "完整"),
    (r"全面(?:覆盖|支持)", "全面"),
    (r"深度(?:优化|集成)", "深度"),
    (r"大规模(?:部署|应用)", "大规模"),
    (r"生产(?:级|环境|部署)", "生产级"),
    (r"线上(?:运行|部署|服务)", "线上"),
]


@dataclass
class EvidenceResult:
    """Result of evidence gate validation."""

    claim_text: str = ""
    evidence_status: str = ""
    allowed: bool = False
    downgraded_text: str = ""
    warnings: list[str] = field(default_factory=list)
    blocked_reason: str = ""


class EvidenceGate:
    """Validate whether a generated claim is supported by evidence status.

    Rules:
    - implemented evidence → can write "built/implemented"
    - designed evidence → must downgrade to "designed/planned"
    - planned evidence → cannot claim completion
    - uncertain/no evidence → blocked
    """

    def validate(self, claim: str, evidence_status: str) -> EvidenceResult:
        """Check a claim against evidence status."""
        result = EvidenceResult(claim_text=claim, evidence_status=evidence_status)

        if evidence_status == STATUS_IMPLEMENTED:
            # Check for exaggerations in implemented claims
            for pattern, label in _EXAGGERATION_PATTERNS:
                if self._contains(claim, pattern):
                    result.warnings.append(f"措辞检查：'{label}' 可能夸大，请确认 evidence 是否支撑")
            result.allowed = True
            return result

        if evidence_status == STATUS_DESIGNED:
            # Must not use "implemented" verbs
            for verb in _ALLOWED_VERBS[STATUS_IMPLEMENTED]:
                if self._contains(claim, verb):
                    result.blocked_reason = f"evidence 状态为 designed，不能使用 '{verb}'，应替换为设计/规划类措辞"
                    result.downgraded_text = self._downgrade(claim)
                    return result
            result.allowed = True
            return result

        if evidence_status == STATUS_PLANNED:
            result.blocked_reason = "evidence 状态为 planned，不能作为已完成经历写入简历"
            return result

        # UNCERTAIN or unknown
        result.blocked_reason = "缺少 evidence 支撑，不能写入简历"
        return result

    def block_unsupported(self, claim: str) -> EvidenceResult:
        """Block a claim with no evidence at all."""
        return EvidenceResult(
            claim_text=claim,
            evidence_status="none",
            allowed=False,
            blocked_reason="无 evidence 支撑，拒绝生成",
        )

    @staticmethod
    def _contains(text: str, pattern: str) -> bool:
        import re
        return bool(re.search(pattern, text))

    @staticmethod
    def _downgrade(claim: str) -> str:
        """Replace implementation verbs with design verbs."""
        replacements = [
            ("实现了", "设计了"), ("构建了", "规划了"), ("完成了", "设计了"),
            ("开发了", "设计了"), ("部署了", "规划了部署方案"),
            ("implemented", "designed"), ("built", "architected"),
            ("developed", "designed"),
        ]
        result = claim
        for old, new in replacements:
            result = result.replace(old, new)
        return result
