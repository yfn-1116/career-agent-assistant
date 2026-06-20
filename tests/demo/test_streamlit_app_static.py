"""Static checks for demo/streamlit/app.py — no streamlit import required."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_PATH = REPO_ROOT / "demo" / "streamlit" / "app.py"


def _read_app() -> str:
    return APP_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAppExists:
    def test_app_file_exists(self):
        assert APP_PATH.is_file(), f"Missing {APP_PATH}"


class TestAppImportsWorkflow:
    def test_contains_job_match_workflow(self):
        text = _read_app()
        assert "JobMatchWorkflow" in text

    def test_contains_streamlit_import(self):
        text = _read_app()
        assert "streamlit" in text


class TestAppContainsRequiredContent:
    def test_contains_jd_filenames(self):
        text = _read_app()
        assert "agent_intern_jd.md" in text
        assert "rag_engineer_intern_jd.md" in text

    def test_contains_top_k(self):
        text = _read_app()
        assert "top_k" in text

    def test_contains_profile_dir(self):
        text = _read_app()
        assert "profile" in text or "PROFILE" in text

    def test_contains_running_instructions(self):
        text = _read_app()
        assert "streamlit run" in text or "运行" in text or "pip install" in text


class TestAppDoesNotImportForbiddenModules:
    def test_no_fastapi(self):
        text = _read_app()
        assert "fastapi" not in text.lower()

    def test_no_langchain(self):
        text = _read_app()
        assert "langchain" not in text.lower()

    def test_no_langgraph(self):
        text = _read_app()
        assert "langgraph" not in text.lower()

    def test_no_network_access(self):
        """app.py should not contain urllib, requests, or socket calls."""
        text = _read_app()
        forbidden = ["urllib", "requests.get", "requests.post", "socket."]
        for token in forbidden:
            assert token not in text.lower(), f"Contains forbidden token: {token}"


class TestAppDoesNotRewriteCoreLogic:
    def test_does_not_redefine_rag_pipeline(self):
        text = _read_app()
        assert "class RAGPipeline" not in text

    def test_does_not_redefine_agents(self):
        text = _read_app()
        for agent in [
            "class JDParserAgent",
            "class RAGRetrieveAgent",
            "class MatchAnalysisAgent",
            "class BuildAgent",
        ]:
            assert agent not in text, f"Should not redefine {agent}"

    def test_does_not_write_to_src(self):
        text = _read_app()
        # Should not contain any file writes to src/
        assert 'src/' not in text or 'sys.path' in text  # Only for path setup


class TestNoExternalModelCalls:
    def test_no_openai_or_deepseek_imports(self):
        """说明文字中可以提及 OpenAI/DeepSeek，但不能实际 import 或调用 API。"""
        text = _read_app()
        assert "import openai" not in text.lower()
        assert "from openai" not in text.lower()
        assert 'openai.' not in text.lower()
        assert 'deepseek.' not in text.lower()
        assert 'api.openai.com' not in text.lower()
        assert 'api.deepseek.com' not in text.lower()
