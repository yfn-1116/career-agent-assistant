"""Tests for MarkdownProfileLoader."""

import tempfile
from pathlib import Path

import pytest

from career_agent.rag.loaders.markdown_loader import MarkdownProfileLoader
from career_agent.rag.schemas import ProfileDocument


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def loader():
    return MarkdownProfileLoader()


@pytest.fixture
def single_md_file():
    """Create a single .md file with a top-level heading."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write("# 个人简历\n\n这是正文内容。\n")
        f.flush()
        yield Path(f.name)
    # cleanup
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def md_without_heading():
    """Create a .md file without any # heading."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write("没有一级标题的内容。\n\n只有纯文本。\n")
        f.flush()
        yield Path(f.name)
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def md_dir():
    """Create a temporary directory with several .md files and one non-.md file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        (base / "resume.md").write_text("# 个人简历\n\n张三的简历内容。\n", encoding="utf-8")
        (base / "projects.md").write_text("# 项目经历\n\n四个项目详情。\n", encoding="utf-8")
        (base / "skills.md").write_text("# 技能详情\n\nPython, FastAPI, LangChain。\n", encoding="utf-8")
        (base / "notes.txt").write_text("这不是 Markdown 文件。\n", encoding="utf-8")

        yield base


@pytest.fixture
def empty_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestLoadSingleFile:
    """Tests for load_file()."""

    def test_load_single_file(self, loader, single_md_file):
        doc = loader.load_file(single_md_file)

        assert isinstance(doc, ProfileDocument)
        assert doc.content == "# 个人简历\n\n这是正文内容。\n"
        assert doc.source_path == str(single_md_file.resolve())

    def test_extracts_title_from_h1(self, loader, single_md_file):
        doc = loader.load_file(single_md_file)

        assert doc.title == "个人简历"

    def test_falls_back_to_filename_when_no_h1(self, loader, md_without_heading):
        doc = loader.load_file(md_without_heading)

        # title falls back to file stem
        assert doc.title == md_without_heading.stem
        assert "没有一级标题" in doc.content

    def test_document_id_is_stable(self, loader, single_md_file):
        doc1 = loader.load_file(single_md_file)
        doc2 = loader.load_file(single_md_file)

        assert doc1.document_id == doc2.document_id
        assert len(doc1.document_id) == 16  # sha256 hex truncated

    def test_metadata_contains_required_keys(self, loader, single_md_file):
        doc = loader.load_file(single_md_file)

        assert doc.metadata["filename"] == single_md_file.name
        assert doc.metadata["file_stem"] == single_md_file.stem
        assert doc.metadata["source_path"] == str(single_md_file.resolve())
        assert doc.metadata["loader"] == "markdown_profile_loader"

    def test_item_type_resume(self, loader):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write("# Test\ncontent\n")
            f.flush()
            path = Path(f.name)
        try:
            # Use a path whose stem is "resume"
            import shutil
            target = path.parent / "resume.md"
            shutil.move(str(path), str(target))
            doc = loader.load_file(target)
            assert doc.item_type == "resume"
        finally:
            target.unlink(missing_ok=True)
            path.unlink(missing_ok=True)


class TestItemTypeInference:
    """Tests for item_type inference rules."""

    _CASES = [
        ("resume.md", "resume"),
        ("projects.md", "project"),
        ("github_repos.md", "github_repo"),
        ("skills.md", "skill"),
        ("internship.md", "internship"),
        ("unknown.md", "document"),
        ("notes.md", "document"),
    ]

    @pytest.mark.parametrize("filename,expected", _CASES)
    def test_infer_item_type(self, loader, filename, expected):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / filename
            path.write_text("# Test\ncontent\n", encoding="utf-8")
            doc = loader.load_file(path)
            assert doc.item_type == expected, f"{filename} → {expected}"


class TestLoadDirectory:
    """Tests for load_directory()."""

    def test_loads_all_md_files(self, loader, md_dir):
        docs = loader.load_directory(md_dir)

        assert len(docs) == 3  # resume, projects, skills (notes.txt skipped)

    def test_ignores_non_md_files(self, loader, md_dir):
        docs = loader.load_directory(md_dir)

        filenames = {Path(d.source_path).name for d in docs}
        assert "notes.txt" not in filenames

    def test_returns_profile_documents(self, loader, md_dir):
        docs = loader.load_directory(md_dir)

        assert all(isinstance(d, ProfileDocument) for d in docs)

    def test_empty_dir_returns_empty_list(self, loader, empty_dir):
        docs = loader.load_directory(empty_dir)

        assert docs == []

    def test_items_have_correct_types(self, loader, md_dir):
        docs = loader.load_directory(md_dir)

        types = {Path(d.source_path).stem: d.item_type for d in docs}
        assert types["resume"] == "resume"
        assert types["projects"] == "project"
        assert types["skills"] == "skill"


class TestDoesNotModifySampleFiles:
    """Verify the loader only reads — never writes — sample files."""

    def test_sample_files_unchanged(self, loader):
        """Load sample files and confirm they still exist with original content."""
        import os

        samples_dir = Path("data/samples/profile")
        if not samples_dir.is_dir():
            pytest.skip("Sample directory not found")

        # Record original content before loading
        original: dict[str, str] = {}
        for md in sorted(samples_dir.glob("*.md")):
            original[md.name] = md.read_text(encoding="utf-8")

        # Load them
        docs = loader.load_directory(samples_dir)
        assert len(docs) > 0, "Expected at least one sample document"

        # Verify content unchanged
        for md in sorted(samples_dir.glob("*.md")):
            current = md.read_text(encoding="utf-8")
            assert current == original[md.name], f"{md.name} was modified by loader"

    def test_sample_files_exist(self):
        """Sanity check: sample directories exist for CI / dev environments."""
        profile_dir = Path("data/samples/profile")
        jobs_dir = Path("data/samples/jobs")

        assert profile_dir.is_dir(), f"Missing {profile_dir}"
        assert jobs_dir.is_dir(), f"Missing {jobs_dir}"

        profile_md = list(profile_dir.glob("*.md"))
        assert len(profile_md) >= 5, f"Expected 5 profile files, got {len(profile_md)}"

        jobs_md = list(jobs_dir.glob("*.md"))
        assert len(jobs_md) == 4, f"Expected 4 job files, got {len(jobs_md)}"
