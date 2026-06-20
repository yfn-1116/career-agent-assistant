"""Embedding-backed vector store — uses EmbeddingProvider for similarity search."""

from career_agent.rag.embeddings.base import EmbeddingProvider
from career_agent.rag.schemas import DocumentChunk, RetrievedEvidence


class EmbeddingVectorStore:
    """A lightweight vector store backed by an EmbeddingProvider.

    Does NOT use numpy — pure-Python cosine similarity.
    This is a first-phase implementation for pipeline validation;
    swap in Chroma / FAISS for production.
    """

    def __init__(self, provider: EmbeddingProvider) -> None:
        self._provider = provider
        self._chunks: list[DocumentChunk] = []
        self._vectors: list[list[float]] = []

    # -- public API ---------------------------------------------------------

    def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        texts = [c.content for c in chunks]
        vectors = self._provider.embed_texts(texts)
        self._chunks.extend(chunks)
        self._vectors.extend(vectors)

    def search(self, query: str, top_k: int = 5) -> list[RetrievedEvidence]:
        if not query.strip() or not self._chunks:
            return []

        query_vec = self._provider.embed_text(query)
        scored = [
            (self._cosine(query_vec, vec), i)
            for i, vec in enumerate(self._vectors)
        ]
        scored.sort(key=lambda x: x[0], reverse=True)

        results: list[RetrievedEvidence] = []
        for score, idx in scored[:top_k]:
            chunk = self._chunks[idx]
            results.append(
                RetrievedEvidence(
                    evidence_id=f"emb-{chunk.chunk_id}",
                    chunk_id=chunk.chunk_id,
                    title=chunk.metadata.get("filename", ""),
                    content=chunk.content,
                    score=round(score, 4),
                    source_path=chunk.source_path,
                    matched_keywords=[],
                    metadata={**chunk.metadata, "store": "embedding_vector_store"},
                )
            )
        return results

    def clear(self) -> None:
        self._chunks.clear()
        self._vectors.clear()

    def count(self) -> int:
        return len(self._chunks)

    # -- internal -----------------------------------------------------------

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(y * y for y in b) ** 0.5
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)
