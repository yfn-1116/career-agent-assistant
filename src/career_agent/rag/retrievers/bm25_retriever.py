"""BM25 Retriever — keyword-based retrieval with jieba tokenization.

Replaces the pure token-intersection MemoryVectorStore.search() with
industry-standard BM25 (Okapi BM25) scoring: term frequency × inverse
document frequency × document length normalization.

Dependencies: pip install jieba rank_bm25
"""

from __future__ import annotations

from typing import Callable

import jieba
from rank_bm25 import BM25Okapi

from career_agent.rag.schemas import DocumentChunk, RetrievedEvidence


def _default_tokenize(text: str) -> list[str]:
    """Tokenize Chinese + English text with jieba."""
    return list(jieba.cut(text))


class BM25Retriever:
    """BM25 keyword retriever — indexes chunks and scores by relevance.

    Parameters
    ----------
    tokenize_fn : callable, optional
        Tokenizer function ``(text: str) -> list[str]``.
        Defaults to jieba.cut for Chinese support.
    """

    def __init__(
        self,
        tokenize_fn: Callable[[str], list[str]] | None = None,
    ) -> None:
        self._tokenize = tokenize_fn or _default_tokenize
        self._chunks: list[DocumentChunk] = []
        self._bm25: BM25Okapi | None = None
        self._tokenized: list[list[str]] = []

    # -- indexing -----------------------------------------------------------

    def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Index chunks for BM25 retrieval."""
        self._chunks.extend(chunks)
        self._tokenized.extend(
            self._tokenize(c.content) for c in chunks
        )
        # Rebuild BM25 index
        self._bm25 = BM25Okapi(self._tokenized)

    def clear(self) -> None:
        self._chunks.clear()
        self._tokenized.clear()
        self._bm25 = None

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    # -- retrieval ----------------------------------------------------------

    def search(
        self, query: str, top_k: int = 5
    ) -> list[RetrievedEvidence]:
        """Search chunks with BM25 scoring.

        Returns top_k RetrievedEvidence items sorted by BM25 score descending.
        """
        if not self._bm25 or not self._chunks:
            return []

        query_tokens = self._tokenize(query)
        scores = self._bm25.get_scores(query_tokens)

        # Pair (index, score) and sort descending
        ranked = sorted(
            enumerate(scores),
            key=lambda x: x[1],
            reverse=True,
        )[:top_k]

        results: list[RetrievedEvidence] = []
        for idx, score in ranked:
            chunk = self._chunks[idx]
            results.append(
                RetrievedEvidence(
                    evidence_id=f"bm25-{chunk.chunk_id}",
                    chunk_id=chunk.chunk_id,
                    title=chunk.metadata.get("filename", ""),
                    content=chunk.content,
                    score=float(score),
                    source_path=chunk.source_path,
                    matched_keywords=[
                        token for token in query_tokens
                        if token in self._tokenized[idx]
                    ],
                    metadata={
                        **chunk.metadata,
                        "retriever": "bm25",
                        "bm25_score": float(score),
                    },
                )
            )

        return results

    # -- RetrieverFn compatible ---------------------------------------------

    def __call__(
        self, query: str, top_k: int
    ) -> list[RetrievedEvidence]:
        """Allow BM25Retriever to be used as a RetrieverFn callback."""
        return self.search(query, top_k=top_k)
