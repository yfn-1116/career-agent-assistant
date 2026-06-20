"""Vector store interface for first-phase RAG retrieval."""

from abc import ABC, abstractmethod

from career_agent.rag.schemas import DocumentChunk, RetrievedEvidence


class VectorStore(ABC):
    """Abstract interface for storing and searching document chunks."""

    @abstractmethod
    def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Add document chunks to the store."""

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> list[RetrievedEvidence]:
        """Return evidence ranked by relevance to query."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all stored chunks."""

    @abstractmethod
    def count(self) -> int:
        """Return the number of stored chunks."""
