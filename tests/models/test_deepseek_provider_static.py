"""Static tests for DeepSeekProvider — no real API calls."""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from career_agent.models.deepseek_provider import DeepSeekProvider


class TestDeepSeekProviderStatic:
    def test_can_instantiate_without_key(self):
        """Constructor should not fail even without an API key."""
        # Remove key if present
        old = os.environ.pop("DEEPSEEK_API_KEY", None)
        try:
            provider = DeepSeekProvider()
            assert provider.model == "deepseek-chat"
            assert provider.api_key == ""
        finally:
            if old is not None:
                os.environ["DEEPSEEK_API_KEY"] = old

    def test_generate_without_key_raises_clear_error(self):
        old = os.environ.pop("DEEPSEEK_API_KEY", None)
        try:
            provider = DeepSeekProvider()
            with pytest.raises(RuntimeError, match="DEEPSEEK_API_KEY"):
                provider.generate("test")
        finally:
            if old is not None:
                os.environ["DEEPSEEK_API_KEY"] = old

    def test_env_var_read_on_init(self):
        os.environ["DEEPSEEK_API_KEY"] = "sk-test-dummy"
        os.environ["DEEPSEEK_MODEL"] = "deepseek-test"
        os.environ["DEEPSEEK_BASE_URL"] = "https://test.example.com"
        try:
            provider = DeepSeekProvider()
            assert provider.api_key == "sk-test-dummy"
            assert provider.model == "deepseek-test"
            assert provider.base_url == "https://test.example.com"
        finally:
            del os.environ["DEEPSEEK_API_KEY"]
            del os.environ["DEEPSEEK_MODEL"]
            del os.environ["DEEPSEEK_BASE_URL"]

    def test_explicit_args_override_env(self):
        os.environ["DEEPSEEK_API_KEY"] = "env-key"
        try:
            provider = DeepSeekProvider(api_key="arg-key")
            assert provider.api_key == "arg-key"
        finally:
            del os.environ["DEEPSEEK_API_KEY"]

    def test_default_base_url(self):
        old_api = os.environ.pop("DEEPSEEK_API_KEY", None)
        old_url = os.environ.pop("DEEPSEEK_BASE_URL", None)
        try:
            provider = DeepSeekProvider()
            assert "api.deepseek.com" in provider.base_url
        finally:
            if old_api is not None:
                os.environ["DEEPSEEK_API_KEY"] = old_api
            if old_url is not None:
                os.environ["DEEPSEEK_BASE_URL"] = old_url

    def test_no_real_network_request(self):
        """Even with a fake key, a real call would hit the network.
        We only verify the error path — no actual HTTP."""
        os.environ["DEEPSEEK_API_KEY"] = "sk-fake-key-for-test"
        try:
            # This would try to call the real API if we called generate().
            # We just verify the provider is configured correctly.
            provider = DeepSeekProvider()
            assert provider.api_key == "sk-fake-key-for-test"
            assert provider.model == "deepseek-chat"
            # Do NOT call generate() — that would make a real HTTP request
        finally:
            del os.environ["DEEPSEEK_API_KEY"]

    def test_api_key_not_leaked_in_repr(self):
        os.environ["DEEPSEEK_API_KEY"] = "sk-secret-12345"
        try:
            provider = DeepSeekProvider()
            r = repr(provider)
            assert "sk-secret-12345" not in r
        finally:
            del os.environ["DEEPSEEK_API_KEY"]
