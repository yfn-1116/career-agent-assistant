"""Application API schemas."""

from __future__ import annotations

from pydantic import BaseModel


class ApplicationCreateRequest(BaseModel):
    job_title: str
    company: str = ""
    source_url: str = ""
    status: str = "planned"
    notes: str = ""
    generated_message: str = ""


class ApplicationResponse(BaseModel):
    id: str
    job_title: str
    company: str = ""
    status: str = "planned"
    created_at: str = ""
    updated_at: str = ""
