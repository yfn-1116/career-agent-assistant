"""Qwen (通义千问) Embedding provider — real semantic embeddings."""

import json
import os
import urllib.request
import urllib.error

from career_agent.rag.embeddings.base import EmbeddingProvider


class QwenEmbeddingProvider(EmbeddingProvider):
    """Qwen text embedding via OpenAI-compatible API.

    Env vars: ``QWEN_API_KEY``, ``QWEN_EMBEDDING_MODEL`` (default ``text-embedding-v3``),
    ``QWEN_EMBEDDING_BASE_URL`` (default dashscope compatible-mode endpoint).
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("QWEN_API_KEY", "")
        self.base_url = (
            base_url or os.getenv("QWEN_EMBEDDING_BASE_URL")
            or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        ).rstrip("/")
        self.model = model or os.getenv("QWEN_EMBEDDING_MODEL") or "text-embedding-v3"
        self._dim = None  # lazy from first call

    @property
    def dimension(self) -> int:
        if self._dim is None:
            v = self.embed_text("dim check")
            self._dim = len(v)
        return self._dim

    def embed_text(self, text: str) -> list[float]:
        if not self.api_key:
            raise RuntimeError("QwenEmbeddingProvider: QWEN_API_KEY 未设置")
        return self._call_api([text])[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not self.api_key:
            raise RuntimeError("QwenEmbeddingProvider: QWEN_API_KEY 未设置")
        # Qwen API limits batch to 10
        results: list[list[float]] = []
        for i in range(0, len(texts), 10):
            batch = texts[i : i + 10]
            results.extend(self._call_api(batch))
        return results

    def _call_api(self, texts: list[str]) -> list[list[float]]:
        body = json.dumps({
            "model": self.model,
            "input": texts,
            "encoding_format": "float",
        }).encode("utf-8")

        url = f"{self.base_url}/embeddings"
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Qwen Embedding HTTP {exc.code}: {detail[:500]}") from exc
        except OSError as exc:
            raise RuntimeError(f"Qwen Embedding 网络错误: {exc}") from exc

        try:
            items = sorted(data["data"], key=lambda x: x["index"])
            return [item["embedding"] for item in items]
        except (KeyError, IndexError) as exc:
            raise RuntimeError(f"Embedding 返回格式异常: {json.dumps(data, ensure_ascii=False)[:300]}") from exc
