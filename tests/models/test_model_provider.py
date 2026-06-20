"""Tests for the ModelProvider interface."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from career_agent.models.provider import ModelProvider


class _Concrete(ModelProvider):
    def generate(self, prompt, *, system_prompt=None, metadata=None):
        return prompt


class TestModelProviderInterface:
    def test_interface_exists(self):
        assert ModelProvider is not None

    def test_generate_signature(self):
        p = _Concrete()
        result = p.generate("hello", system_prompt="sys", metadata={"a": 1})
        assert result == "hello"

    def test_subclass_enforced(self):
        """Instantiating the ABC directly should fail."""
        import pytest
        with pytest.raises(TypeError):
            ModelProvider()  # type: ignore[abstract]
