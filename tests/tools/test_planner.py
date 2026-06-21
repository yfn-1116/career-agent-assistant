"""Tests for ControlledPlanner."""

from career_agent.domain.schemas import ParsedJD
from career_agent.rag.grading import RetrievalGradeReport
from career_agent.tools.planner import ControlledPlanner, PlannerDecision


def _state(**overrides):
    s = {
        "raw_jd": "", "parsed_jd": None, "queries": [],
        "retrieved_chunks": [], "reranked_chunks": [],
        "retrieval_scores": None, "missing_keywords": [],
        "decision": "continue", "match_analysis": None,
        "generated_result": None, "faithfulness_report": None,
        "report_path": "", "diagnostics_path": "",
        "retry_count": 0, "max_retries": 2,
    }
    s.update(overrides)
    return s


class TestPlanner:
    def test_no_parsed_jd_selects_parse(self):
        planner = ControlledPlanner()
        d = planner.decide(_state())
        assert d.next_tool == "parse_jd"

    def test_no_queries_selects_plan(self):
        planner = ControlledPlanner()
        d = planner.decide(_state(parsed_jd=ParsedJD(job_direction="agent")))
        assert d.next_tool == "plan_queries"

    def test_no_chunks_selects_retrieve(self):
        planner = ControlledPlanner()
        d = planner.decide(_state(
            parsed_jd=ParsedJD(), queries=["Python"],
        ))
        assert d.next_tool == "retrieve_profile"

    def test_no_rerank_selects_rerank(self):
        planner = ControlledPlanner()
        d = planner.decide(_state(
            parsed_jd=ParsedJD(), queries=["q"], retrieved_chunks=[{"id": 1}],
        ))
        assert d.next_tool == "rerank_chunks"

    def test_low_score_not_exhausted_selects_rewrite(self):
        planner = ControlledPlanner(min_score=0.65, max_retries=2)
        rs = RetrievalGradeReport(
            query="test", top_k=3, evidence_count=1, average_score=0.3,
            keyword_coverage=0.1, source_diversity=1, grade="weak",
            metadata={"total_score": 0.30},
        )
        d = planner.decide(_state(
            parsed_jd=ParsedJD(), queries=["q"], retrieved_chunks=[{"id": 1}],
            reranked_chunks=[{"id": 1}], retrieval_scores=rs, retry_count=0,
        ))
        assert d.next_tool == "rewrite_query"
        assert "score 0.30" in d.reason

    def test_low_score_exhausted_selects_fallback(self):
        planner = ControlledPlanner(min_score=0.65, max_retries=2)
        rs = RetrievalGradeReport(
            query="test", top_k=3, evidence_count=1, average_score=0.3,
            keyword_coverage=0.1, source_diversity=1, grade="failed",
            metadata={"total_score": 0.20},
        )
        d = planner.decide(_state(
            parsed_jd=ParsedJD(), queries=["q"], retrieved_chunks=[{"id": 1}],
            reranked_chunks=[{"id": 1}], retrieval_scores=rs, retry_count=2,
        ))
        assert d.next_tool == "fallback"

    def test_high_score_selects_analyze(self):
        planner = ControlledPlanner(min_score=0.65)
        rs = RetrievalGradeReport(
            query="test", top_k=3, evidence_count=3, average_score=0.8,
            keyword_coverage=0.8, source_diversity=3, grade="good",
            metadata={"total_score": 0.80},
        )
        d = planner.decide(_state(
            parsed_jd=ParsedJD(), queries=["q"], retrieved_chunks=[{"id": 1}],
            reranked_chunks=[{"id": 1}], retrieval_scores=rs,
        ))
        assert d.next_tool == "analyze_match"

    def test_done_after_all_steps(self):
        planner = ControlledPlanner()
        d = planner.decide(_state(
            parsed_jd=ParsedJD(), queries=["q"], retrieved_chunks=[{"id": 1}],
            reranked_chunks=[{"id": 1}],
            retrieval_scores=RetrievalGradeReport(
                query="q", top_k=3, evidence_count=3, average_score=0.8,
                keyword_coverage=0.8, source_diversity=3, grade="good",
                metadata={"total_score": 0.80},
            ),
            match_analysis={"strengths": ["a"]},
            generated_result={"bullets": ["b"]},
            faithfulness_report={"faithfulness_score": 0.90},
            report_path="/tmp/r.md",
        ))
        assert d.next_tool == "write_diagnostics"

    def test_planner_decision_is_structured(self):
        d = PlannerDecision(next_tool="parse_jd", reason="no parsed_jd")
        assert isinstance(d.next_tool, str)
        assert isinstance(d.reason, str)
