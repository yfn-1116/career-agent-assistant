"""Runtime knowledge-base service for demos and local UI state."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from career_agent.rag.chunking.text_chunker import TextChunker
from career_agent.rag.loaders.file_loader import FileLoader
from career_agent.rag.schemas import DocumentChunk, ProfileDocument, RetrievedEvidence
from career_agent.rag.vectorstores.memory_store import MemoryVectorStore


@dataclass
class KnowledgeBaseIngestResult:
    source_name: str
    chunk_count: int
    saved_path: Path | None = None


class KnowledgeBaseService:
    """Manage local runtime uploads and persisted demo knowledge-base chunks."""

    def __init__(self, runtime_dir: str | Path = "runtime") -> None:
        self.runtime_dir = Path(runtime_dir)
        self.knowledge_base_dir = self.runtime_dir / "knowledge_base"
        self.upload_dir = self.runtime_dir / "uploads"
        self.chunk_file = self.knowledge_base_dir / "chunks.jsonl"
        self.repo_file = self.knowledge_base_dir / "chunks.repos.txt"
        self.chunker = TextChunker()
        self.file_loader = FileLoader()

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
        """Load persisted chunks into an in-memory vector store."""
        store = MemoryVectorStore()
        count = 0
        for chunk in self.iter_chunks():
            store.add_chunks([chunk])
            count += 1
        return store, count

    def search(self, query: str, top_k: int = 5) -> list[RetrievedEvidence]:
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

    def _append_chunks(self, chunks: list[DocumentChunk]) -> None:
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
