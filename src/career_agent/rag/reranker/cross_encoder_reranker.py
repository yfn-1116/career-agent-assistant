"""Cross-Encoder Reranker — ML-based fine-grained re-ranking.

Replaces the rule-based LightweightReranker with a Cross-Encoder model
(bge-reranker-base) that reads (query, chunk) pairs and produces a
relevance score through a full Transformer forward pass.

Dependencies: pip install transformers torch
Model: BAAI/bge-reranker-base (~1.1 GB, downloaded on first use)
"""

from __future__ import annotations

from typing import Any

from career_agent.rag.schemas import RetrievedEvidence


class CrossEncoderReranker:
    """Cross-Encoder reranker using bge-reranker-base.

    Parameters
    ----------
    model_name : str
        HuggingFace model ID (default ``"BAAI/bge-reranker-base"``).
    device : str
        ``"cpu"``, ``"cuda"``, or ``"auto"`` (default).
    batch_size : int
        Number of pairs to score per forward pass (default 16).
    max_length : int
        Max token length per input (default 512).
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-base",
        device: str = "auto",
        batch_size: int = 16,
        max_length: int = 512,
    ) -> None:
        self.model_name = model_name
        self.batch_size = batch_size
        self.max_length = max_length
        self._model: Any = None
        self._tokenizer: Any = None
        self._device = device
        self._loaded = False

    # -- lazy loading --------------------------------------------------------

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return

        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self._tokenizer = AutoTokenizer.from_pretrained(
            self.model_name
        )
        self._model = AutoModelForSequenceClassification.from_pretrained(
            self.model_name
        )

        if self._device == "auto":
            self._device = "cuda" if torch.cuda.is_available() else "cpu"

        self._model = self._model.to(self._device)
        self._model.eval()
        self._loaded = True

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def device(self) -> str:
        return self._device

    # -- reranking -----------------------------------------------------------

    def rerank(
        self,
        query: str,
        chunks: list[RetrievedEvidence],
        top_n: int = 5,
    ) -> list[tuple[RetrievedEvidence, float]]:
        """Rerank candidate chunks with Cross-Encoder scoring.

        Parameters
        ----------
        query : str
            The search query / user question.
        chunks : list[RetrievedEvidence]
            Candidate chunks to rerank.
        top_n : int
            Number of top results to return (default 5).

        Returns
        -------
        list of (RetrievedEvidence, float)
            Reranked list with Cross-Encoder scores, descending.
        """
        if not chunks:
            return []

        self._ensure_loaded()

        import torch

        all_scores: list[float] = []

        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i : i + self.batch_size]

            pairs = [[query, c.content] for c in batch]

            inputs = self._tokenizer(
                pairs,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt",
            ).to(self._device)

            with torch.no_grad():
                outputs = self._model(**inputs)
                batch_scores = outputs.logits.squeeze(-1)

            if batch_scores.dim() == 0:
                batch_scores = batch_scores.unsqueeze(0)

            all_scores.extend(batch_scores.detach().cpu().tolist())

        # Pair and sort
        ranked = sorted(
            zip(chunks, all_scores),
            key=lambda x: x[1],
            reverse=True,
        )

        return ranked[:top_n]

    def rerank_and_filter(
        self,
        query: str,
        chunks: list[RetrievedEvidence],
        top_n: int = 5,
        min_score: float | None = None,
    ) -> tuple[list[RetrievedEvidence], list[tuple[RetrievedEvidence, float]], bool]:
        """Rerank, filter by min_score, and return (selected, all_ranked, enough_evidence).

        Parameters
        ----------
        query, chunks, top_n : same as rerank()
        min_score : float or None
            If None, no filtering (always returns top_n).
            If set, chunks below this score are excluded.

        Returns
        -------
        selected : list[RetrievedEvidence]
            Top chunks above min_score threshold.
        all_ranked : list of (RetrievedEvidence, float)
            All scored pairs for debugging.
        enough_evidence : bool
            True if at least one chunk passed min_score, or min_score is None.
        """
        all_ranked = self.rerank(query, chunks, top_n=len(chunks))

        if min_score is None:
            selected = [c for c, _s in all_ranked[:top_n]]
            return selected, all_ranked, True

        selected = []
        for chunk, score in all_ranked:
            if score >= min_score:
                selected.append(chunk)

        selected = selected[:top_n]
        enough_evidence = len(selected) > 0

        return selected, all_ranked, enough_evidence
