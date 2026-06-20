"""Text chunker for splitting ProfileDocument content into DocumentChunk objects."""

import re
from copy import deepcopy

from career_agent.rag.schemas import DocumentChunk, ProfileDocument


class TextChunker:
    """Clean and split profile documents into overlapping character-based chunks.

    Each chunk inherits the parent document's ``document_id``, ``source_path``,
    and ``metadata``, with additional chunk-specific metadata appended.

    Usage::

        chunker = TextChunker(chunk_size=800, overlap=100)
        chunks = chunker.chunk_documents(docs)
    """

    def __init__(self, chunk_size: int = 800, overlap: int = 100) -> None:
        if overlap >= chunk_size:
            raise ValueError(
                f"overlap ({overlap}) must be less than chunk_size ({chunk_size})"
            )
        if chunk_size < 1:
            raise ValueError(f"chunk_size must be positive, got {chunk_size}")
        if overlap < 0:
            raise ValueError(f"overlap must be non-negative, got {overlap}")

        self.chunk_size = chunk_size
        self.overlap = overlap

    # -- public API ----------------------------------------------------------

    def chunk_document(self, doc: ProfileDocument) -> list[DocumentChunk]:
        """Split a single ProfileDocument into DocumentChunk objects.

        Returns an empty list when ``doc.content`` is empty after cleaning.
        """
        cleaned = self.clean_text(doc.content)
        if not cleaned:
            return []

        segments = self._split_text(cleaned)
        return self._build_chunks(doc, segments)

    def chunk_documents(self, docs: list[ProfileDocument]) -> list[DocumentChunk]:
        """Split a list of ProfileDocument objects into DocumentChunk objects."""
        chunks: list[DocumentChunk] = []
        for doc in docs:
            chunks.extend(self.chunk_document(doc))
        return chunks

    # -- text cleaning -------------------------------------------------------

    @staticmethod
    def clean_text(text: str) -> str:
        """Normalise whitespace in Markdown text while preserving structure.

        * Strip leading / trailing whitespace.
        * Normalise line endings to ``\\n``.
        * Collapse sequences of 3+ blank lines down to 2.
        * Preserve Markdown headings and list markers.
        """
        text = text.strip()
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Collapse 3+ consecutive blank lines to 2
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text

    # -- internal ------------------------------------------------------------

    def _split_text(self, text: str) -> list[str]:
        """Divide ``text`` into overlapping character windows."""
        step = self.chunk_size - self.overlap
        segments: list[str] = []
        start = 0
        while start < len(text):
            window = text[start : start + self.chunk_size]
            segments.append(window)
            start += step
        return segments

    def _build_chunks(
        self, doc: ProfileDocument, segments: list[str]
    ) -> list[DocumentChunk]:
        """Create DocumentChunk objects from the parent document and segments."""
        base_meta = deepcopy(doc.metadata)
        chunks: list[DocumentChunk] = []
        for idx, segment in enumerate(segments):
            chunk_id = f"{doc.document_id}_{idx}"
            chunk_meta = {
                **base_meta,
                "chunk_size": self.chunk_size,
                "overlap": self.overlap,
                "chunk_index": idx,
                "chunker": "text_chunker",
            }
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=doc.document_id,
                    content=segment,
                    chunk_index=idx,
                    source_path=doc.source_path,
                    metadata=chunk_meta,
                )
            )
        return chunks
