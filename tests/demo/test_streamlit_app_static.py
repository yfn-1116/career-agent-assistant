"""Static checks for demo/streamlit/app.py — no streamlit import required."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
APP_PATH = REPO_ROOT / "demo" / "streamlit" / "app.py"


def _read_app() -> str:
    return APP_PATH.read_text(encoding="utf-8")


class TestAppExists:
    def test_app_file_exists(self):
        assert APP_PATH.is_file()


class TestAppUsesAgentRunService:
    def test_imports_agent_run_service(self):
        text = _read_app()
        assert "AgentRunService" in text or "agent_run" in text

    def test_does_not_directly_import_rag(self):
        """UI should call AgentRunService, not RAG internals."""
        text = _read_app()
        assert "RAGPipeline" not in text
        assert "JobMatchWorkflow" not in text


class TestAppContainsRequiredContent:
    def test_contains_title(self):
        text = _read_app()
        assert "Smart Apply Agent" in text

    def test_contains_input_area(self):
        text = _read_app()
        assert "text_area" in text or "Ask Agent" in text

    def test_contains_expandable_details(self):
        text = _read_app()
        assert "expander" in text


class TestAppDoesNotImportForbiddenModules:
    def test_no_fastapi(self):
        assert "fastapi" not in _read_app().lower()

    def test_no_network_access(self):
        text = _read_app()
        forbidden = ["urllib", "requests.get", "requests.post"]
        for token in forbidden:
            assert token not in text.lower()


class TestAppDoesNotRewriteCoreLogic:
    def test_does_not_redefine_rag_pipeline(self):
        assert "class RAGPipeline" not in _read_app()

    def test_does_not_redefine_agents(self):
        text = _read_app()
        for agent in ["class JDParserAgent", "class MatchAnalysisAgent", "class BuildAgent"]:
            assert agent not in text
