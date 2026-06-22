"""Job analysis routes."""

from fastapi import APIRouter

from career_agent.api.schemas import JobAnalyzeRequest, JobAnalyzeResponse
from career_agent.service.agent_run import AgentRunService

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

AGENT_SERVICE = AgentRunService()


@router.post("/analyze", response_model=JobAnalyzeResponse)
def analyze_job(request: JobAnalyzeRequest) -> JobAnalyzeResponse:
    result = AGENT_SERVICE.analyze_job(
        request.jd_text,
        user_message=request.title or request.jd_text,
    )
    matched = list(result.match_summary.get("matched_skills", []))
    missing = list(result.match_summary.get("missing_skills", []))
    return JobAnalyzeResponse(
        match_score=result.match_score,
        opportunity_score=result.match_score,
        recommendation=result.recommended_action,
        matched_skills=matched,
        missing_skills=missing,
        evidence=list(result.evidence_sources),
        warnings=list(result.warnings),
        approval_required=result.approval_required,
    )
