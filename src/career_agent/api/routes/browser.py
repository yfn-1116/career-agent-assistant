"""Browser-extension compatibility routes."""

from fastapi import APIRouter

from career_agent.api.schemas import BrowserAgentResult, BrowserPageSnapshot
from career_agent.service.browser_service import BrowserAssistantService

router = APIRouter(prefix="/api/browser", tags=["browser"])

BROWSER_SERVICE = BrowserAssistantService()


@router.post("/analyze-current-page", response_model=BrowserAgentResult)
def analyze_current_page(snapshot: BrowserPageSnapshot) -> BrowserAgentResult:
    return BROWSER_SERVICE.analyze_current_page(snapshot)
