"""Tests for TextChunker."""

import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from career_agent.rag.chunking.text_chunker import TextChunker
from career_agent.rag.schemas import DocumentChunk, ProfileDocument


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_doc(
    document_id: str = "doc-1",
    content: str = "",
    source_path: str = "/tmp/test.md",
    title: str = "测试",
    item_type: str = "document",
    metadata: dict | None = None,
) -> ProfileDocument:
    return ProfileDocument(
        document_id=document_id,
        source_path=source_path,
        title=title,
        content=content,
        item_type=item_type,
        metadata=metadata or {"filename": "test.md", "loader": "test"},
    )


# ---------------------------------------------------------------------------
# clean_text
# ---------------------------------------------------------------------------

class TestCleanText:
    def test_strips_leading_trailing_whitespace(self):
        chunker = TextChunker()
        raw = "  \n\n  内容  \n  "
        assert chunker.clean_text(raw) == "内容"

    def test_collapses_excess_blank_lines(self):
        chunker = TextChunker()
        raw = "段落1\n\n\n\n\n段落2"
        result = chunker.clean_text(raw)
        # 3+ blanks → 2 (one empty line between paragraphs)
        assert result == "段落1\n\n段落2"

    def test_normalizes_carriage_return(self):
        chunker = TextChunker()
        raw = "行1\r\n行2\r行3"
        result = chunker.clean_text(raw)
        assert "\r" not in result
        assert result == "行1\n行2\n行3"

    def test_preserves_markdown_headings(self):
        chunker = TextChunker()
        raw = "# 标题\n\n## 二级标题\n\n内容"
        assert "# 标题" in chunker.clean_text(raw)
        assert "## 二级标题" in chunker.clean_text(raw)

    def test_preserves_list_markers(self):
        chunker = TextChunker()
        raw = "- 项目1\n- 项目2\n- 项目3"
        result = chunker.clean_text(raw)
        assert result.count("- 项目") == 3

    def test_empty_string_returns_empty(self):
        chunker = TextChunker()
        assert chunker.clean_text("") == ""

    def test_whitespace_only_returns_empty(self):
        chunker = TextChunker()
        assert chunker.clean_text("   \n \n  ") == ""


# ---------------------------------------------------------------------------
# chunk_document — single document
# ---------------------------------------------------------------------------

class TestChunkSingleDocument:
    def test_short_document_produces_one_chunk(self):
        chunker = TextChunker(chunk_size=800, overlap=100)
        doc = _make_doc(content="短文档内容。")

        chunks = chunker.chunk_document(doc)
        assert len(chunks) == 1
        assert chunks[0].content == "短文档内容。"

    def test_long_document_produces_multiple_chunks(self):
        chunker = TextChunker(chunk_size=100, overlap=10)
        # ~350 chars → should produce ~4 chunks
        content = "长文档内容。" * 50
        doc = _make_doc(content=content)

        chunks = chunker.chunk_document(doc)
        assert len(chunks) >= 3

    def test_empty_content_returns_empty_list(self):
        chunker = TextChunker()
        doc = _make_doc(content="   \n  ")  # clean → ""
        assert chunker.chunk_document(doc) == []

        doc2 = _make_doc(content="")
        assert chunker.chunk_document(doc2) == []

    def test_chunks_have_overlap(self):
        """Verify that adjacent chunks share overlapping content."""
        chunker = TextChunker(chunk_size=100, overlap=20)
        # Create predictable text so we can check overlap precisely
        content = "0123456789" * 30  # 300 chars
        doc = _make_doc(content=content)

        chunks = chunker.chunk_document(doc)
        assert len(chunks) >= 3

        # The last chars of chunk[0] should match the first chars of chunk[1]
        end_of_first = chunks[0].content[-20:]
        start_of_second = chunks[1].content[:20]
        assert end_of_first == start_of_second

    def test_chunk_id_stable(self):
        chunker = TextChunker(chunk_size=100, overlap=10)
        doc = _make_doc(document_id="doc-1", content="内容" * 50)

        c1 = chunker.chunk_document(doc)
        c2 = chunker.chunk_document(doc)
        assert [c.chunk_id for c in c1] == [c.chunk_id for c in c2]

    def test_chunk_index_increments(self):
        chunker = TextChunker(chunk_size=80, overlap=10)
        doc = _make_doc(content="数据" * 60)

        chunks = chunker.chunk_document(doc)
        for i, c in enumerate(chunks):
            assert c.chunk_index == i

    def test_returns_document_chunk_objects(self):
        chunker = TextChunker()
        doc = _make_doc(content="测试")

        chunks = chunker.chunk_document(doc)
        assert isinstance(chunks[0], DocumentChunk)

    def test_metadata_inherits_and_appends(self):
        chunker = TextChunker(chunk_size=200, overlap=20)
        doc = _make_doc(
            document_id="doc-1",
            content="内容" * 80,
            metadata={"filename": "resume.md", "loader": "markdown_profile_loader"},
        )

        chunks = chunker.chunk_document(doc)
        for c in chunks:
            assert c.metadata["filename"] == "resume.md"
            assert c.metadata["loader"] == "markdown_profile_loader"
            assert c.metadata["chunk_size"] == 200
            assert c.metadata["overlap"] == 20
            assert c.metadata["chunker"] == "text_chunker"
            assert "chunk_index" in c.metadata

    def test_inherits_document_id_and_source_path(self):
        chunker = TextChunker(chunk_size=500)
        doc = _make_doc(
            document_id="abc123", source_path="/data/resume.md", content="内容" * 200
        )

        chunks = chunker.chunk_document(doc)
        for c in chunks:
            assert c.document_id == "abc123"
            assert c.source_path == "/data/resume.md"


# ---------------------------------------------------------------------------
# chunk_documents — list
# ---------------------------------------------------------------------------

class TestChunkMultipleDocuments:
    def test_chunks_multiple_documents(self):
        chunker = TextChunker(chunk_size=500, overlap=50)
        docs = [
            _make_doc(document_id="d1", content="文档1内容。" * 100),
            _make_doc(document_id="d2", content="文档2内容。" * 100),
        ]

        chunks = chunker.chunk_documents(docs)
        assert len(chunks) >= 2
        assert any(c.document_id == "d1" for c in chunks)
        assert any(c.document_id == "d2" for c in chunks)

    def test_empty_list_returns_empty(self):
        chunker = TextChunker()
        assert chunker.chunk_documents([]) == []

    def test_chunk_ids_unique_across_documents(self):
        chunker = TextChunker(chunk_size=100, overlap=10)
        docs = [
            _make_doc(document_id="d1", content="A" * 300),
            _make_doc(document_id="d2", content="B" * 300),
        ]
        chunks = chunker.chunk_documents(docs)
        ids = [c.chunk_id for c in chunks]
        assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# parameter validation
# ---------------------------------------------------------------------------

class TestParameterValidation:
    def test_overlap_gte_chunk_size_raises(self):
        with pytest.raises(ValueError):
            TextChunker(chunk_size=100, overlap=100)

        with pytest.raises(ValueError):
            TextChunker(chunk_size=100, overlap=150)

    def test_negative_chunk_size_raises(self):
        with pytest.raises(ValueError):
            TextChunker(chunk_size=-1)

    def test_negative_overlap_raises(self):
        with pytest.raises(ValueError):
            TextChunker(chunk_size=100, overlap=-1)

    def test_default_parameters_valid(self):
        chunker = TextChunker()
        assert chunker.chunk_size == 800
        assert chunker.overlap == 100
        assert chunker.overlap < chunker.chunk_size
