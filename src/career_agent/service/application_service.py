"""Application-record service used by UI and API layers."""

from __future__ import annotations

import uuid
from pathlib import Path

from career_agent.applications.repository import ApplicationRecord, ApplicationRepository
from career_agent.service.agent_run import AgentRunResult


class ApplicationService:
    """Small wrapper around ApplicationRepository for AgentRunResult persistence."""

    def __init__(self, runtime_dir: str | Path = "runtime") -> None:
        self.runtime_dir = Path(runtime_dir)
        self.repository = ApplicationRepository(
            str(self.runtime_dir / "applications" / "applications.jsonl")
        )

    def save_from_agent_result(
        self,
        result: AgentRunResult,
        *,
        job_title: str,
        company: str = "",
        jd_text: str = "",
        status: str = "analyzed",
    ) -> ApplicationRecord:
        summary = result.match_summary or {}
        record = ApplicationRecord(
            application_id=uuid.uuid4().hex[:12],
            company=company,
            job_title=job_title,
            jd_text=jd_text[:500],
            match_score=result.match_score,
            matched_skills=list(summary.get("matched_skills", [])),
            missing_skills=list(summary.get("missing_skills", [])),
            communication_script=result.communication_script,
            status=status,
            trace_id=result.trace_id,
            report_path=result.report_path,
            diagnostics_path=result.diagnostics_path,
        )
        self.repository.save(record)
        return record

    def create_manual_record(
        self,
        *,
        job_title: str,
        company: str = "",
        source_url: str = "",
        status: str = "planned",
        notes: str = "",
        generated_message: str = "",
    ) -> ApplicationRecord:
        record = ApplicationRecord(
            application_id=uuid.uuid4().hex[:12],
            company=company,
            job_title=job_title,
            source_url=source_url,
            notes=notes,
            communication_script=generated_message,
            status=status,
        )
        self.repository.save(record)
        return record

    def list_records(self) -> list[ApplicationRecord]:
        return self.repository.list_all()
