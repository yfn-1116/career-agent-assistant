"""First-phase RAG pipeline composition."""

from pathlib import Path

from career_agent.rag.chunking.text_chunker import TextChunker
from career_agent.rag.loaders.markdown_loader import MarkdownProfileLoader
from career_agent.rag.retrievers.simple_retriever import SimpleRetriever
from career_agent.rag.schemas import RetrievedEvidence
from career_agent.rag.vectorstores.base import VectorStore
from career_agent.rag.vectorstores.memory_store import MemoryVectorStore


class RAGPipeline:
    """Build a local Markdown index and retrieve evidence from it."""

    def __init__(
        self,
        loader: MarkdownProfileLoader | None = None,
        chunker: TextChunker | None = None,
        vectorstore: VectorStore | None = None,
    ) -> None:
        self.loader = loader or MarkdownProfileLoader()
        self.chunker = chunker or TextChunker()
        self.vectorstore = vectorstore or MemoryVectorStore()
        self.retriever = SimpleRetriever(self.vectorstore)

    def build_index(self, source_path: str | Path) -> None:
        path = Path(source_path)
        documents = (
            [self.loader.load_file(path)]
            if path.is_file()
            else self.loader.load_directory(path)
        )
        chunks = self.chunker.chunk_documents(documents)
        self.vectorstore.add_chunks(chunks)

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedEvidence]:
        return self.retriever.retrieve(query=query, top_k=top_k)

    def clear(self) -> None:
        self.vectorstore.clear()

    def count(self) -> int:
        return self.vectorstore.count()
