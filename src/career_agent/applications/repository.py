"""Application memory — persistent job application records (JSONL file)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VALID_APP_STATUSES = {"analyzed", "planned", "applied", "interview", "rejected", "offer", "archived"}


@dataclass
class ApplicationRecord:
    application_id: str = ""
    company: str = ""
    job_title: str = ""
    jd_text: str = ""
    match_score: float = 0.0
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    generated_resume_path: str = ""
    communication_script: str = ""
    status: str = "analyzed"
    trace_id: str = ""
    report_path: str = ""
    diagnostics_path: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "application_id": self.application_id, "company": self.company,
            "job_title": self.job_title, "jd_text": self.jd_text,
            "match_score": self.match_score, "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills, "generated_resume_path": self.generated_resume_path,
            "communication_script": self.communication_script, "status": self.status,
            "trace_id": self.trace_id, "report_path": self.report_path,
            "diagnostics_path": self.diagnostics_path,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ApplicationRecord:
        return cls(**{k: d.get(k, v.default if hasattr(v, "default") else v)
                       for k, v in cls.__dataclass_fields__.items()})


class ApplicationRepository:
    """JSONL-file based application record store."""

    def __init__(self, path: str = "data/applications/applications.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, record: ApplicationRecord) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    def list_all(self) -> list[ApplicationRecord]:
        if not self.path.is_file():
            return []
        records = []
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(ApplicationRecord.from_dict(json.loads(line)))
                    except Exception:
                        pass
        return records

    def get(self, application_id: str) -> ApplicationRecord | None:
        for r in self.list_all():
            if r.application_id == application_id:
                return r
        return None

    def update_status(self, application_id: str, status: str) -> bool:
        records = self.list_all()
        updated = False
        with open(self.path, "w", encoding="utf-8") as f:
            for r in records:
                if r.application_id == application_id:
                    r.status = status
                    r.updated_at = datetime.now(timezone.utc).isoformat()
                    updated = True
                f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")
        return updated

    def count(self) -> int:
        return len(self.list_all())
