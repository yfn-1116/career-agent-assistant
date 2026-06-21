"""Domain schemas — pure data models for the Agentic RAG system.

These models have zero dependencies on LangGraph, FastAPI, Streamlit,
or any specific vector store / LLM provider.
"""

from career_agent.domain.schemas import (
    AgentDecision,
    DocumentChunk,
    Evidence,
    GeneratedBullet,
    MatchAnalysis,
    ParsedJD,
    RetrievedChunk,
    RetrievalQuery,
    RetrievalScore,
    ToolCallTrace,
    WorkflowTrace,
)
from career_agent.domain.validation import (
    MAX_SCORE,
    MIN_SCORE,
    validate_score,
)

__all__ = [
    "AgentDecision",
    "DocumentChunk",
    "Evidence",
    "GeneratedBullet",
    "MatchAnalysis",
    "MAX_SCORE",
    "MIN_SCORE",
    "ParsedJD",
    "RetrievedChunk",
    "RetrievalQuery",
    "RetrievalScore",
    "ToolCallTrace",
    "WorkflowTrace",
    "validate_score",
]
