"""Tests for JDParserAgent."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from career_agent.agents.jd_parser import JDParserAgent
from career_agent.agents.state import ParsedJD


def _read_sample(name: str) -> str:
    path = Path("data/samples/jobs") / name
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestParseRealJDs:
    """Parse the four sample JD files."""

    def test_parse_agent_intern_jd(self):
        text = _read_sample("agent_intern_jd.md")
        agent = JDParserAgent()
        result = agent.parse(text)
        assert isinstance(result, ParsedJD)
        assert "Agent" in result.job_title or result.job_title != ""

    def test_parse_rag_engineer_jd(self):
        text = _read_sample("rag_engineer_intern_jd.md")
        agent = JDParserAgent()
        result = agent.parse(text)
        assert result.raw_text == text

    def test_parse_ai_application_jd(self):
        text = _read_sample("ai_application_intern_jd.md")
        agent = JDParserAgent()
        result = agent.parse(text)
        assert isinstance(result, ParsedJD)

    def test_parse_backend_ai_jd(self):
        text = _read_sample("backend_ai_intern_jd.md")
        agent = JDParserAgent()
        result = agent.parse(text)
        assert isinstance(result, ParsedJD)


class TestEmptyInput:
    def test_empty_string_returns_default(self):
        agent = JDParserAgent()
        result = agent.parse("")
        assert result.job_title == ""
        assert result.hard_skills == []
        assert result.keywords == []

    def test_whitespace_only_returns_default(self):
        agent = JDParserAgent()
        result = agent.parse("   \n  \n  ")
        assert result.job_title == ""
        assert result.metadata["parser"] == "jd_parser_agent"


class TestMetadata:
    def test_metadata_contains_parser(self):
        agent = JDParserAgent()
        result = agent.parse("Python RAG 岗位")
        assert result.metadata["parser"] == "jd_parser_agent"

    def test_raw_text_preserved(self):
        text = "# Test JD\n\n需要 Python 和 RAG"
        agent = JDParserAgent()
        result = agent.parse(text)
        assert result.raw_text == text


class TestSkillDetection:
    def test_detects_python(self):
        agent = JDParserAgent()
        result = agent.parse("要求熟练掌握 Python")
        assert "Python" in result.hard_skills

    def test_detects_rag(self):
        agent = JDParserAgent()
        result = agent.parse("了解 RAG 和向量数据库")
        assert "RAG" in result.hard_skills
        assert "向量数据库" in result.hard_skills

    def test_detects_agent(self):
        agent = JDParserAgent()
        result = agent.parse("有 Agent 和 LangGraph 经验")
        assert "Agent" in result.hard_skills
        assert "LangGraph" in result.hard_skills

    def test_detects_langchain(self):
        agent = JDParserAgent()
        result = agent.parse("使用过 LangChain 框架")
        assert "LangChain" in result.hard_skills

    def test_keywords_not_empty_for_rich_jd(self):
        text = _read_sample("agent_intern_jd.md")
        agent = JDParserAgent()
        result = agent.parse(text)
        assert len(result.keywords) > 0

    def test_soft_skills_detected(self):
        agent = JDParserAgent()
        result = agent.parse("需要良好的沟通能力和团队协作")
        assert "沟通" in result.soft_skills
        assert "团队协作" in result.soft_skills


class TestDirectionInference:
    def test_agent_direction(self):
        agent = JDParserAgent()
        result = agent.parse("Agent 开发，LangGraph，多 Agent 协作")
        assert result.job_direction == "agent"

    def test_rag_direction(self):
        agent = JDParserAgent()
        result = agent.parse("RAG 检索增强生成，向量数据库，embedding")
        assert result.job_direction == "rag"

    def test_backend_direction(self):
        agent = JDParserAgent()
        result = agent.parse("后端开发，FastAPI，PostgreSQL，API 设计")
        assert result.job_direction == "backend"

    def test_general_when_no_match(self):
        agent = JDParserAgent()
        result = agent.parse("这是一个普通岗位描述")
        assert result.job_direction == "general"
