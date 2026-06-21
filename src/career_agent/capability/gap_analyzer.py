"""Capability gap analyzer — long-term skill gap tracking."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CapabilityGapReport:
    analyzed_jobs_count: int = 0
    frequent_required_skills: list[tuple[str, int]] = field(default_factory=list)
    user_strong_skills: list[str] = field(default_factory=list)
    user_weak_skills: list[str] = field(default_factory=list)
    missing_skills_ranked: list[tuple[str, int]] = field(default_factory=list)
    recommended_project_improvements: list[str] = field(default_factory=list)
    recommended_resume_improvements: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "analyzed_jobs_count": self.analyzed_jobs_count,
            "frequent_required_skills": self.frequent_required_skills,
            "user_strong_skills": self.user_strong_skills,
            "user_weak_skills": self.user_weak_skills,
            "missing_skills_ranked": self.missing_skills_ranked,
            "recommended_project_improvements": self.recommended_project_improvements,
            "recommended_resume_improvements": self.recommended_resume_improvements,
        }


class CapabilityGapAnalyzer:
    """Analyze skill gaps across multiple job applications."""

    def analyze(
        self,
        applications: list[Any],
        profile_items: list[Any],
    ) -> CapabilityGapReport:
        if not applications:
            return CapabilityGapReport()

        # Collect all required skills across applications
        all_required: Counter[str] = Counter()
        all_missing: Counter[str] = Counter()
        for app in applications:
            for sk in getattr(app, "missing_skills", []):
                all_missing[sk.lower()] += 1
            for sk in getattr(app, "matched_skills", []):
                all_required[sk.lower()] += 1

        # Frequent required skills
        frequent = all_required.most_common(10)

        # User skills from profile
        strong = []
        weak = []
        for item in profile_items:
            status = getattr(item, "status", "")
            for sk in item.skills:
                if status == "implemented":
                    strong.append(sk)
                elif status in ("designed", "planned"):
                    weak.append(sk)

        # Ranked missing skills
        missing_ranked = all_missing.most_common(10)

        # Recommendations
        proj_recs = []
        resume_recs = []
        for sk, count in missing_ranked[:5]:
            if count >= 2:
                proj_recs.append(f"建议补充 {sk} 相关项目经历（{count} 个岗位要求）")
            resume_recs.append(f"简历可补充 {sk} 相关内容")

        return CapabilityGapReport(
            analyzed_jobs_count=len(applications),
            frequent_required_skills=frequent,
            user_strong_skills=sorted(set(strong))[:15],
            user_weak_skills=sorted(set(weak))[:15],
            missing_skills_ranked=missing_ranked,
            recommended_project_improvements=proj_recs[:5],
            recommended_resume_improvements=resume_recs[:5],
        )
