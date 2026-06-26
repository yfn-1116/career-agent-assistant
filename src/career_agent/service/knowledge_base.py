"""Runtime knowledge-base service for demos and local UI state."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from career_agent.rag.chunking.text_chunker import TextChunker
from career_agent.rag.loaders.file_loader import FileLoader
from career_agent.rag.schemas import DocumentChunk, ProfileDocument, RetrievedEvidence
from career_agent.rag.vectorstores.memory_store import MemoryVectorStore


def _guess_source_type(source_path: str, metadata: dict | None = None) -> str:
    """Guess the source type from filename or metadata."""
    if metadata:
        item_type = str(metadata.get("item_type", "")).lower()
        if item_type:
            return item_type
    path = (source_path or "").lower()
    if "resume" in path or "简历" in path:
        return "resume"
    if "project" in path or "项目" in path:
        return "project"
    if "github" in path:
        return "github"
    if "skill" in path or "技能" in path:
        return "skill"
    if "intern" in path or "实习" in path:
        return "internship"
    if "cert" in path or "证书" in path or "奖" in path:
        return "certificate"
    if "upload" in path:
        return "upload"
    return "document"


@dataclass
class KnowledgeBaseIngestResult:
    source_name: str
    chunk_count: int
    saved_path: Path | None = None


class KnowledgeBaseService:
    """Manage local runtime uploads and persisted demo knowledge-base chunks.

    Uses BM25 keyword retrieval (with jieba) when available;
    falls back to MemoryVectorStore token matching otherwise.
    """

    def __init__(self, runtime_dir: str | Path = "runtime") -> None:
        self.runtime_dir = Path(runtime_dir)
        self.knowledge_base_dir = self.runtime_dir / "knowledge_base"
        self.upload_dir = self.runtime_dir / "uploads"
        self.chunk_file = self.knowledge_base_dir / "chunks.jsonl"
        self.repo_file = self.knowledge_base_dir / "chunks.repos.txt"
        self.chunker = TextChunker()
        self.file_loader = FileLoader()
        self._bm25: Any = None
        self._bm25_dirty: bool = True

    def ensure_dirs(self) -> None:
        self.knowledge_base_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def index_text(self, content: str, source_name: str = "upload") -> KnowledgeBaseIngestResult:
        """Chunk text, append chunks to the runtime JSONL index, and return count."""
        self.ensure_dirs()
        document = ProfileDocument(
            document_id=hashlib.sha256(source_name.encode("utf-8")).hexdigest()[:16],
            source_path=source_name,
            title=Path(source_name).name,
            content=content,
            item_type="profile",
        )
        chunks = self.chunker.chunk_document(document)
        self._append_chunks(chunks)
        return KnowledgeBaseIngestResult(source_name=source_name, chunk_count=len(chunks))

    def ingest_upload(self, filename: str, data: bytes) -> KnowledgeBaseIngestResult:
        """Persist an uploaded file under runtime/uploads and index its text."""
        self.ensure_dirs()
        safe_name = Path(filename).name
        saved_path = self.upload_dir / safe_name
        saved_path.write_bytes(data)

        document = self.file_loader.load(saved_path)
        result = self.index_text(document.content, source_name=safe_name)
        result.saved_path = saved_path
        return result

    def load_store(self) -> tuple[MemoryVectorStore, int]:
        """Load persisted chunks into an in-memory vector store (legacy)."""
        store = MemoryVectorStore()
        count = 0
        for chunk in self.iter_chunks():
            store.add_chunks([chunk])
            count += 1
        return store, count

    # -- BM25-enhanced search -------------------------------------------------

    def _ensure_bm25_index(self) -> None:
        """Build BM25 index from JSONL if dirty or not yet built."""
        if not self._bm25_dirty and self._bm25 is not None:
            return

        try:
            from career_agent.rag.retrievers.bm25_retriever import BM25Retriever
        except ImportError:
            self._bm25 = None
            self._bm25_dirty = False
            return

        retriever = BM25Retriever()
        chunks = list(self.iter_chunks())
        if chunks:
            retriever.add_chunks(chunks)
        self._bm25 = retriever
        self._bm25_dirty = False

    def search(self, query: str, top_k: int = 5) -> list[RetrievedEvidence]:
        """Keyword search with BM25 when available; falls back to MemoryVectorStore.

        The BM25 index is rebuilt lazily on first call after chunks change.
        """
        self._ensure_bm25_index()
        if self._bm25 is not None:
            results = self._bm25.search(query, top_k=top_k)
            if results:
                return results
        # Fallback to legacy MemoryVectorStore
        store, _ = self.load_store()
        return store.search(query=query, top_k=top_k)

    def list_sources(self) -> list[str]:
        sources = {
            chunk.source_path
            for chunk in self.iter_chunks()
            if chunk.source_path
        }
        return sorted(sources)

    def load_github_repos(self) -> list[str]:
        if not self.repo_file.is_file():
            return []
        return [line.strip() for line in self.repo_file.read_text(encoding="utf-8").splitlines() if line.strip()]

    def save_github_repos(self, repos: Iterable[str]) -> None:
        self.ensure_dirs()
        unique = sorted({repo.strip() for repo in repos if repo.strip()})
        self.repo_file.write_text("\n".join(unique), encoding="utf-8")

    def ingest_github_repo(self, repo_name: str) -> KnowledgeBaseIngestResult:
        """Fetch and index a public GitHub README for local demo use."""
        import urllib.request

        url = f"https://raw.githubusercontent.com/{repo_name}/main/README.md"
        request = urllib.request.Request(url, headers={"User-Agent": "smart-apply"})
        with urllib.request.urlopen(request, timeout=10) as response:
            content = response.read().decode("utf-8", errors="replace")

        result = self.index_text(content, f"github:{repo_name}")
        repos = self.load_github_repos()
        if repo_name not in repos:
            repos.append(repo_name)
            self.save_github_repos(repos)
        return result

    def ingest_github_user(self, username: str, limit: int = 100) -> int:
        """Fetch public repo metadata and README files, returning indexed repo count."""
        import urllib.request

        url = f"https://api.github.com/users/{username}/repos?per_page={limit}&sort=updated"
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "smart-apply",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            repos = json.loads(response.read().decode("utf-8"))

        indexed = 0
        known = self.load_github_repos()
        for repo in repos:
            if repo.get("fork"):
                continue
            full_name = repo["full_name"]
            content = (
                f"# {full_name}\n"
                f"{repo.get('description') or ''}\n"
                f"语言:{repo.get('language') or ''} Stars:{repo.get('stargazers_count', 0)}\n"
            )
            try:
                readme_url = f"https://raw.githubusercontent.com/{full_name}/main/README.md"
                readme_request = urllib.request.Request(readme_url, headers={"User-Agent": "smart-apply"})
                with urllib.request.urlopen(readme_request, timeout=8) as readme_response:
                    content += readme_response.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            self.index_text(content, f"github:{full_name}")
            if full_name not in known:
                known.append(full_name)
            indexed += 1

        self.save_github_repos(known)
        return indexed

    def iter_chunks(self) -> Iterable[DocumentChunk]:
        if not self.chunk_file.is_file():
            return
        with self.chunk_file.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    yield DocumentChunk(
                        chunk_id=data["chunk_id"],
                        document_id=data.get("document_id", ""),
                        content=data.get("content", ""),
                        source_path=data.get("source_path", ""),
                        chunk_index=data.get("chunk_index", 0),
                        metadata=data.get("metadata", {}),
                    )
                except Exception:
                    continue

    # -- read-only query helpers -----------------------------------------------

    def get_summary(self) -> dict:
        """Return a lightweight knowledge-base summary dict.

        Safe to call even when the KB is empty — all counts will be zero.
        """
        import os
        chunk_count = 0
        sources: set[str] = set()
        for chunk in self.iter_chunks():
            chunk_count += 1
            if chunk.source_path:
                sources.add(chunk.source_path)
        repos = self.load_github_repos()
        upload_count = sum(
            1 for _ in self.upload_dir.iterdir()
        ) if self.upload_dir.is_dir() else 0
        return {
            "chunk_count": chunk_count,
            "source_count": len(sources),
            "repo_count": len(repos),
            "upload_count": upload_count,
            "last_updated": (
                os.path.getmtime(str(self.chunk_file))
                if self.chunk_file.is_file()
                else None
            ),
        }

    def get_source_details(self) -> list[dict]:
        """Return a list of source descriptors for the KB overview.

        Each entry: source_name, source_type, chunk_count, path.
        """
        source_map: dict[str, dict] = {}
        for chunk in self.iter_chunks():
            key = chunk.source_path or chunk.document_id or "unknown"
            if key not in source_map:
                source_map[key] = {
                    "source_name": chunk.source_path or chunk.document_id,
                    "source_type": _guess_source_type(chunk.source_path, chunk.metadata),
                    "chunk_count": 0,
                    "path": chunk.source_path or "",
                }
            source_map[key]["chunk_count"] += 1
        # Add GitHub repos as sources
        for repo in self.load_github_repos():
            key = f"github:{repo}"
            if key not in source_map:
                source_map[key] = {
                    "source_name": repo,
                    "source_type": "github",
                    "chunk_count": 0,
                    "path": f"https://github.com/{repo}",
                }
        return sorted(source_map.values(), key=lambda s: s["chunk_count"], reverse=True)

    def get_profile_text(self) -> str:
        """Return concatenated text of all chunks — used for profile summary.

        Truncated to a reasonable length to avoid overwhelming the LLM context.
        """
        parts: list[str] = []
        total = 0
        max_chars = 8000
        for chunk in self.iter_chunks():
            snippet = chunk.content[:600]
            parts.append(f"[{chunk.source_path}] {snippet}")
            total += len(snippet)
            if total > max_chars:
                break
        return "\n\n".join(parts) if parts else ""

    # -- internal --------------------------------------------------------------

    def _append_chunks(self, chunks: list[DocumentChunk]) -> None:
        self._bm25_dirty = True  # mark for rebuild
        with self.chunk_file.open("a", encoding="utf-8") as handle:
            for chunk in chunks:
                handle.write(json.dumps({
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "content": chunk.content,
                    "source_path": chunk.source_path,
                    "chunk_index": chunk.chunk_index,
                    "metadata": chunk.metadata,
                }, ensure_ascii=False) + "\n")
