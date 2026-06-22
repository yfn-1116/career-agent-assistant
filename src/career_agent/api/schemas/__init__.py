"""Public API schema exports."""

from career_agent.api.schemas.application import ApplicationCreateRequest, ApplicationResponse
from career_agent.api.schemas.common import BrowserAgentResult, BrowserPageSnapshot, ErrorResponse, HealthResponse
from career_agent.api.schemas.job import JobAnalyzeRequest, JobAnalyzeResponse
from career_agent.api.schemas.knowledge import KnowledgeUploadRequest, KnowledgeUploadResponse
from career_agent.api.schemas.message import GenerateMessageRequest, GenerateMessageResponse

__all__ = [
    "ApplicationCreateRequest",
    "ApplicationResponse",
    "BrowserAgentResult",
    "BrowserPageSnapshot",
    "ErrorResponse",
    "GenerateMessageRequest",
    "GenerateMessageResponse",
    "HealthResponse",
    "JobAnalyzeRequest",
    "JobAnalyzeResponse",
    "KnowledgeUploadRequest",
    "KnowledgeUploadResponse",
]
