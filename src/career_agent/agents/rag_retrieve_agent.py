"""RAG retrieve agent — queries the RAG pipeline for user profile evidence."""

from pathlib import Path

from career_agent.agents.state import ParsedJD
from career_agent.rag.pipeline import RAGPipeline
from career_agent.rag.schemas import RetrievedEvidence


class RAGRetrieveAgent:
    """Retrieve evidence from the user profile knowledge base.

    Wraps a ``RAGPipeline`` and translates ``ParsedJD`` into retrieval
    queries.  No external model calls — the pipeline uses keyword matching.
    """

    def __init__(self, pipeline: RAGPipeline | None = None) -> None:
        self.pipeline = pipeline or RAGPipeline()

    def ingest_profile_dir(self, profile_dir: str | Path) -> None:
        """Load and index all Markdown files under *profile_dir*."""
        self.pipeline.build_index(profile_dir)

    def build_query_from_parsed_jd(self, parsed_jd: ParsedJD) -> str:
        """Compose a retrieval query from the parsed JD fields."""
        parts: list[str] = []

        if parsed_jd.job_direction and parsed_jd.job_direction != "general":
            parts.append(parsed_jd.job_direction)

        if parsed_jd.hard_skills:
            parts.extend(parsed_jd.hard_skills[:8])

        if parsed_jd.bonus_skills:
            parts.extend(parsed_jd.bonus_skills[:5])

        if parsed_jd.keywords:
            extra = [kw for kw in parsed_jd.keywords[:10]
                     if kw not in parts]
            parts.extend(extra)

        return " ".join(parts) if parts else ""

    def retrieve(
        self, parsed_jd: ParsedJD, top_k: int = 5
    ) -> list[RetrievedEvidence]:
        """Retrieve evidence for a parsed JD."""
        query = self.build_query_from_parsed_jd(parsed_jd)
        if not query:
            return []
        return self.pipeline.retrieve(query=query, top_k=top_k)

    def retrieve_by_query(
        self, query: str, top_k: int = 5
    ) -> list[RetrievedEvidence]:
        """Retrieve evidence with a raw query string."""
        if not query.strip():
            return []
        return self.pipeline.retrieve(query=query.strip(), top_k=top_k)
