"""Knowledge-base routes."""

from fastapi import APIRouter

from career_agent.api.schemas import KnowledgeUploadRequest, KnowledgeUploadResponse
from career_agent.service.knowledge_base import KnowledgeBaseService

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

KNOWLEDGE_SERVICE = KnowledgeBaseService()


@router.post("/upload", response_model=KnowledgeUploadResponse)
def upload_knowledge(request: KnowledgeUploadRequest) -> KnowledgeUploadResponse:
    result = KNOWLEDGE_SERVICE.index_text(
        request.content,
        source_name=request.filename,
    )
    return KnowledgeUploadResponse(
        source_name=result.source_name,
        chunk_count=result.chunk_count,
        index_path=str(KNOWLEDGE_SERVICE.chunk_file),
        saved_path=str(result.saved_path) if result.saved_path else None,
    )
