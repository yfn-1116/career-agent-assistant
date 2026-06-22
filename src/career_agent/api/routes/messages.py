"""Communication-message routes."""

from fastapi import APIRouter

from career_agent.api.schemas import GenerateMessageRequest, GenerateMessageResponse
from career_agent.service.agent_run import AgentRunService

router = APIRouter(prefix="/api/messages", tags=["messages"])

AGENT_SERVICE = AgentRunService()


@router.post("/generate", response_model=GenerateMessageResponse)
def generate_message(request: GenerateMessageRequest) -> GenerateMessageResponse:
    result = AGENT_SERVICE.generate_message(
        job_title=request.job_id or "该岗位",
        matched_skills=[],
        evidence_paths=[],
    )
    return GenerateMessageResponse(
        message=result.communication_script,
        evidence_used=list(result.evidence_sources),
        warnings=list(result.warnings),
        approval_required=result.approval_required,
    )
