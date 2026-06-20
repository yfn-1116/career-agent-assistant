"""Tests for LocalGitHubRepoReader."""

import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from career_agent.github.local_repo_reader import LocalGitHubRepoReader
from career_agent.rag.schemas import ProfileDocument


@pytest.fixture
def reader():
    return LocalGitHubRepoReader()


@pytest.fixture
def sample_repo():
    """Create a temp repo with README.md + docs/*.md + non-md file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir) / "my-repo"
        base.mkdir()
        (base / "README.md").write_text("# 项目名称\n\n项目描述。", encoding="utf-8")
        docs = base / "docs"
        docs.mkdir()
        (docs / "design.md").write_text("# 设计文档\n\n设计内容。", encoding="utf-8")
        (docs / "notes.md").write_text("# 笔记\n\n开发笔记。", encoding="utf-8")
        (base / "src").mkdir()
        (base / "src" / "main.py").write_text("print('hello')", encoding="utf-8")
        yield base


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestReadSingleRepo:
    def test_reads_readme(self, reader, sample_repo):
        docs = reader.read_repo(sample_repo)
        assert any("README.md" in d.source_path for d in docs)

    def test_reads_docs_markdown(self, reader, sample_repo):
        docs = reader.read_repo(sample_repo)
        assert len(docs) == 3  # README + 2 docs

    def test_ignores_non_md_files(self, reader, sample_repo):
        docs = reader.read_repo(sample_repo)
        sources = [d.source_path for d in docs]
        assert not any("main.py" in s for s in sources)

    def test_returns_profile_documents(self, reader, sample_repo):
        docs = reader.read_repo(sample_repo)
        assert all(isinstance(d, ProfileDocument) for d in docs)

    def test_item_type_is_github_repo(self, reader, sample_repo):
        docs = reader.read_repo(sample_repo)
        assert all(d.item_type == "github_repo" for d in docs)

    def test_metadata_contains_required_keys(self, reader, sample_repo):
        docs = reader.read_repo(sample_repo)
        for d in docs:
            assert d.metadata["repo_name"] == "my-repo"
            assert "relative_path" in d.metadata
            assert d.metadata["reader"] == "local_github_repo_reader"
            assert d.metadata["document_role"] in ("readme", "docs")

    def test_title_from_h1(self, reader, sample_repo):
        docs = reader.read_repo(sample_repo)
        readme = [d for d in docs if d.metadata["document_role"] == "readme"][0]
        assert readme.title == "项目名称"

    def test_document_id_stable(self, reader, sample_repo):
        docs1 = reader.read_repo(sample_repo)
        docs2 = reader.read_repo(sample_repo)
        assert [d.document_id for d in docs1] == [d.document_id for d in docs2]

    def test_empty_dir_returns_empty(self, reader):
        with tempfile.TemporaryDirectory() as tmpdir:
            empty = Path(tmpdir) / "empty-repo"
            empty.mkdir()
            assert reader.read_repo(empty) == []

    def test_nonexistent_dir_returns_empty(self, reader):
        assert reader.read_repo("/nonexistent/path") == []

    def test_no_network_access(self, reader, sample_repo):
        docs = reader.read_repo(sample_repo)
        assert len(docs) > 0


class TestReadRepos:
    def test_reads_multiple_repos(self, reader):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            for name in ["repo-a", "repo-b"]:
                r = base / name
                r.mkdir()
                (r / "README.md").write_text(f"# {name}\ncontent", encoding="utf-8")

            docs = reader.read_repos(base)
            assert len(docs) == 2
            names = {d.metadata["repo_name"] for d in docs}
            assert names == {"repo-a", "repo-b"}

    def test_empty_root_returns_empty(self, reader):
        with tempfile.TemporaryDirectory() as tmpdir:
            assert reader.read_repos(tmpdir) == []
