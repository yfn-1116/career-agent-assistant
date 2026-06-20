"""In-memory keyword-based vector store replacement for Phase 1."""

import re

from career_agent.rag.schemas import DocumentChunk, RetrievedEvidence
from career_agent.rag.vectorstores.base import VectorStore


class MemoryVectorStore(VectorStore):
    """Store chunks in memory and search them with lightweight token overlap."""

    def __init__(self) -> None:
        self._chunks: list[DocumentChunk] = []

    def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        self._chunks.extend(chunks)

    def search(self, query: str, top_k: int = 5) -> list[RetrievedEvidence]:
        query_tokens = self._tokenize(query)
        if not query_tokens or top_k <= 0:
            return []

        scored: list[tuple[float, DocumentChunk, list[str]]] = []
        for chunk in self._chunks:
            content_tokens = self._tokenize(chunk.content)
            matched = sorted(query_tokens & content_tokens)
            if not matched:
                continue
            score = len(matched) / len(query_tokens)
            scored.append((score, chunk, matched))

        scored.sort(key=lambda item: (-item[0], item[1].chunk_index, item[1].chunk_id))
        return [
            self._to_evidence(chunk=chunk, score=score, matched_keywords=matched)
            for score, chunk, matched in scored[:top_k]
        ]

    def clear(self) -> None:
        self._chunks.clear()

    def count(self) -> int:
        return len(self._chunks)

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return {token for token in re.findall(r"[\w\u4e00-\u9fff]+", text) if token}

    @staticmethod
    def _to_evidence(
        chunk: DocumentChunk, score: float, matched_keywords: list[str]
    ) -> RetrievedEvidence:
        metadata = {**chunk.metadata, "vectorstore": "memory"}
        return RetrievedEvidence(
            evidence_id=f"evidence-{chunk.chunk_id}",
            chunk_id=chunk.chunk_id,
            title=str(chunk.metadata.get("title", "")),
            content=chunk.content,
            score=score,
            source_path=chunk.source_path,
            matched_keywords=matched_keywords,
            metadata=metadata,
        )
