"""Profile loader — converts documents to structured ProfileItems with status inference."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from career_agent.profile.schema import (
    STATUS_DESIGNED,
    STATUS_IMPLEMENTED,
    STATUS_PLANNED,
    STATUS_UNCERTAIN,
    ProfileItem,
)
from career_agent.rag.schemas import ProfileDocument


class ProfileLoader:
    """Load documents and infer profile item status from content signals.

    Status inference rules:
    - architecture/spec/design/task docs → designed or planned
    - README, project docs, completion logs → implemented
    - Unknown content → uncertain
    """

    # Signals that suggest "implemented" status
    _IMPLEMENTED_SIGNALS = [
        r"\b(?:完成|部署|上线|实现|构建|开发|delivered|deployed|implemented|built)\b",
        r"pytest.*passed|测试.*通过|\d+ passed",
        r"#\s*(?:项目经历|Project|Implementation)",
        r"技术栈[：:].+",
    ]

    # Signals that suggest "designed" status
    _DESIGNED_SIGNALS = [
        r"\b(?:设计|架构|方案|预留|接口|design|architecture|spec|plan)\b",
        r"#\s*(?:架构设计|系统设计|Design Doc)",
        r"预留.*接口|interface.*reserved",
    ]

    # Signals that suggest "planned" status
    _PLANNED_SIGNALS = [
        r"\b(?:计划|后续|TODO|FIXME|roadmap|planned|future)\b",
        r"后续.*扩展|future.*extension",
    ]

    def load(self, doc: ProfileDocument) -> ProfileItem:
        """Convert a ProfileDocument to a ProfileItem with inferred status."""
        item_id = hashlib.sha256(doc.source_path.encode()).hexdigest()[:16]
        content = doc.content
        status = self._infer_status(content, doc.source_path)
        claims = self._extract_claims(content)
        skills = self._extract_skills(content)

        return ProfileItem(
            item_id=item_id,
            source_path=doc.source_path,
            source_type=doc.item_type,
            title=doc.title or Path(doc.source_path).stem,
            skills=skills,
            claims=claims,
            status=status,
            confidence=0.7 if status != STATUS_UNCERTAIN else 0.3,
            raw_content=content,
        )

    def load_documents(self, docs: list[ProfileDocument]) -> list[ProfileItem]:
        return [self.load(d) for d in docs]

    @classmethod
    def _infer_status(cls, content: str, source_path: str) -> str:
        path_lower = source_path.lower()

        # Architecture/docs/spec/task files → designed
        if any(kw in path_lower for kw in ["architecture", "design", "spec", "01-", "02-"]):
            impl_score = cls._count_matches(content, cls._IMPLEMENTED_SIGNALS)
            design_score = cls._count_matches(content, cls._DESIGNED_SIGNALS)
            if impl_score > design_score:
                return STATUS_IMPLEMENTED
            return STATUS_DESIGNED

        # README, project, runbook → implemented
        impl_score = cls._count_matches(content, cls._IMPLEMENTED_SIGNALS)
        design_score = cls._count_matches(content, cls._DESIGNED_SIGNALS)
        planned_score = cls._count_matches(content, cls._PLANNED_SIGNALS)

        if impl_score > 0:
            return STATUS_IMPLEMENTED
        if design_score > 0:
            return STATUS_DESIGNED
        if planned_score > 0:
            return STATUS_PLANNED
        return STATUS_UNCERTAIN

    @staticmethod
    def _count_matches(text: str, patterns: list[str]) -> int:
        return sum(len(re.findall(p, text, re.IGNORECASE)) for p in patterns)

    @staticmethod
    def _extract_claims(text: str) -> list[str]:
        """Extract ability claims from text."""
        claims = []
        # Find lines with tech stack, achievements, or capability statements
        for pattern in [
            r"(?:实现|构建|开发|完成|使用|基于|利用)[^。\n]{10,80}",
            r"(?:负责|参与|独立完成)[^。\n]{10,80}",
        ]:
            for m in re.finditer(pattern, text):
                claim = m.group().strip()[:120]
                if claim not in claims:
                    claims.append(claim)
        return claims[:10]

    @staticmethod
    def _extract_skills(text: str) -> list[str]:
        """Extract technical skills from text."""
        skills = set()
        # Match capitalized tech terms and Chinese tech terms
        for m in re.finditer(
            r"\b([A-Z][a-zA-Z0-9+#.]{2,}(?:/[A-Z][a-zA-Z0-9+#.]*)?)\b",
            text,
        ):
            skills.add(m.group(1))
        return sorted(skills)[:20]
