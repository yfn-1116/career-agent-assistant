"""JobPosting schema — structured job posting from any source."""

from __future__ import annotations
import dataclasses
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid


@dataclass
class JobPosting:
    job_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    platform: str = ""
    source_type: str = "manual"  # manual / sample / file / browser_text / url
    company: str = ""
    job_title: str = ""
    salary: str = ""
    location: str = ""
    education: str = ""
    experience: str = ""
    hr_name: str = ""
    job_url: str = ""
    jd_text: str = ""
    hard_skills: list[str] = field(default_factory=list)
    soft_skills: list[str] = field(default_factory=list)
    responsibilities: list[str] = field(default_factory=list)
    benefits: list[str] = field(default_factory=list)
    raw_text: str = ""
    extracted_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in dataclasses.fields(self)}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> JobPosting:
        fields = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in fields})
