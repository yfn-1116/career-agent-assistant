"""Lightweight evaluation rules for JobMatchWorkflow output quality.

All rules operate on ``AgentTaskState`` and return ``EvaluationItem``.
None of them call external models or modify state.
"""

from career_agent.agents.state import AgentTaskState
from career_agent.evaluation.schemas import EvaluationItem, EvaluationReport


# -- individual rules -------------------------------------------------------

def evaluate_no_empty_status(state: AgentTaskState) -> EvaluationItem:
    """Check that workflow completed without errors."""
    if state.status == "completed" and not state.error_message:
        return EvaluationItem(
            name="workflow_status",
            passed=True,
            score=1.0,
            message="Workflow completed without errors.",
        )
    return EvaluationItem(
        name="workflow_status",
        passed=False,
        score=0.0,
        message=f"Status: {state.status}, error: {state.error_message or 'N/A'}",
    )


def evaluate_evidence_count(state: AgentTaskState) -> EvaluationItem:
    """Check that at least one piece of evidence was retrieved."""
    count = len(state.retrieved_evidence)
    if count > 0:
        return EvaluationItem(
            name="evidence_count",
            passed=True,
            score=1.0,
            message=f"Retrieved {count} evidence items.",
        )
    return EvaluationItem(
        name="evidence_count",
        passed=False,
        score=0.0,
        message="No evidence retrieved.",
    )


def evaluate_generated_output_non_empty(state: AgentTaskState) -> EvaluationItem:
    """Check that generated output contains non-empty fields."""
    go = state.generated_output
    if go is None:
        return EvaluationItem(
            name="generated_output_non_empty",
            passed=False,
            score=0.0,
            message="generated_output is None.",
        )

    checks = [
        bool(go.summary),
        bool(go.resume_bullets),
        bool(go.communication_message),
    ]
    passed_count = sum(checks)
    score = passed_count / len(checks) if checks else 0.0

    return EvaluationItem(
        name="generated_output_non_empty",
        passed=passed_count == len(checks),
        score=score,
        message=(
            f"summary: {'OK' if checks[0] else 'EMPTY'}, "
            f"resume_bullets: {'OK' if checks[1] else 'EMPTY'}, "
            f"communication_message: {'OK' if checks[2] else 'EMPTY'}"
        ),
    )


def evaluate_evidence_refs(state: AgentTaskState) -> EvaluationItem:
    """Check that generated_output.evidence_refs match retrieved evidence."""
    go = state.generated_output
    if go is None:
        return EvaluationItem(
            name="evidence_refs",
            passed=False,
            score=0.0,
            message="generated_output is None.",
        )

    ev_ids = {ev.evidence_id for ev in state.retrieved_evidence}
    refs = set(go.evidence_refs)

    if not refs:
        return EvaluationItem(
            name="evidence_refs",
            passed=False,
            score=0.0,
            message="No evidence_refs in generated output.",
        )

    valid = refs & ev_ids
    score = len(valid) / len(refs) if refs else 0.0

    return EvaluationItem(
        name="evidence_refs",
        passed=score >= 0.5,
        score=score,
        message=f"{len(valid)}/{len(refs)} refs traceable to evidence.",
    )


def evaluate_keyword_coverage(state: AgentTaskState) -> EvaluationItem:
    """Check how many parsed JD keywords appear in evidence keywords."""
    jd = state.parsed_jd
    if jd is None:
        return EvaluationItem(
            name="keyword_coverage",
            passed=False,
            score=0.0,
            message="parsed_jd is None.",
        )

    jd_kw = {kw.lower() for kw in (jd.hard_skills + jd.keywords)}
    if not jd_kw:
        return EvaluationItem(
            name="keyword_coverage",
            passed=True,
            score=1.0,
            message="No JD keywords to check.",
        )

    ev_kw: set[str] = set()
    for ev in state.retrieved_evidence:
        for kw in ev.matched_keywords:
            ev_kw.add(kw.lower())

    matched = jd_kw & ev_kw
    score = len(matched) / len(jd_kw) if jd_kw else 1.0

    return EvaluationItem(
        name="keyword_coverage",
        passed=score >= 0.1,
        score=score,
        message=f"{len(matched)}/{len(jd_kw)} JD keywords matched by evidence.",
    )


# -- aggregator -------------------------------------------------------------

def evaluate_state(
    state: AgentTaskState, case_id: str = "", job_file: str = ""
) -> EvaluationReport:
    """Run all evaluation rules against *state* and return a report."""
    items = [
        evaluate_no_empty_status(state),
        evaluate_evidence_count(state),
        evaluate_generated_output_non_empty(state),
        evaluate_evidence_refs(state),
        evaluate_keyword_coverage(state),
    ]

    scores = [it.score for it in items]
    total = sum(scores) / len(scores) if scores else 0.0

    passed_count = sum(1 for it in items if it.passed)
    summary = (
        f"Case '{case_id or state.task_id}': "
        f"{passed_count}/{len(items)} checks passed, "
        f"total_score={total:.2f}"
    )

    return EvaluationReport(
        case_id=case_id or state.task_id,
        job_file=job_file,
        total_score=round(total, 2),
        items=items,
        summary=summary,
        metadata={"evaluator": "lightweight_rules"},
    )
