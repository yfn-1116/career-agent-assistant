# LangGraph RAG Standardization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use $superpower-subagents (recommended) or $superpower-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking via update_plan.

**Goal:** Build a LangGraph-based job match workflow and expose standard RAG retrieval diagnostics in CLI and Streamlit.

**Architecture:** Keep the existing agents and RAG pipeline as reusable business logic. Add a retrieval grading module, extend workflow state, introduce `LangGraphJobMatchWorkflow`, then display the same grading report in CLI and Streamlit.

**Tech Stack:** Python dataclasses, existing `src/career_agent` modules, `langgraph.graph.StateGraph`, pytest, Streamlit optional demo.

---

## File Structure

- Create `src/career_agent/rag/grading.py`: retrieval grading schemas and deterministic scoring.
- Modify `src/career_agent/rag/__init__.py`: export grading types if consistent with existing exports.
- Modify `src/career_agent/agents/state.py`: add `retrieval_query`, `retrieval_grade_report`, and `workflow_trace`.
- Create `src/career_agent/workflows/langgraph_job_match_workflow.py`: LangGraph workflow wrapper.
- Modify `src/career_agent/workflows/__init__.py`: export the new workflow.
- Modify `demo/cli/run_job_match_demo.py`: use LangGraph workflow and render RAG diagnostics.
- Modify `demo/streamlit/app.py`: use LangGraph workflow and render RAG diagnostics.
- Create `pyproject.toml`: project metadata, `langgraph` dependency, optional Streamlit dependency, pytest pythonpath.
- Add tests under `tests/rag/`, `tests/workflows/`, and `tests/demo/`.
- Update docs: RAG design, LangGraph decision, evaluation docs, demo docs, runbooks, journal, planning.

Recommended execution order: Task 1, Task 4, Task 2, Task 3, Task 5. Task 4 installs `langgraph`, so it should happen before running the LangGraph workflow tests in Task 2.

## Task 1: Retrieval Grading

**Files:**
- Create: `src/career_agent/rag/grading.py`
- Modify: `src/career_agent/rag/__init__.py`
- Modify: `src/career_agent/agents/state.py`
- Test: `tests/rag/test_retrieval_grading.py`

- [ ] **Step 1: Write failing tests for grading data structures and failed retrieval**

Create `tests/rag/test_retrieval_grading.py` with:

```python
from career_agent.agents.state import ParsedJD
from career_agent.rag.grading import (
    RetrievalGradeReport,
    grade_retrieval,
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
```

- [ ] **Step 2: Run the failing test**

Run: `PYTHONPATH=src pytest tests/rag/test_retrieval_grading.py::test_no_evidence_returns_failed_report -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'career_agent.rag.grading'`.

- [ ] **Step 3: Implement grading schemas and no-evidence behavior**

Create `src/career_agent/rag/grading.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from career_agent.agents.state import ParsedJD
from career_agent.rag.schemas import RetrievedEvidence


GRADE_EXCELLENT = "excellent"
GRADE_GOOD = "good"
GRADE_WEAK = "weak"
GRADE_FAILED = "failed"


@dataclass
class RetrievalGradeItem:
    name: str
    score: float
    passed: bool
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalGradeReport:
    query: str
    top_k: int
    evidence_count: int
    average_score: float
    keyword_coverage: float
    source_diversity: int
    grade: str
    items: list[RetrievalGradeItem] = field(default_factory=list)
    evidence_summaries: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def grade_retrieval(
    query: str,
    parsed_jd: ParsedJD | None,
    evidence: list[RetrievedEvidence],
    top_k: int,
) -> RetrievalGradeReport:
    evidence_count = len(evidence)
    average_score = _average_score(evidence)
    keyword_coverage = _keyword_coverage(parsed_jd, evidence)
    source_diversity = len({ev.source_path for ev in evidence if ev.source_path})
    traceable = all(ev.source_path and ev.chunk_id for ev in evidence)

    items = [
        RetrievalGradeItem(
            name="evidence_count",
            score=1.0 if evidence_count > 0 else 0.0,
            passed=evidence_count > 0,
            message=(
                f"Retrieved {evidence_count} evidence items."
                if evidence_count > 0
                else "No evidence retrieved."
            ),
            metadata={"count": evidence_count, "top_k": top_k},
        ),
        RetrievalGradeItem(
            name="average_score",
            score=average_score,
            passed=average_score >= 0.35,
            message=f"Average evidence score is {average_score:.2f}.",
        ),
        RetrievalGradeItem(
            name="keyword_coverage",
            score=keyword_coverage,
            passed=keyword_coverage >= 0.5,
            message=f"Keyword coverage is {keyword_coverage:.2f}.",
        ),
        RetrievalGradeItem(
            name="source_diversity",
            score=min(source_diversity / 3, 1.0),
            passed=source_diversity >= 1,
            message=f"Evidence comes from {source_diversity} source(s).",
            metadata={"source_count": source_diversity},
        ),
        RetrievalGradeItem(
            name="traceability",
            score=1.0 if traceable and evidence_count > 0 else 0.0,
            passed=traceable and evidence_count > 0,
            message=(
                "All evidence has source_path and chunk_id."
                if traceable and evidence_count > 0
                else "Some evidence is missing source_path or chunk_id."
            ),
        ),
    ]

    total_score = sum(item.score for item in items) / len(items)
    grade = _grade_from_score(total_score, evidence_count, traceable)

    return RetrievalGradeReport(
        query=query,
        top_k=top_k,
        evidence_count=evidence_count,
        average_score=average_score,
        keyword_coverage=keyword_coverage,
        source_diversity=source_diversity,
        grade=grade,
        items=items,
        evidence_summaries=[_summarize_evidence(ev) for ev in evidence],
        metadata={"total_score": round(total_score, 4)},
    )
```

- [ ] **Step 4: Add helper functions**

Append to `src/career_agent/rag/grading.py`:

```python
def _average_score(evidence: list[RetrievedEvidence]) -> float:
    if not evidence:
        return 0.0
    return round(sum(ev.score for ev in evidence) / len(evidence), 4)


def _keyword_coverage(
    parsed_jd: ParsedJD | None,
    evidence: list[RetrievedEvidence],
) -> float:
    if parsed_jd is None:
        return 0.0

    expected = set(parsed_jd.hard_skills + parsed_jd.bonus_skills + parsed_jd.keywords)
    expected = {kw.lower() for kw in expected if kw}
    if not expected:
        return 0.0

    evidence_text = " ".join(
        [" ".join(ev.matched_keywords) + " " + ev.content for ev in evidence]
    ).lower()
    matched = {kw for kw in expected if kw.lower() in evidence_text}
    return round(len(matched) / len(expected), 4)


def _grade_from_score(total_score: float, evidence_count: int, traceable: bool) -> str:
    if evidence_count == 0 or not traceable or total_score < 0.35:
        return GRADE_FAILED
    if total_score >= 0.85:
        return GRADE_EXCELLENT
    if total_score >= 0.65:
        return GRADE_GOOD
    return GRADE_WEAK


def _summarize_evidence(ev: RetrievedEvidence) -> dict[str, Any]:
    return {
        "evidence_id": ev.evidence_id,
        "chunk_id": ev.chunk_id,
        "title": ev.title,
        "score": ev.score,
        "source_path": ev.source_path,
        "matched_keywords": list(ev.matched_keywords),
        "snippet": ev.content[:240].replace("\n", " "),
    }
```

- [ ] **Step 5: Export grading types**

Update `src/career_agent/rag/__init__.py`:

```python
"""RAG package for profile loading, chunking, retrieval, and grading."""
```

Do not add broad imports if the package currently avoids them.

- [ ] **Step 6: Extend workflow state**

Update `src/career_agent/agents/state.py`:

```python
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from career_agent.rag.grading import RetrievalGradeReport
```

Add fields to `AgentTaskState` after `retrieved_evidence`:

```python
    retrieval_query: str = ""
    retrieval_grade_report: RetrievalGradeReport | None = None
    workflow_trace: list[str] = field(default_factory=list)
```

Keep the `RetrievalGradeReport` import under `TYPE_CHECKING` to avoid a runtime circular import: `rag.grading` imports `ParsedJD` from this file.

- [ ] **Step 7: Add complete grading tests**

Extend `tests/rag/test_retrieval_grading.py`:

```python
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
```

- [ ] **Step 8: Run RAG grading tests**

Run: `PYTHONPATH=src pytest tests/rag/test_retrieval_grading.py -v`

Expected: PASS.

- [ ] **Step 9: Commit Task 1**

```bash
git add src/career_agent/rag/grading.py src/career_agent/rag/__init__.py src/career_agent/agents/state.py tests/rag/test_retrieval_grading.py
git commit -m "feat: add retrieval grading report"
```

## Task 2: LangGraph Workflow

**Files:**
- Create: `src/career_agent/workflows/langgraph_job_match_workflow.py`
- Modify: `src/career_agent/workflows/__init__.py`
- Test: `tests/workflows/test_langgraph_job_match_workflow.py`

- [ ] **Step 1: Write failing workflow tests**

Create `tests/workflows/test_langgraph_job_match_workflow.py`:

```python
from pathlib import Path

from career_agent.agents.state import AgentTaskState
from career_agent.workflows.langgraph_job_match_workflow import (
    LangGraphJobMatchWorkflow,
)


def _read_sample_jd(name: str) -> str:
    return Path("data/samples/jobs", name).read_text(encoding="utf-8")


def test_langgraph_workflow_runs_full_chain():
    wf = LangGraphJobMatchWorkflow(profile_dir="data/samples/profile")
    state = wf.run(_read_sample_jd("agent_intern_jd.md"), top_k=5)

    assert isinstance(state, AgentTaskState)
    assert state.status == "completed"
    assert state.parsed_jd is not None
    assert state.retrieval_query
    assert state.retrieved_evidence
    assert state.retrieval_grade_report is not None
    assert state.match_analysis is not None
    assert state.generated_output is not None


def test_langgraph_workflow_trace_contains_nodes_in_order():
    wf = LangGraphJobMatchWorkflow(profile_dir="data/samples/profile")
    state = wf.run(_read_sample_jd("rag_engineer_intern_jd.md"), top_k=3)

    assert state.workflow_trace == [
        "parse_jd",
        "build_retrieval_query",
        "retrieve_evidence",
        "grade_retrieval",
        "analyze_match",
        "build_output",
        "finalize_report",
    ]
```

- [ ] **Step 2: Run the failing workflow test**

Run: `PYTHONPATH=src pytest tests/workflows/test_langgraph_job_match_workflow.py -v`

Expected: FAIL with missing `langgraph_job_match_workflow` or missing `langgraph`.

- [ ] **Step 3: Implement LangGraph workflow imports and class shell**

Create `src/career_agent/workflows/langgraph_job_match_workflow.py`:

```python
"""LangGraph-based job matching workflow."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from career_agent.agents.build_agent import BuildAgent
from career_agent.agents.jd_parser import JDParserAgent
from career_agent.agents.match_analysis_agent import MatchAnalysisAgent
from career_agent.agents.rag_retrieve_agent import RAGRetrieveAgent
from career_agent.agents.state import AgentTaskState
from career_agent.rag.grading import grade_retrieval
from career_agent.rag.pipeline import RAGPipeline


class _GraphState(TypedDict, total=False):
    state: AgentTaskState
    top_k: int


class LangGraphJobMatchWorkflow:
    """Execute the job-match workflow as an explicit LangGraph state graph."""

    def __init__(
        self,
        profile_dir: str | Path | None = None,
        rag_pipeline: RAGPipeline | None = None,
        jd_parser: JDParserAgent | None = None,
        rag_retrieve_agent: RAGRetrieveAgent | None = None,
        match_analysis_agent: MatchAnalysisAgent | None = None,
        build_agent: BuildAgent | None = None,
    ) -> None:
        self.rag_pipeline = rag_pipeline or RAGPipeline()
        self.jd_parser = jd_parser or JDParserAgent()
        self.rag_retrieve_agent = rag_retrieve_agent or RAGRetrieveAgent(
            pipeline=self.rag_pipeline
        )
        self.match_analysis_agent = match_analysis_agent or MatchAnalysisAgent()
        self.build_agent = build_agent or BuildAgent()

        if profile_dir is not None:
            self.rag_pipeline.build_index(profile_dir)

        self.graph = self._build_graph()
```

- [ ] **Step 4: Implement graph construction**

Append:

```python
    def _build_graph(self):
        builder = StateGraph(_GraphState)
        builder.add_node("parse_jd", self._parse_jd)
        builder.add_node("build_retrieval_query", self._build_retrieval_query)
        builder.add_node("retrieve_evidence", self._retrieve_evidence)
        builder.add_node("grade_retrieval", self._grade_retrieval)
        builder.add_node("analyze_match", self._analyze_match)
        builder.add_node("build_output", self._build_output)
        builder.add_node("finalize_report", self._finalize_report)

        builder.add_edge(START, "parse_jd")
        builder.add_edge("parse_jd", "build_retrieval_query")
        builder.add_edge("build_retrieval_query", "retrieve_evidence")
        builder.add_edge("retrieve_evidence", "grade_retrieval")
        builder.add_edge("grade_retrieval", "analyze_match")
        builder.add_edge("analyze_match", "build_output")
        builder.add_edge("build_output", "finalize_report")
        builder.add_edge("finalize_report", END)
        return builder.compile()

    def run(self, job_description: str, top_k: int = 5) -> AgentTaskState:
        state = AgentTaskState(job_description=job_description)
        try:
            result = self.graph.invoke({"state": state, "top_k": top_k})
            return result["state"]
        except Exception as exc:
            state.status = "failed"
            state.error_message = str(exc)
            state.updated_at = datetime.now(timezone.utc).isoformat()
            return state
```

- [ ] **Step 5: Implement graph nodes**

Append:

```python
    @staticmethod
    def _mark(state: AgentTaskState, node_name: str) -> None:
        state.workflow_trace.append(node_name)

    def _parse_jd(self, graph_state: _GraphState) -> _GraphState:
        state = graph_state["state"]
        state.parsed_jd = self.jd_parser.parse(state.job_description)
        self._mark(state, "parse_jd")
        return {"state": state}

    def _build_retrieval_query(self, graph_state: _GraphState) -> _GraphState:
        state = graph_state["state"]
        if state.parsed_jd is None:
            state.retrieval_query = ""
        else:
            state.retrieval_query = (
                self.rag_retrieve_agent.build_query_from_parsed_jd(state.parsed_jd)
            )
        self._mark(state, "build_retrieval_query")
        return {"state": state}

    def _retrieve_evidence(self, graph_state: _GraphState) -> _GraphState:
        state = graph_state["state"]
        top_k = graph_state.get("top_k", 5)
        state.retrieved_evidence = self.rag_retrieve_agent.retrieve_by_query(
            state.retrieval_query,
            top_k=top_k,
        )
        self._mark(state, "retrieve_evidence")
        return {"state": state}

    def _grade_retrieval(self, graph_state: _GraphState) -> _GraphState:
        state = graph_state["state"]
        top_k = graph_state.get("top_k", 5)
        state.retrieval_grade_report = grade_retrieval(
            query=state.retrieval_query,
            parsed_jd=state.parsed_jd,
            evidence=state.retrieved_evidence,
            top_k=top_k,
        )
        self._mark(state, "grade_retrieval")
        return {"state": state}

    def _analyze_match(self, graph_state: _GraphState) -> _GraphState:
        state = graph_state["state"]
        if state.parsed_jd is not None:
            state.match_analysis = self.match_analysis_agent.analyze(
                parsed_jd=state.parsed_jd,
                evidence=state.retrieved_evidence,
            )
        self._mark(state, "analyze_match")
        return {"state": state}

    def _build_output(self, graph_state: _GraphState) -> _GraphState:
        state = graph_state["state"]
        if state.parsed_jd is not None and state.match_analysis is not None:
            state.generated_output = self.build_agent.build(
                parsed_jd=state.parsed_jd,
                evidence=state.retrieved_evidence,
                match_analysis=state.match_analysis,
            )
        self._mark(state, "build_output")
        return {"state": state}

    def _finalize_report(self, graph_state: _GraphState) -> _GraphState:
        state = graph_state["state"]
        state.status = "completed"
        state.updated_at = datetime.now(timezone.utc).isoformat()
        state.metadata["workflow"] = "langgraph"
        self._mark(state, "finalize_report")
        return {"state": state}
```

- [ ] **Step 6: Export workflow**

Update `src/career_agent/workflows/__init__.py`:

```python
"""Workflow entry points."""
```

Do not add eager imports if current package style avoids them.

- [ ] **Step 7: Run workflow tests**

Run: `PYTHONPATH=src pytest tests/workflows/test_langgraph_job_match_workflow.py -v`

Expected: PASS after `langgraph` is installed or declared by Task 4. If `langgraph` is not installed yet, pause and execute Task 4 before rerunning.

- [ ] **Step 8: Run old workflow tests**

Run: `PYTHONPATH=src pytest tests/workflows/test_job_match_workflow.py -v`

Expected: PASS.

- [ ] **Step 9: Commit Task 2**

```bash
git add src/career_agent/workflows/langgraph_job_match_workflow.py src/career_agent/workflows/__init__.py tests/workflows/test_langgraph_job_match_workflow.py
git commit -m "feat: add langgraph job match workflow"
```

## Task 3: Demo RAG Diagnostics

**Files:**
- Modify: `demo/cli/run_job_match_demo.py`
- Modify: `demo/streamlit/app.py`
- Test: `tests/demo/test_cli_demo_smoke.py`
- Test: `tests/demo/test_streamlit_app_static.py`

- [ ] **Step 1: Add failing CLI smoke assertion**

In `tests/demo/test_cli_demo_smoke.py`, add or update a test to assert:

```python
assert "RAG 检索诊断" in content
assert "Overall grade" in content
assert "retrieval query" in content.lower() or "Query" in content
```

- [ ] **Step 2: Add failing Streamlit static assertion**

In `tests/demo/test_streamlit_app_static.py`, add:

```python
def test_streamlit_app_contains_rag_diagnostics_section():
    content = Path("demo/streamlit/app.py").read_text(encoding="utf-8")
    assert "RAG 检索效果" in content
    assert "retrieval_grade_report" in content
```

- [ ] **Step 3: Run failing demo tests**

Run: `PYTHONPATH=src pytest tests/demo/test_cli_demo_smoke.py tests/demo/test_streamlit_app_static.py -v`

Expected: FAIL because reports do not render retrieval grading yet.

- [ ] **Step 4: Switch CLI to LangGraph workflow**

In `demo/cli/run_job_match_demo.py`, replace:

```python
from career_agent.workflows.job_match_workflow import JobMatchWorkflow
```

with:

```python
from career_agent.workflows.langgraph_job_match_workflow import (
    LangGraphJobMatchWorkflow,
)
```

Replace:

```python
wf = JobMatchWorkflow(
```

with:

```python
wf = LangGraphJobMatchWorkflow(
```

- [ ] **Step 5: Add CLI RAG diagnostics renderer**

Add this function near `_render_usage_section`:

```python
def _render_rag_diagnostics_section(state: "AgentTaskState") -> str:
    report = getattr(state, "retrieval_grade_report", None)
    lines: list[str] = []
    L = lines.append

    L("## 4. RAG 检索诊断")
    L("")
    if report is None:
        L("（当前 workflow 未返回检索诊断报告。）")
        L("")
        return "\n".join(lines)

    L(f"Query: `{report.query or '（空）'}`")
    L("")
    L(f"Overall grade: **{report.grade}** ({report.metadata.get('total_score', 0):.2f})")
    L("")
    L("Metrics:")
    for item in report.items:
        status = "passed" if item.passed else "failed"
        L(f"- {item.name}: {item.score:.2f} ({status}) - {item.message}")
    L("")
    L("Top Evidence:")
    for i, ev in enumerate(report.evidence_summaries, 1):
        L(f"{i}. {ev.get('title') or ev.get('evidence_id')}")
        L(f"   - score: {ev.get('score', 0):.2f}")
        L(f"   - source: `{ev.get('source_path', '')}`")
        L(f"   - matched_keywords: {', '.join(ev.get('matched_keywords', []))}")
        L(f"   - snippet: {ev.get('snippet', '')}")
    L("")
    L("> 注：该评分是规则型检索诊断，不是人工标注或 LLM Judge。")
    L("")
    return "\n".join(lines)
```

- [ ] **Step 6: Insert CLI diagnostics section**

In `render_report`, insert `_render_rag_diagnostics_section(state)` after the existing RAG evidence section and renumber later headings if desired. Minimum acceptable change:

```python
    L(_render_rag_diagnostics_section(state))
```

- [ ] **Step 7: Switch Streamlit to LangGraph workflow and render diagnostics**

In `demo/streamlit/app.py`, replace workflow import and construction with `LangGraphJobMatchWorkflow`.

Add after the evidence section:

```python
st.markdown("## RAG 检索效果")
report = state.retrieval_grade_report
if report is None:
    st.info("当前 workflow 未返回检索诊断报告。")
else:
    st.metric("Overall grade", report.grade, report.metadata.get("total_score", 0))
    st.markdown(f"**Retrieval query**：`{report.query or '（空）'}`")
    st.table(
        [
            {
                "metric": item.name,
                "score": item.score,
                "passed": item.passed,
                "message": item.message,
            }
            for item in report.items
        ]
    )
    st.caption("该评分是规则型检索诊断，不是人工标注或 LLM Judge。")
    for i, ev in enumerate(report.evidence_summaries, 1):
        with st.expander(f"Top evidence {i}: {ev.get('title') or ev.get('evidence_id')}"):
            st.markdown(f"**score**：{ev.get('score', 0):.2f}")
            st.markdown(f"**source**：`{ev.get('source_path', '')}`")
            st.markdown(
                f"**matched_keywords**：{', '.join(ev.get('matched_keywords', []))}"
            )
            st.text(ev.get("snippet", ""))
```

- [ ] **Step 8: Run demo tests and CLI**

Run:

```bash
PYTHONPATH=src pytest tests/demo/test_cli_demo_smoke.py tests/demo/test_streamlit_app_static.py -v
PYTHONPATH=src python demo/cli/run_job_match_demo.py
```

Expected: PASS and CLI output includes `RAG 检索诊断`.

- [ ] **Step 9: Commit Task 3**

```bash
git add demo/cli/run_job_match_demo.py demo/streamlit/app.py tests/demo/test_cli_demo_smoke.py tests/demo/test_streamlit_app_static.py outputs/demo/job_match_result.md
git commit -m "feat: show rag retrieval diagnostics in demos"
```

Only add `outputs/demo/job_match_result.md` if the project wants checked-in demo output refreshed.

## Task 4: Packaging

**Files:**
- Create: `pyproject.toml`
- Modify: `README.md`
- Modify: `documents/98-runbook/01-local-development.md`

- [ ] **Step 1: Write pyproject**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "career-agent-assistant"
version = "0.1.0"
description = "RAG and LangGraph based career agent assistant MVP."
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
  "langgraph>=1.0,<2.0",
]

[project.optional-dependencies]
demo = [
  "streamlit>=1.30",
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

- [ ] **Step 2: Install editable package**

Run: `python -m pip install -e .`

Expected: package installs and `langgraph` is available. If network access fails in the sandbox, rerun with approval.

- [ ] **Step 3: Verify pytest no longer needs PYTHONPATH**

Run: `pytest tests -q`

Expected: PASS.

- [ ] **Step 4: Update README commands**

In `README.md`, replace commands that require `PYTHONPATH=src` with:

```bash
python -m pip install -e .
pytest tests -q
python demo/cli/run_job_match_demo.py
python -m pip install -e ".[demo]"
streamlit run demo/streamlit/app.py
```

- [ ] **Step 5: Update local development runbook**

In `documents/98-runbook/01-local-development.md`, add the same install and run commands. Keep any server-specific instructions unchanged.

- [ ] **Step 6: Commit Task 4**

```bash
git add pyproject.toml README.md documents/98-runbook/01-local-development.md
git commit -m "chore: add pyproject for langgraph workflow"
```

## Task 5: Documentation and Final Verification

**Files:**
- Modify: `documents/02-design/02-rag-module-design.md`
- Modify: `documents/02-design/05-data-flow-design.md`
- Modify: `documents/03-technical-decisions/02-langgraph-selection.md`
- Modify: `documents/05-evaluation/01-rag-evaluation.md`
- Modify: `documents/06-demo/01-demo-script.md`
- Modify: `documents/97-journal.md`
- Modify: `documents/99-project-planning.md`

- [ ] **Step 1: Update RAG design doc**

Add a short section to `documents/02-design/02-rag-module-design.md`:

```markdown
## RAG 检索诊断

当前标准流程为：load -> split -> index -> build query -> retrieve -> grade -> report。
`RetrievalGradeReport` 是单次 workflow 的规则型诊断报告，用于解释检索效果。
它不同于批量 evaluation runner，不代表人工标注准确率。
```

- [ ] **Step 2: Update LangGraph decision doc**

Update `documents/03-technical-decisions/02-langgraph-selection.md` to record that the migration condition is met and `WORKFLOW-002` introduces LangGraph.

- [ ] **Step 3: Update evaluation doc**

In `documents/05-evaluation/01-rag-evaluation.md`, add:

```markdown
## 单次运行诊断 vs 批量评估

`RetrievalGradeReport` 用于单次 workflow 可视化，展示 query、score、关键词覆盖和证据来源。
`EvaluationReport` 用于多 JD 批量评估，检查 workflow 输出是否稳定。
两者互补，不互相替代。
```

- [ ] **Step 4: Update planning board**

In `documents/99-project-planning.md`, add:

```markdown
| WORKFLOW | WORKFLOW-002 | LangGraph workflow 集成 | Codex | DONE | 新增 LangGraph 状态图 |
| RAG | RAG-006 | 检索评分与诊断报告 | Codex | DONE | RetrievalGradeReport |
| DEMO | DEMO-003 | RAG 检索诊断展示 | Claude Code + DeepSeek | DONE | CLI + Streamlit |
| PACKAGING | PACKAGING-001 | pyproject 与依赖规范化 | Codex | DONE | langgraph dependency |
```

- [ ] **Step 5: Update journal**

Add an entry to `documents/97-journal.md`:

```markdown
### WORKFLOW-002 / RAG-006 / DEMO-003 / PACKAGING-001 LangGraph 与 RAG 诊断

- Executor: Codex
- Type: architecture / implementation / demo
- Summary:
  - 新增 LangGraph workflow。
  - 新增规则型 RetrievalGradeReport。
  - CLI 和 Streamlit 展示 RAG 检索效果。
  - 新增 pyproject.toml 规范依赖和运行方式。
- Validation:
  - pytest tests -q
  - python demo/cli/run_job_match_demo.py
```

- [ ] **Step 6: Run full verification**

Run:

```bash
pytest tests -q
python demo/cli/run_job_match_demo.py
git status --short
```

Expected: all tests pass; git status only shows intended files.

- [ ] **Step 7: Commit docs and final verification**

```bash
git add documents/02-design/02-rag-module-design.md documents/02-design/05-data-flow-design.md documents/03-technical-decisions/02-langgraph-selection.md documents/05-evaluation/01-rag-evaluation.md documents/06-demo/01-demo-script.md documents/97-journal.md documents/99-project-planning.md
git commit -m "docs: update langgraph rag diagnostics documentation"
```

## Verification

Final required commands:

```bash
python -m pip install -e .
pytest tests -q
python demo/cli/run_job_match_demo.py
```

Expected final evidence:

- All tests pass.
- CLI report includes `RAG 检索诊断`.
- Streamlit source includes `RAG 检索效果`.
- `AgentTaskState` includes `retrieval_query`, `retrieval_grade_report`, and `workflow_trace`.
- LangGraph workflow state metadata includes `workflow=langgraph`.

## Next Skill

Use `$superpower-subagents` for subagent-driven implementation, or `$superpower-executing-plans` for inline execution in this session.
