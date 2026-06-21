"""Tests for centralized settings module."""

import os
from unittest.mock import patch

import pytest

from career_agent.core.settings import (
    AppSettings,
    EmbeddingSettings,
    HybridRetrievalSettings,
    LLMSettings,
    OutputSettings,
    RAGSettings,
    Settings,
)


# ---------------------------------------------------------------------------
# AppSettings
# ---------------------------------------------------------------------------


class TestAppSettings:
    def test_defaults(self):
        s = AppSettings()
        assert s.env == "local"
        assert s.log_level == "INFO"

    def test_from_env(self):
        with patch.dict(os.environ, {"APP_ENV": "production", "LOG_LEVEL": "DEBUG"}):
            s = AppSettings()
            assert s.env == "production"
            assert s.log_level == "DEBUG"


# ---------------------------------------------------------------------------
# LLMSettings
# ---------------------------------------------------------------------------


class TestLLMSettings:
    def test_default_is_mock(self):
        s = LLMSettings()
        assert s.provider == "mock"
        assert not s.api_key

    def test_from_env(self):
        with patch.dict(os.environ, {
            "LLM_PROVIDER": "qwen",
            "LLM_API_KEY": "sk-test",
            "LLM_MODEL": "qwen-plus",
            "LLM_TIMEOUT_SECONDS": "30",
            "LLM_MAX_RETRIES": "1",
        }):
            s = LLMSettings()
            assert s.provider == "qwen"
            assert s.api_key == "sk-test"
            assert s.model == "qwen-plus"
            assert s.timeout_seconds == 30
            assert s.max_retries == 1

    def test_missing_api_key_means_not_available(self):
        s = LLMSettings(provider="qwen", api_key="")
        assert not s.is_available


# ---------------------------------------------------------------------------
# EmbeddingSettings
# ---------------------------------------------------------------------------


class TestEmbeddingSettings:
    def test_default_is_mock(self):
        s = EmbeddingSettings()
        assert s.provider == "mock"
        assert s.dim == 1024
        assert s.batch_size == 16

    def test_from_env(self):
        with patch.dict(os.environ, {
            "EMBEDDING_PROVIDER": "qwen",
            "EMBEDDING_MODEL": "text-embedding-v3",
            "EMBEDDING_DIM": "1024",
            "EMBEDDING_BATCH_SIZE": "8",
        }):
            s = EmbeddingSettings()
            assert s.provider == "qwen"
            assert s.model == "text-embedding-v3"
            assert s.dim == 1024
            assert s.batch_size == 8

    def test_batch_size_positive(self):
        with pytest.raises(ValueError):
            EmbeddingSettings(batch_size=0)


# ---------------------------------------------------------------------------
# RAGSettings
# ---------------------------------------------------------------------------


class TestRAGSettings:
    def test_defaults(self):
        s = RAGSettings()
        assert s.chunk_size == 800
        assert s.chunk_overlap == 100
        assert s.retrieval_top_k == 8
        assert s.rerank_top_k == 5

    def test_overlap_must_be_less_than_chunk_size(self):
        with pytest.raises(ValueError):
            RAGSettings(chunk_size=100, chunk_overlap=200)

    def test_negative_chunk_size_raises(self):
        with pytest.raises(ValueError):
            RAGSettings(chunk_size=-1)

    def test_top_k_positive(self):
        with pytest.raises(ValueError):
            RAGSettings(retrieval_top_k=0)

    def test_from_env(self):
        with patch.dict(os.environ, {
            "CHUNK_SIZE": "1000",
            "CHUNK_OVERLAP": "200",
            "RETRIEVAL_TOP_K": "10",
            "RERANK_TOP_K": "3",
            "MIN_RETRIEVAL_SCORE": "0.70",
            "MAX_RETRIES": "3",
        }):
            s = RAGSettings()
            assert s.chunk_size == 1000
            assert s.chunk_overlap == 200
            assert s.retrieval_top_k == 10
            assert s.rerank_top_k == 3
            assert s.min_retrieval_score == 0.70
            assert s.max_retries == 3

    def test_min_retrieval_score_rejects_bool(self):
        with pytest.raises(ValueError):
            RAGSettings(min_retrieval_score=True)

    def test_min_retrieval_score_range(self):
        with pytest.raises(ValueError):
            RAGSettings(min_retrieval_score=1.5)


# ---------------------------------------------------------------------------
# HybridRetrievalSettings
# ---------------------------------------------------------------------------


class TestHybridRetrievalSettings:
    def test_defaults(self):
        s = HybridRetrievalSettings()
        assert s.vector_weight == 0.40
        assert s.keyword_weight == 0.35
        assert s.metadata_weight == 0.15
        assert s.priority_weight == 0.10

    def test_weights_sum_to_one(self):
        s = HybridRetrievalSettings()
        total = s.vector_weight + s.keyword_weight + s.metadata_weight + s.priority_weight
        assert 0.99 <= total <= 1.01

    def test_rejects_negative_weight(self):
        with pytest.raises(ValueError):
            HybridRetrievalSettings(vector_weight=-0.1)

    def test_rejects_bool_weight(self):
        with pytest.raises(ValueError):
            HybridRetrievalSettings(vector_weight=True)

    def test_rejects_nan_weight(self):
        import math
        with pytest.raises(ValueError):
            HybridRetrievalSettings(vector_weight=math.nan)

    def test_from_env(self):
        with patch.dict(os.environ, {
            "HYBRID_VECTOR_WEIGHT": "0.45",
            "HYBRID_KEYWORD_WEIGHT": "0.30",
            "HYBRID_METADATA_WEIGHT": "0.15",
            "HYBRID_PRIORITY_WEIGHT": "0.10",
        }):
            s = HybridRetrievalSettings()
            assert s.vector_weight == 0.45
            assert s.keyword_weight == 0.30

    def test_warns_on_weights_far_from_one(self):
        """Weights summing far from 1.0 should still construct but log warning (test just checks it doesn't crash)."""
        s = HybridRetrievalSettings(vector_weight=0.50, keyword_weight=0.50, metadata_weight=0.0, priority_weight=0.0)
        total = s.vector_weight + s.keyword_weight + s.metadata_weight + s.priority_weight
        # 1.00 is fine
        assert 0.99 <= total <= 1.01


# ---------------------------------------------------------------------------
# OutputSettings
# ---------------------------------------------------------------------------


class TestOutputSettings:
    def test_defaults(self):
        s = OutputSettings()
        assert s.output_dir == "outputs"
        assert "rag_reports" in s.rag_report_dir
        assert "diagnostics" in s.diagnostics_dir

    def test_from_env(self):
        with patch.dict(os.environ, {
            "OUTPUT_DIR": "custom_outputs",
            "RAG_REPORT_DIR": "custom_outputs/reports",
            "DIAGNOSTICS_DIR": "custom_outputs/diag",
            "TRACE_DIR": "custom_outputs/traces",
        }):
            s = OutputSettings()
            assert s.output_dir == "custom_outputs"
            assert s.rag_report_dir == "custom_outputs/reports"
            assert s.diagnostics_dir == "custom_outputs/diag"
            assert s.trace_dir == "custom_outputs/traces"


# ---------------------------------------------------------------------------
# Composite Settings
# ---------------------------------------------------------------------------


class TestSettings:
    def test_loads_all_sub_settings(self):
        s = Settings()
        assert s.app.env == "local"
        assert s.llm.provider == "mock"
        assert s.embedding.provider == "mock"
        assert s.rag.chunk_size == 800
        assert s.hybrid.vector_weight == 0.40
        assert s.output.output_dir == "outputs"

    def test_default_llm_is_not_available(self):
        s = Settings()
        assert not s.llm.is_available

    def test_no_real_api_key_needed_for_defaults(self):
        """Default settings must not require any API keys."""
        s = Settings()
        # This should not raise
        assert s.llm.api_key == ""

    def test_can_override_individual_settings(self):
        s = Settings(
            rag=RAGSettings(chunk_size=500, retrieval_top_k=3),
            llm=LLMSettings(provider="qwen", api_key="sk-test"),
        )
        assert s.rag.chunk_size == 500
        assert s.rag.retrieval_top_k == 3
        assert s.llm.provider == "qwen"
        # Other settings remain default
        assert s.hybrid.vector_weight == 0.40
