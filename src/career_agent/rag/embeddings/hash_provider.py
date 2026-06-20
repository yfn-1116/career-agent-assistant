"""Hash-based pseudo-embedding provider — deterministic, no network."""

import hashlib
import struct

from career_agent.rag.embeddings.base import EmbeddingProvider


class HashEmbeddingProvider(EmbeddingProvider):
    """Generate deterministic pseudo-vectors from character trigram hashing.

    This is NOT a semantic embedding.  It maps each unique text to a
    deterministic vector and makes texts with many overlapping trigrams
    produce similar vectors.  Useful for pipeline testing without
    external API calls.

    Parameters
    ----------
    dim : int
        Vector dimensionality (default 64).
    """

    def __init__(self, dim: int = 64) -> None:
        self._dim = dim

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_text(self, text: str) -> list[float]:
        if not text:
            return [0.0] * self._dim

        # Extract character trigrams
        trigrams = [text[i : i + 3] for i in range(max(len(text) - 2, 1))]

        # Hash each trigram into a dimension index
        vec = [0.0] * self._dim
        for tg in trigrams:
            h = hashlib.md5(tg.encode("utf-8")).digest()
            idx = struct.unpack("<I", h[:4])[0] % self._dim
            vec[idx] += 1.0

        # Normalise to unit length (or near it)
        norm = sum(v * v for v in vec) ** 0.5
        if norm > 0:
            vec = [v / norm for v in vec]

        return vec
