"""Centralised configuration — no hard-coded parameters.

All RAG, LLM, embedding, hybrid, and output settings are read from
environment variables (or constructor kwargs) and validated at init time.

Usage::

    from career_agent.core.settings import Settings
    settings = Settings()
    print(settings.rag.chunk_size)
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def _env_float(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def _validate_score(value: float, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be float, got bool")
    if not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be float, got {type(value).__name__}")
    fv = float(value)
    if not math.isfinite(fv):
        raise ValueError(f"{name} must be finite, got {fv}")
    if fv < 0.0 or fv > 1.0:
        raise ValueError(f"{name} must be in [0.0, 1.0], got {fv}")
    return fv


def _validate_positive(value: int, name: str) -> int:
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    return value


# ---------------------------------------------------------------------------
# AppSettings
# ---------------------------------------------------------------------------


@dataclass
class AppSettings:
    env: str = field(default_factory=lambda: _env("APP_ENV", "local"))
    log_level: str = field(default_factory=lambda: _env("LOG_LEVEL", "INFO"))


# ---------------------------------------------------------------------------
# LLMSettings
# ---------------------------------------------------------------------------


@dataclass
class LLMSettings:
    provider: str = field(default_factory=lambda: _env("LLM_PROVIDER", "mock"))
    api_key: str = field(default_factory=lambda: _env("LLM_API_KEY", ""))
    model: str = field(default_factory=lambda: _env("LLM_MODEL", ""))
    base_url: str = field(default_factory=lambda: _env("LLM_BASE_URL", ""))
    timeout_seconds: int = field(
        default_factory=lambda: _env_int("LLM_TIMEOUT_SECONDS", 60)
    )
    max_retries: int = field(
        default_factory=lambda: _env_int("LLM_MAX_RETRIES", 2)
    )

    @property
    def is_available(self) -> bool:
        return self.provider != "mock" and bool(self.api_key)


# ---------------------------------------------------------------------------
# EmbeddingSettings
# ---------------------------------------------------------------------------


@dataclass
class EmbeddingSettings:
    provider: str = field(
        default_factory=lambda: _env("EMBEDDING_PROVIDER", "mock")
    )
    api_key: str = field(
        default_factory=lambda: _env("EMBEDDING_API_KEY", "") or _env("QWEN_API_KEY", "")
    )
    model: str = field(default_factory=lambda: _env("EMBEDDING_MODEL", ""))
    dim: int = field(default_factory=lambda: _env_int("EMBEDDING_DIM", 1024))
    batch_size: int = field(
        default_factory=lambda: _env_int("EMBEDDING_BATCH_SIZE", 16)
    )

    def __post_init__(self) -> None:
        _validate_positive(self.batch_size, "batch_size")


# ---------------------------------------------------------------------------
# RAGSettings
# ---------------------------------------------------------------------------


@dataclass
class RAGSettings:
    chunk_size: int = field(
        default_factory=lambda: _env_int("CHUNK_SIZE", 800)
    )
    chunk_overlap: int = field(
        default_factory=lambda: _env_int("CHUNK_OVERLAP", 100)
    )
    retrieval_top_k: int = field(
        default_factory=lambda: _env_int("RETRIEVAL_TOP_K", 8)
    )
    rerank_top_k: int = field(
        default_factory=lambda: _env_int("RERANK_TOP_K", 5)
    )
    min_retrieval_score: float = field(
        default_factory=lambda: _env_float("MIN_RETRIEVAL_SCORE", 0.65)
    )
    max_retries: int = field(
        default_factory=lambda: _env_int("MAX_RETRIES", 2)
    )

    def __post_init__(self) -> None:
        _validate_positive(self.chunk_size, "chunk_size")
        _validate_positive(self.retrieval_top_k, "retrieval_top_k")
        _validate_positive(self.rerank_top_k, "rerank_top_k")
        if self.chunk_overlap < 0:
            raise ValueError(f"chunk_overlap must be >= 0, got {self.chunk_overlap}")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                f"chunk_overlap ({self.chunk_overlap}) must be less than "
                f"chunk_size ({self.chunk_size})"
            )
        if self.max_retries < 0:
            raise ValueError(f"max_retries must be >= 0, got {self.max_retries}")
        _validate_score(self.min_retrieval_score, "min_retrieval_score")


# ---------------------------------------------------------------------------
# HybridRetrievalSettings
# ---------------------------------------------------------------------------


@dataclass
class HybridRetrievalSettings:
    vector_weight: float = field(
        default_factory=lambda: _env_float("HYBRID_VECTOR_WEIGHT", 0.40)
    )
    keyword_weight: float = field(
        default_factory=lambda: _env_float("HYBRID_KEYWORD_WEIGHT", 0.35)
    )
    metadata_weight: float = field(
        default_factory=lambda: _env_float("HYBRID_METADATA_WEIGHT", 0.15)
    )
    priority_weight: float = field(
        default_factory=lambda: _env_float("HYBRID_PRIORITY_WEIGHT", 0.10)
    )

    def __post_init__(self) -> None:
        self.vector_weight = _validate_score(self.vector_weight, "vector_weight")
        self.keyword_weight = _validate_score(self.keyword_weight, "keyword_weight")
        self.metadata_weight = _validate_score(self.metadata_weight, "metadata_weight")
        self.priority_weight = _validate_score(self.priority_weight, "priority_weight")
        total = (
            self.vector_weight
            + self.keyword_weight
            + self.metadata_weight
            + self.priority_weight
        )
        if total < 0.95 or total > 1.05:
            # We log a warning but don't crash — user may want custom weights
            import logging
            logging.getLogger(__name__).warning(
                "Hybrid weights sum to %.2f (expected ~1.0)", total
            )


# ---------------------------------------------------------------------------
# OutputSettings
# ---------------------------------------------------------------------------


@dataclass
class OutputSettings:
    output_dir: str = field(
        default_factory=lambda: _env("OUTPUT_DIR", "outputs")
    )
    rag_report_dir: str = field(
        default_factory=lambda: _env("RAG_REPORT_DIR", "outputs/rag_reports")
    )
    diagnostics_dir: str = field(
        default_factory=lambda: _env("DIAGNOSTICS_DIR", "outputs/diagnostics")
    )
    trace_dir: str = field(
        default_factory=lambda: _env("TRACE_DIR", "outputs/traces")
    )


# ---------------------------------------------------------------------------
# Composite Settings
# ---------------------------------------------------------------------------


@dataclass
class Settings:
    """Top-level settings aggregator."""

    app: AppSettings = field(default_factory=AppSettings)
    llm: LLMSettings = field(default_factory=LLMSettings)
    embedding: EmbeddingSettings = field(default_factory=EmbeddingSettings)
    rag: RAGSettings = field(default_factory=RAGSettings)
    hybrid: HybridRetrievalSettings = field(default_factory=HybridRetrievalSettings)
    output: OutputSettings = field(default_factory=OutputSettings)
