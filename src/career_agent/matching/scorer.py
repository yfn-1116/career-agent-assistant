"""Evidence-based job matching scorer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from career_agent.profile.schema import STATUS_IMPLEMENTED


@dataclass
class SkillMatch:
    skill: str = ""
    status: str = "missing"  # strong / medium / weak / missing
    evidence_ids: list[str] = field(default_factory=list)
    source_paths: list[str] = field(default_factory=list)
    explanation: str = ""


@dataclass
class JobMatchResult:
    job_id: str = ""
    job_title: str = ""
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    weak_skills: list[str] = field(default_factory=list)
    skill_evidence_map: dict[str, list[str]] = field(default_factory=dict)
    match_score: float = 0.0
    confidence: float = 0.0
    recommended_action: str = "not_priority"
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id, "job_title": self.job_title,
            "required_skills": self.required_skills, "preferred_skills": self.preferred_skills,
            "matched_skills": self.matched_skills, "missing_skills": self.missing_skills,
            "weak_skills": self.weak_skills, "skill_evidence_map": self.skill_evidence_map,
            "match_score": self.match_score, "confidence": self.confidence,
            "recommended_action": self.recommended_action, "reasons": self.reasons,
        }


class JobMatchScorer:
    """Score job match based on profile evidence strength.

    Formula:
        match_score = 0.40 * skill_coverage + 0.25 * evidence_strength
                    + 0.15 * project_relevance + 0.10 * source_confidence
                    + 0.10 * gap_penalty_adjusted
    """

    def score(
        self,
        job_title: str,
        required_skills: list[str],
        preferred_skills: list[str],
        profile_items: list[Any],
        evidence_map: dict[str, list[Any]] | None = None,
    ) -> JobMatchResult:
        em = evidence_map or {}
        all_required = [s.strip().lower() for s in required_skills if s.strip()]
        all_preferred = [s.strip().lower() for s in preferred_skills if s.strip()]

        # Build skill→evidence mapping from profile items
        skill_ev: dict[str, list[str]] = {}
        for item in profile_items:
            for skill in item.skills:
                sk = skill.strip().lower()
                if sk not in skill_ev:
                    skill_ev[sk] = []
                if item.source_path not in skill_ev[sk]:
                    skill_ev[sk].append(item.source_path)

        # Classify each required skill
        matched, missing, weak = [], [], []
        for sk in all_required:
            if sk in skill_ev and skill_ev[sk]:
                has_implemented = any(
                    getattr(item, "status", "") == STATUS_IMPLEMENTED
                    for item in profile_items
                    if sk in [s.lower() for s in getattr(item, "skills", [])]
                )
                if has_implemented:
                    matched.append(sk)
                else:
                    weak.append(sk)  # exists but not implemented
            else:
                missing.append(sk)

        for sk in all_preferred:
            if sk in skill_ev and skill_ev[sk]:
                if sk not in matched:
                    matched.append(sk)

        # Compute scores
        total_req = len(all_required) or 1
        skill_coverage = len(matched) / total_req
        evidence_strength = len([s for s in matched if s in skill_ev and len(skill_ev[s]) >= 2]) / max(total_req, 1)
        project_relevance = min(1.0, len(matched) / max(len(all_required + all_preferred), 1))
        source_confidence = sum(
            1.0 for item in profile_items if getattr(item, "confidence", 0) >= 0.7
        ) / max(len(profile_items), 1)
        gap_penalty = 1.0 - (len(missing) / max(total_req, 1))

        match_score = round(
            0.40 * skill_coverage + 0.25 * evidence_strength
            + 0.15 * project_relevance + 0.10 * source_confidence
            + 0.10 * gap_penalty,
            4,
        )

        # Decision
        if match_score >= 0.80:
            action = "strong_apply"
        elif match_score >= 0.65:
            action = "apply_with_resume_adjustment"
        elif match_score >= 0.50:
            action = "apply_only_if_interested"
        else:
            action = "not_priority"

        reasons = []
        if matched:
            reasons.append(f"匹配技能：{', '.join(matched[:8])}")
        if missing:
            reasons.append(f"缺失技能：{', '.join(missing[:8])}")
        if weak:
            reasons.append(f"弱证据技能：{', '.join(weak[:5])}")

        return JobMatchResult(
            job_id=job_title.replace(" ", "_").lower()[:20],
            job_title=job_title,
            required_skills=all_required,
            preferred_skills=all_preferred,
            matched_skills=matched,
            missing_skills=missing,
            weak_skills=weak,
            skill_evidence_map={sk: skill_ev.get(sk, []) for sk in matched},
            match_score=match_score,
            confidence=round(source_confidence, 2),
            recommended_action=action,
            reasons=reasons,
        )
