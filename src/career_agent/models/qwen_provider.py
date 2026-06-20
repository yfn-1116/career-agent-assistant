"""Qwen (通义千问) API provider — uses stdlib only, OpenAI-compatible endpoint."""

import json
import os
import urllib.request
import urllib.error

from career_agent.models.provider import ModelProvider


class QwenProvider(ModelProvider):
    """Call the Qwen chat-completions API (OpenAI-compatible endpoint).

    Configuration is read from environment variables:

    * ``QWEN_API_KEY`` (required)
    * ``QWEN_BASE_URL`` (default ``https://dashscope.aliyuncs.com/compatible-mode/v1``)
    * ``QWEN_MODEL`` (default ``qwen-plus``)
    * ``QWEN_TIMEOUT`` (default 30 seconds)
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("QWEN_API_KEY", "")
        self.base_url = (base_url or os.getenv("QWEN_BASE_URL")
                         or "https://dashscope.aliyuncs.com/compatible-mode/v1").rstrip("/")
        self.model = model or os.getenv("QWEN_MODEL") or "qwen-plus"
        self.timeout = timeout or int(os.getenv("QWEN_TIMEOUT") or "30")

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        metadata: dict | None = None,  # noqa: ARG002
    ) -> str:
        if not self.api_key:
            raise RuntimeError(
                "QwenProvider: QWEN_API_KEY 未设置。"
                "请通过环境变量配置，或使用 MockProvider 运行。"
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

        url = f"{self.base_url}/chat/completions"
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
                f"Qwen API HTTP {exc.code}: {detail[:500]}"
            ) from exc
        except OSError as exc:
            raise RuntimeError(
                f"Qwen API 网络错误: {exc}"
            ) from exc

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError(
                f"Qwen API 返回格式异常: {json.dumps(data, ensure_ascii=False)[:500]}"
            ) from exc
