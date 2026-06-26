"""Conversation Memory — short-term dialog + long-term persistent knowledge.

Short-term: in-memory list for current session context.
Long-term : JSONL-persisted conversation history with BM25 retrieval.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


@dataclass
class MemoryEntry:
    """A single entry in the conversation memory."""
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


class ConversationMemory:
    """Dual-layer memory for Agent conversations.

    Short-term: last N messages in memory (fast, for current context).
    Long-term : JSONL file on disk + BM25 retrieval (for past sessions).

    Parameters
    ----------
    memory_dir : str
        Directory for persistent memory storage.
    short_term_limit : int
        Max messages to keep in short-term memory (default 20).
    """

    def __init__(
        self,
        memory_dir: str = "runtime/memory",
        short_term_limit: int = 20,
    ) -> None:
        self._dir = Path(memory_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._history_file = self._dir / "conversations.jsonl"
        self._short_term: list[MemoryEntry] = []
        self._short_term_limit = short_term_limit
        self._bm25: Any = None
        self._bm25_dirty = True

    # -- short-term memory ---------------------------------------------------

    def remember(self, role: str, content: str, **meta: Any) -> None:
        """Add a message to short-term memory and persist."""
        entry = MemoryEntry(role=role, content=content, metadata=meta)
        self._short_term.append(entry)
        if len(self._short_term) > self._short_term_limit:
            self._short_term = self._short_term[-self._short_term_limit:]
        self._persist(entry)
        self._bm25_dirty = True

    def user_says(self, content: str) -> None:
        self.remember("user", content)

    def assistant_says(self, content: str, **meta: Any) -> None:
        self.remember("assistant", content, **meta)

    def get_context(self, n: int = 10) -> list[MemoryEntry]:
        """Return last N messages as context for LLM."""
        return self._short_term[-n:]

    def context_text(self, n: int = 10) -> str:
        """Return last N messages formatted for LLM prompt."""
        lines = []
        for e in self.get_context(n):
            role_label = {"user": "用户", "assistant": "助手", "system": "系统"}.get(e.role, e.role)
            lines.append(f"[{role_label}]: {e.content[:300]}")
        return "\n".join(lines)

    def clear_short_term(self) -> None:
        self._short_term.clear()

    # -- long-term memory ----------------------------------------------------

    def recall(self, query: str, top_k: int = 3) -> list[MemoryEntry]:
        """Retrieve relevant past conversations using BM25."""
        entries = list(self._iter_history())
        if not entries:
            return []
        texts = [e.content for e in entries]
        try:
            from career_agent.rag.retrievers.bm25_retriever import BM25Retriever
            from career_agent.rag.schemas import DocumentChunk
        except ImportError:
            return []
        ret = BM25Retriever()
        chunks = [
            DocumentChunk(
                chunk_id=f"mem-{i}", document_id="memory",
                content=texts[i], source_path="memory",
                metadata={"role": entries[i].role, "timestamp": entries[i].timestamp},
            )
            for i in range(len(texts))
        ]
        if not chunks:
            return []
        ret.add_chunks(chunks)
        results = ret.search(query, top_k=top_k)
        matched = {r.chunk_id: r.score for r in results}
        recalled = [(entries[i], matched[cid]) for i in range(len(entries))
                    if (cid := f"mem-{i}") in matched]
        recalled.sort(key=lambda x: -x[1])
        return [e for e, _s in recalled[:top_k]]

    def summary(self) -> str:
        """Generate a lightweight summary of the current session."""
        entries = self._short_term
        if not entries:
            return "暂无对话记录"
        topics: list[str] = []
        for e in entries:
            if e.role == "user":
                topics.append(e.content[:60])
        return f"共 {len(entries)} 条对话。最近话题: {'; '.join(topics[-5:])}"

    # -- internal ------------------------------------------------------------

    def _persist(self, entry: MemoryEntry) -> None:
        with self._history_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "role": entry.role,
                "content": entry.content,
                "timestamp": entry.timestamp,
                "metadata": entry.metadata,
            }, ensure_ascii=False) + "\n")

    def _iter_history(self):
        if not self._history_file.is_file():
            return
        import os
        # Read last N lines for large files
        with self._history_file.open(encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines[-200:]:  # last 200 entries
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                yield MemoryEntry(
                    role=d.get("role", "user"),
                    content=d.get("content", ""),
                    timestamp=d.get("timestamp", ""),
                    metadata=d.get("metadata", {}),
                )
            except Exception:
                continue

    def _ensure_bm25(self) -> None:
        if not self._bm25_dirty and self._bm25 is not None:
            return
        self._bm25_dirty = False
