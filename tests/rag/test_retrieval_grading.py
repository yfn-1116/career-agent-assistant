import math

from career_agent.agents.state import ParsedJD
from career_agent.rag.grading import (
    AVERAGE_SCORE_PASS_THRESHOLD,
    RetrievalGradeReport,
    grade_retrieval,
)
from career_agent.rag.schemas import RetrievedEvidence


def _evidence(
    content: str = "Python RAG Agent workflow",
    score: float = 0.8,
    source_path: str = "profile.md",
    chunk_id: str = "chunk-1",
    matched_keywords: list[str] | None = None,
) -> RetrievedEvidence:
    return RetrievedEvidence(
        evidence_id=f"ev-{chunk_id}",
        chunk_id=chunk_id,
        title="Project",
        content=content,
        score=score,
        source_path=source_path,
        matched_keywords=(
            matched_keywords if matched_keywords is not None else ["Python", "RAG"]
        ),
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


def test_representative_successful_retrieval_returns_good():
    jd = ParsedJD(hard_skills=["Python"], keywords=["RAG", "Agent"])

    report = grade_retrieval(
        query="Python RAG Agent",
        parsed_jd=jd,
        evidence=[
            _evidence(
                content="Python RAG workflow",
                source_path="a.md",
                chunk_id="a",
                score=0.7,
            ),
            _evidence(
                content="Python RAG workflow",
                source_path="b.md",
                chunk_id="b",
                score=0.7,
            ),
        ],
        top_k=5,
    )

    assert report.grade == "good"
    assert report.evidence_count == 2
    assert report.keyword_coverage >= 0.5
    assert report.source_diversity == 2
    assert report.evidence_summaries[0]["source_path"] == "a.md"


def test_keyword_coverage_does_not_match_inside_longer_word():
    jd = ParsedJD(hard_skills=["Go"], keywords=[])

    report = grade_retrieval(
        query="Go",
        parsed_jd=jd,
        evidence=[
            _evidence(
                content="Built a Django API service",
                matched_keywords=[],
                source_path="a.md",
                chunk_id="a",
            )
        ],
        top_k=5,
    )

    assert report.keyword_coverage == 0.0


def test_keyword_coverage_matches_exact_normalized_matched_keywords():
    jd = ParsedJD(hard_skills=["Go"], keywords=[])

    report = grade_retrieval(
        query="Go",
        parsed_jd=jd,
        evidence=[
            _evidence(
                content="Built backend services",
                matched_keywords=[" go "],
                source_path="a.md",
                chunk_id="a",
            )
        ],
        top_k=5,
    )

    assert report.keyword_coverage == 1.0


def test_keyword_coverage_matches_multi_word_phrase_with_term_boundaries():
    jd = ParsedJD(hard_skills=[], keywords=["machine learning"])

    report = grade_retrieval(
        query="machine learning",
        parsed_jd=jd,
        evidence=[
            _evidence(
                content="Built a machine learning ranking pipeline.",
                matched_keywords=[],
                source_path="a.md",
                chunk_id="a",
            )
        ],
        top_k=5,
    )

    assert report.keyword_coverage == 1.0


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


def test_strong_retrieval_with_three_sources_and_full_coverage_is_excellent():
    jd = ParsedJD(hard_skills=["Python"], keywords=["RAG", "Agent"])

    report = grade_retrieval(
        query="Python RAG Agent",
        parsed_jd=jd,
        evidence=[
            _evidence(
                content="Python RAG Agent workflow",
                score=0.9,
                source_path="a.md",
                chunk_id="a",
            ),
            _evidence(
                content="Python RAG Agent workflow",
                score=0.9,
                source_path="b.md",
                chunk_id="b",
            ),
            _evidence(
                content="Python RAG Agent workflow",
                score=0.9,
                source_path="c.md",
                chunk_id="c",
            ),
        ],
        top_k=5,
    )

    assert report.grade == "excellent"
    assert report.keyword_coverage == 1.0
    assert report.source_diversity == 3


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


def test_nan_score_fails_traceability():
    jd = ParsedJD(hard_skills=["Python"], keywords=["RAG"])
    ev = _evidence()
    ev.score = math.nan

    report = grade_retrieval(
        query="Python RAG",
        parsed_jd=jd,
        evidence=[ev],
        top_k=5,
    )

    assert report.grade == "failed"
    traceability = [item for item in report.items if item.name == "traceability"][0]
    assert not traceability.passed


def test_infinite_score_fails_traceability():
    jd = ParsedJD(hard_skills=["Python"], keywords=["RAG"])
    ev = _evidence()
    ev.score = math.inf

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
