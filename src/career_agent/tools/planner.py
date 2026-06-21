"""Controlled Planner — rule-based tool selection from agent state.

No autonomous LLM decisions.  The planner reads AgentState and returns
the next tool to invoke.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PlannerDecision:
    """Structured planner decision."""

    next_tool: str = ""
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class ControlledPlanner:
    """Rule-based planner — selects the next tool based on state.

    Parameters
    ----------
    min_score : float
        Minimum retrieval score to skip retry (default 0.65).
    max_retries : int
        Maximum query rewrite retries (default 2).
    faithfulness_threshold : float
        Minimum faithfulness score to pass (default 0.75).
    """

    def __init__(
        self,
        min_score: float = 0.65,
        max_retries: int = 2,
        faithfulness_threshold: float = 0.75,
    ) -> None:
        self.min_score = min_score
        self.max_retries = max_retries
        self.faithfulness_threshold = faithfulness_threshold

    def decide(self, state: dict[str, Any]) -> PlannerDecision:
        """Inspect state and return the next tool to execute."""
        # Step 1: parse JD
        if state.get("parsed_jd") is None:
            return PlannerDecision(next_tool="parse_jd", reason="no parsed_jd")

        # Step 2: plan queries
        if not state.get("queries"):
            return PlannerDecision(next_tool="plan_queries", reason="no queries")

        # Step 3: retrieve
        if not state.get("retrieved_chunks"):
            return PlannerDecision(next_tool="retrieve_profile", reason="no retrieved_chunks")

        # Step 4: rerank
        if not state.get("reranked_chunks"):
            return PlannerDecision(next_tool="rerank_chunks", reason="no reranked_chunks")

        # Step 5: grade
        if state.get("retrieval_scores") is None:
            return PlannerDecision(next_tool="grade_retrieval", reason="no retrieval_scores")

        # Step 6: retry decision
        rs = state["retrieval_scores"]
        total_score = rs.metadata.get("total_score", 0) if hasattr(rs, "metadata") else 0
        retry_count = state.get("retry_count", 0)

        if total_score < self.min_score:
            if retry_count < self.max_retries:
                return PlannerDecision(
                    next_tool="rewrite_query",
                    reason=f"score {total_score:.2f} < {self.min_score}, retry {retry_count}/{self.max_retries}",
                )
            return PlannerDecision(
                next_tool="fallback",
                reason=f"score {total_score:.2f} < {self.min_score}, max retries ({self.max_retries}) exhausted",
            )

        # Step 7: match analysis
        if state.get("match_analysis") is None:
            return PlannerDecision(next_tool="analyze_match", reason="no match_analysis")

        # Step 8: generate
        if state.get("generated_result") is None:
            return PlannerDecision(next_tool="generate_grounded_answer", reason="no generated_result")

        # Step 9: faithfulness
        if state.get("faithfulness_report") is None:
            return PlannerDecision(next_tool="check_faithfulness", reason="no faithfulness_report")

        # Step 10: final check
        fr = state.get("faithfulness_report")
        if fr is not None and hasattr(fr, "faithfulness_score"):
            if fr.faithfulness_score < self.faithfulness_threshold:
                return PlannerDecision(
                    next_tool="generate_grounded_answer",
                    reason=f"faithfulness {fr.faithfulness_score:.2f} < {self.faithfulness_threshold}, revise required",
                    metadata={"revise_required": True},
                )

        # Step 11: report
        if not state.get("report_path"):
            return PlannerDecision(next_tool="write_report", reason="no report")

        # Step 12: diagnostics
        if not state.get("diagnostics_path"):
            return PlannerDecision(next_tool="write_diagnostics", reason="final step")

        # Done
        return PlannerDecision(next_tool="done", reason="all steps complete")
