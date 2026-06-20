"""Simple retriever backed by a VectorStore."""

from career_agent.rag.schemas import RetrievedEvidence
from career_agent.rag.vectorstores.base import VectorStore


class SimpleRetriever:
    """Thin retrieval wrapper around the configured vector store."""

    def __init__(self, vectorstore: VectorStore) -> None:
        self.vectorstore = vectorstore

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedEvidence]:
        return self.vectorstore.search(query=query, top_k=top_k)
