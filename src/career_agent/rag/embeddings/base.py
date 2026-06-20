"""Abstract embedding provider interface."""

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Pluggable text-embedding backend.

    Implementations convert text into fixed-dimensionality float vectors
    for similarity-based retrieval.
    """

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Return a vector for a single text."""
        ...

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return vectors for multiple texts (default loops over embed_text)."""
        return [self.embed_text(t) for t in texts]

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Dimensionality of the vectors returned by this provider."""
        ...
