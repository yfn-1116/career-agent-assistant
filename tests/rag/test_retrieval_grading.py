from career_agent.agents.state import ParsedJD
from career_agent.rag.grading import (
    AVERAGE_SCORE_PASS_THRESHOLD,
    KEYWORD_COVERAGE_PASS_THRESHOLD,
    SOURCE_DIVERSITY_TARGET,
    TOTAL_SCORE_EXCELLENT_THRESHOLD,
    TOTAL_SCORE_FAILED_THRESHOLD,
    TOTAL_SCORE_GOOD_THRESHOLD,
    RetrievalGradeReport,
    grade_retrieval,
)
from career_agent.rag.schemas import RetrievedEvidence


def _evidence(
    content: str = "Python RAG Agent workflow",
    score: float = 0.8,
    source_path: str = "profile.md",
    chunk_id: str = "chunk-1",
) -> RetrievedEvidence:
    return RetrievedEvidence(
        evidence_id=f"ev-{chunk_id}",
        chunk_id=chunk_id,
        title="Project",
        content=content,
        score=score,
        source_path=source_path,
        matched_keywords=["Python", "RAG"],
    )


def test_no_evidence_returns_failed_report():
    jd = ParsedJD(hard_skills=["Python"], keywords=["RAG"])

    report = grade_retrieval(
        query="Python RAG",
        parsed_jd=jd,
        evidence=[],
        top_k=5,
    )

    assert isinstance(report, RetrievalGradeReport)
    assert report.grade == "failed"
    assert report.evidence_count == 0
    assert report.average_score == 0.0
    assert any(item.name == "evidence_count" for item in report.items)


def test_good_evidence_returns_good_or_excellent():
    jd = ParsedJD(hard_skills=["Python"], keywords=["RAG", "Agent"])

    report = grade_retrieval(
        query="Python RAG Agent",
        parsed_jd=jd,
        evidence=[
            _evidence(source_path="a.md", chunk_id="a"),
            _evidence(source_path="b.md", chunk_id="b", score=0.7),
        ],
        top_k=5,
    )

    assert report.grade in {"good", "excellent"}
    assert report.evidence_count == 2
    assert report.keyword_coverage >= 0.5
    assert report.source_diversity == 2
    assert report.evidence_summaries[0]["source_path"] == "a.md"


def test_missing_traceability_fails():
    jd = ParsedJD(hard_skills=["Python"], keywords=["RAG"])

    report = grade_retrieval(
        query="Python RAG",
        parsed_jd=jd,
        evidence=[_evidence(source_path="", chunk_id="")],
        top_k=5,
    )

    assert report.grade == "failed"
    traceability = [item for item in report.items if item.name == "traceability"][0]
    assert not traceability.passed


def test_threshold_constants_are_available_for_edge_cases():
    assert AVERAGE_SCORE_PASS_THRESHOLD == 0.35
    assert KEYWORD_COVERAGE_PASS_THRESHOLD == 0.5
    assert SOURCE_DIVERSITY_TARGET == 3
    assert TOTAL_SCORE_FAILED_THRESHOLD == 0.35
    assert TOTAL_SCORE_GOOD_THRESHOLD == 0.65
    assert TOTAL_SCORE_EXCELLENT_THRESHOLD == 0.85


def test_score_at_average_threshold_passes_average_score_item():
    jd = ParsedJD(hard_skills=["Python"], keywords=["RAG"])

    report = grade_retrieval(
        query="Python RAG",
        parsed_jd=jd,
        evidence=[_evidence(score=AVERAGE_SCORE_PASS_THRESHOLD)],
        top_k=5,
    )

    average_score = [item for item in report.items if item.name == "average_score"][0]
    assert average_score.passed


def test_missing_score_fails_traceability():
    jd = ParsedJD(hard_skills=["Python"], keywords=["RAG"])
    ev = _evidence()
    ev.score = None

    report = grade_retrieval(
        query="Python RAG",
        parsed_jd=jd,
        evidence=[ev],
        top_k=5,
    )

    assert report.grade == "failed"
    traceability = [item for item in report.items if item.name == "traceability"][0]
    assert not traceability.passed


def test_non_numeric_score_fails_traceability():
    jd = ParsedJD(hard_skills=["Python"], keywords=["RAG"])
    ev = _evidence()
    ev.score = "0.8"

    report = grade_retrieval(
        query="Python RAG",
        parsed_jd=jd,
        evidence=[ev],
        top_k=5,
    )

    assert report.grade == "failed"
    traceability = [item for item in report.items if item.name == "traceability"][0]
    assert not traceability.passed
