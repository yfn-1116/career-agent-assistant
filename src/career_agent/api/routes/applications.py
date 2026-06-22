"""Application-record routes."""

from fastapi import APIRouter

from career_agent.api.schemas import ApplicationCreateRequest, ApplicationResponse
from career_agent.applications.repository import ApplicationRecord
from career_agent.service.application_service import ApplicationService

router = APIRouter(prefix="/api/applications", tags=["applications"])

APPLICATION_SERVICE = ApplicationService()


def _to_response(record: ApplicationRecord) -> ApplicationResponse:
    return ApplicationResponse(
        id=record.application_id,
        job_title=record.job_title,
        company=record.company,
        status=record.status,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.post("", response_model=ApplicationResponse)
def create_application(request: ApplicationCreateRequest) -> ApplicationResponse:
    record = APPLICATION_SERVICE.create_manual_record(
        job_title=request.job_title,
        company=request.company,
        source_url=request.source_url,
        status=request.status,
        notes=request.notes,
        generated_message=request.generated_message,
    )
    return _to_response(record)


@router.get("", response_model=list[ApplicationResponse])
def list_applications() -> list[ApplicationResponse]:
    return [_to_response(record) for record in APPLICATION_SERVICE.list_records()]
