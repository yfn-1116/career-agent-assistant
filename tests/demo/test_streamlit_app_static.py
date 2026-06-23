"""Static checks for demo/streamlit/*.py — no streamlit import required."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
APP_PATH = REPO_ROOT / "demo" / "streamlit" / "app.py"
UI_PATH = REPO_ROOT / "demo" / "streamlit" / "ui_components.py"
STYLES_PATH = REPO_ROOT / "demo" / "streamlit" / "styles.py"

_ALL_DEMO_FILES = [APP_PATH, UI_PATH, STYLES_PATH]


def _read_app() -> str:
    return APP_PATH.read_text(encoding="utf-8")


def _read_ui() -> str:
    return UI_PATH.read_text(encoding="utf-8")


def _read_styles() -> str:
    return STYLES_PATH.read_text(encoding="utf-8")


def _read_all_demo() -> str:
    return "\n".join(f.read_text(encoding="utf-8") for f in _ALL_DEMO_FILES if f.is_file())


# ---------------------------------------------------------------------------
# File existence
# ---------------------------------------------------------------------------


class TestAppExists:
    def test_app_file_exists(self):
        assert APP_PATH.is_file()

    def test_ui_components_file_exists(self):
        assert UI_PATH.is_file()

    def test_styles_file_exists(self):
        assert STYLES_PATH.is_file()


# ---------------------------------------------------------------------------
# Service imports
# ---------------------------------------------------------------------------


class TestAppUsesAgentRunService:
    def test_imports_agent_run_service(self):
        text = _read_app()
        assert "AgentRunService" in text or "agent_run" in text

    def test_uses_runtime_services(self):
        text = _read_app()
        assert "KnowledgeBaseService" in text
        assert "ApplicationService" in text

    def test_does_not_directly_import_rag_for_workflow(self):
        """Main workflow must go through AgentRunService, not direct RAG/Agent calls."""
        text = _read_app()
        assert "JobMatchWorkflow" not in text

    def test_app_imports_ui_modules(self):
        """app.py must import from styles and ui_components."""
        text = _read_app()
        assert "from styles import" in text or "from demo.streamlit.styles import" in text
        assert "from ui_components import" in text or "from demo.streamlit.ui_components import" in text


# ---------------------------------------------------------------------------
# Required content
# ---------------------------------------------------------------------------


class TestAppContainsRequiredContent:
    def test_contains_title(self):
        """Page title is now 'Internship Copilot'."""
        combined = _read_all_demo()
        assert "Internship Copilot" in combined

    def test_contains_input_area(self):
        text = _read_all_demo()
        assert "chat_input" in text or "Ask Agent" in text or "ask about" in text.lower()

    def test_contains_expandable_details(self):
        """Expanders live in ui_components.py after refactor."""
        text = _read_all_demo()
        assert "expander" in text


# ---------------------------------------------------------------------------
# UI module structure
# ---------------------------------------------------------------------------


class TestUIModulesDontImportCore:
    """ui_components.py and styles.py must not import or redefine core logic."""

    def test_ui_components_no_core_redefines(self):
        text = _read_ui()
        for agent in [
            "class RAGPipeline",
            "class JDParserAgent",
            "class MatchAnalysisAgent",
            "class BuildAgent",
        ]:
            assert agent not in text

    def test_ui_components_has_render_functions(self):
        text = _read_ui()
        required = [
            "def render_empty_state",
            "def render_chat_messages",
            "def render_evidence_gate",
            "def render_application_records",
            "def render_sidebar_pipeline",
            "def render_sidebar_demo_controls",
            "def render_sidebar_kb_stats",
            "def render_sidebar_logo",
            "def render_sidebar_nav_section",
            "def load_sample_jd_text",
        ]
        for fn in required:
            assert fn in text, f"Missing function: {fn}"


class TestStyles:
    def test_inject_custom_css_exists(self):
        text = _read_styles()
        assert "def inject_custom_css" in text

    def test_styles_uses_unsafe_allow_html(self):
        text = _read_styles()
        assert "unsafe_allow_html=True" in text


# ---------------------------------------------------------------------------
# Forbidden imports & patterns (all demo files)
# ---------------------------------------------------------------------------


class TestAppDoesNotImportForbiddenModules:
    def test_no_fastapi_import(self):
        """Demo files must not import FastAPI — it's a backend framework."""
        forbidden = ["import fastapi", "from fastapi"]
        for f in _ALL_DEMO_FILES:
            if f.is_file():
                text = f.read_text(encoding="utf-8").lower()
                for token in forbidden:
                    assert token not in text, f"{f.name} contains '{token}'"

    def test_no_network_access(self):
        forbidden = ["urllib", "requests.get", "requests.post"]
        for f in _ALL_DEMO_FILES:
            if f.is_file():
                text = f.read_text(encoding="utf-8").lower()
                for token in forbidden:
                    assert token not in text, f"{f.name} contains {token}"

    def test_no_direct_runtime_data_paths(self):
        forbidden = [
            "data/uploads",
            "data/applications",
            "data/knowledge_base",
        ]
        for f in _ALL_DEMO_FILES:
            if f.is_file():
                text = f.read_text(encoding="utf-8")
                for token in forbidden:
                    assert token not in text, f"{f.name} contains {token}"


class TestAppDoesNotRewriteCoreLogic:
    def test_does_not_redefine_rag_pipeline(self):
        for f in _ALL_DEMO_FILES:
            if f.is_file():
                assert "class RAGPipeline" not in f.read_text(encoding="utf-8"), (
                    f"{f.name} redefines RAGPipeline"
                )

    def test_does_not_redefine_agents(self):
        agents = ["class JDParserAgent", "class MatchAnalysisAgent", "class BuildAgent"]
        for f in _ALL_DEMO_FILES:
            if f.is_file():
                text = f.read_text(encoding="utf-8")
                for agent in agents:
                    assert agent not in text, f"{f.name} redefines {agent}"
