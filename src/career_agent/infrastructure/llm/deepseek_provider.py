"""DeepSeek LLM provider — stdlib-only, no third-party HTTP client."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from career_agent.infrastructure.llm.base import LLMProvider


class DeepSeekProvider(LLMProvider):
    """DeepSeek chat-completions API.

    Reads defaults from env vars; explicit constructor args override.
    Use ``create_llm_provider`` factory for Settings-based construction.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.base_url = (
            base_url
            or os.getenv("DEEPSEEK_BASE_URL")
            or "https://api.deepseek.com"
        ).rstrip("/")
        self.model = model or os.getenv("DEEPSEEK_MODEL") or "deepseek-chat"
        self.timeout = timeout or int(os.getenv("DEEPSEEK_TIMEOUT") or "30")

    # -- LLMProvider interface ----------------------------------------------

    @property
    def model_name(self) -> str:
        return self.model

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
    ) -> str:
        if not self.api_key:
            raise RuntimeError(
                "DeepSeekProvider: DEEPSEEK_API_KEY 未设置。"
                "请通过环境变量配置，或使用 MockLLMProvider 运行。"
            )

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        body = json.dumps({
            "model": self.model,
            "messages": messages,
            "max_tokens": 1024,
        }).encode("utf-8")

        url = f"{self.base_url}/v1/chat/completions"
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"DeepSeek API HTTP {exc.code}: {detail[:500]}"
            ) from exc
        except OSError as exc:
            raise RuntimeError(f"DeepSeek API 网络错误: {exc}") from exc

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError(
                f"DeepSeek API 返回格式异常: "
                f"{json.dumps(data, ensure_ascii=False)[:500]}"
            ) from exc
