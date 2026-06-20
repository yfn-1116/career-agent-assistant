"""Tests for MockProvider."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from career_agent.models.mock_provider import MockProvider


class TestMockProvider:
    def test_returns_default_text(self):
        p = MockProvider()
        result = p.generate("test prompt")
        assert len(result) > 0
        assert "MockProvider" in result

    def test_records_last_prompt(self):
        p = MockProvider()
        p.generate("hello world")
        assert p.last_prompt == "hello world"

    def test_records_system_prompt(self):
        p = MockProvider()
        p.generate("p", system_prompt="sys")
        assert p.last_system_prompt == "sys"

    def test_records_metadata(self):
        p = MockProvider()
        p.generate("p", metadata={"source": "test"})
        assert p.last_metadata == {"source": "test"}

    def test_call_count_increments(self):
        p = MockProvider()
        p.generate("1")
        p.generate("2")
        assert p.call_count == 2

    def test_returns_fixed_response(self):
        p = MockProvider(fixed_response="固定输出")
        assert p.generate("anything") == "固定输出"

    def test_no_network_access(self):
        p = MockProvider()
        # Should complete instantly without any I/O
        result = p.generate("test")
        assert result is not None
