# LangGraph Workflow and Standard RAG Visibility Design

## Purpose

This spec defines the next architecture step for `career-agent-assistant`: migrate the current fixed Python workflow toward a LangGraph-based workflow, standardize the RAG execution flow, and expose a rule-based retrieval quality report in both CLI and Streamlit demos.

The change follows the project rule of documentation-first execution. This document is a design artifact only; implementation requires a separate task card and implementation plan before code changes.

## Current State

The project already has a working MVP:

- `RAGPipeline` loads Markdown, chunks documents, indexes chunks, and retrieves evidence.
- `JobMatchWorkflow` runs a fixed chain: JD parsing, RAG retrieval, match analysis, output building.
- CLI and Streamlit demos display the final generated result.
- Evaluation checks exist, but retrieval quality is only indirectly visible through evidence count, keyword coverage, and output traceability.
- `documents/03-technical-decisions/02-langgraph-selection.md` previously deferred LangGraph until `AgentTaskState` and agent boundaries became stable. That condition is now met.

## Goals

- Add a LangGraph workflow layer that makes the agent flow explicit and inspectable.
- Keep existing agent classes as reusable node implementations instead of rewriting agent behavior.
- Standardize the RAG flow as `load -> split -> index -> build query -> retrieve -> grade -> report`.
- Add rule-based retrieval grading so the user can see whether RAG retrieved useful evidence.
- Show the RAG effect in both CLI Markdown output and Streamlit UI.
- Add `pyproject.toml` during implementation so dependencies and run commands are standardized.

## Non-Goals

- Do not build a full frontend/backend split.
- Do not replace the whole RAG module with Chroma, FAISS, or a remote vector database in this step.
- Do not require a real LLM or network API to run the default demo.
- Do not add an agentic retry loop in this step, such as `retrieve -> grade -> rewrite query -> retrieve again`.
- Do not delete the existing `JobMatchWorkflow` until the LangGraph workflow is verified and documented.

## Recommended Approach

Use a standardization-first migration:

1. Keep the existing RAG and agent modules as the core business logic.
2. Add a new LangGraph workflow wrapper.
3. Add a retrieval grading module that evaluates the retrieved evidence for each run.
4. Extend state, CLI output, Streamlit output, and evaluation docs to surface the RAG diagnostics.

This keeps the migration focused while satisfying the requirement to follow LangGraph and standard RAG structure.

## LangGraph Workflow Design

Add a new workflow class, tentatively named `LangGraphJobMatchWorkflow`, under `src/career_agent/workflows/`.

The LangGraph nodes should be:

```text
parse_jd
-> build_retrieval_query
-> retrieve_evidence
-> grade_retrieval
-> analyze_match
-> build_output
-> finalize_report
```

Node responsibilities:

- `parse_jd`: use `JDParserAgent.parse` and write `parsed_jd`.
- `build_retrieval_query`: use the existing RAG query construction logic and write `retrieval_query`.
- `retrieve_evidence`: use `RAGRetrieveAgent` or `RAGPipeline` and write `retrieved_evidence`.
- `grade_retrieval`: run rule-based RAG grading and write `retrieval_grade_report`.
- `analyze_match`: use `MatchAnalysisAgent.analyze` and write `match_analysis`.
- `build_output`: use `BuildAgent.build` and write `generated_output`.
- `finalize_report`: set final status and append trace metadata.

The existing `JobMatchWorkflow` should remain available during the first implementation pass. The CLI can switch to LangGraph once tests confirm behavior is equivalent or better.

## Standard RAG Flow

The RAG flow should be explicit and visible:

```text
load documents
-> split chunks
-> index vector store
-> build retrieval query
-> retrieve top_k evidence
-> grade retrieval
-> expose report
```

Existing modules map to the flow as follows:

- `MarkdownProfileLoader`: load Markdown profile documents.
- `TextChunker`: split documents into chunks.
- `VectorStore`: index chunks.
- `SimpleRetriever`: retrieve evidence.
- new grading module: evaluate retrieval quality.
- CLI and Streamlit: expose report.

This step does not require replacing `MemoryVectorStore` or `EmbeddingVectorStore`. The default should remain local and deterministic.

## Retrieval Grading Design

Add retrieval grading data structures, separate from the batch evaluation structures:

```python
RetrievalGradeItem
- name: str
- score: float
- passed: bool
- message: str
- metadata: dict

RetrievalGradeReport
- query: str
- top_k: int
- evidence_count: int
- average_score: float
- keyword_coverage: float
- source_diversity: int
- grade: str  # excellent | good | weak | failed
- items: list[RetrievalGradeItem]
- evidence_summaries: list[dict]
- metadata: dict
```

Initial rule-based checks:

- `evidence_count`: whether retrieval returned enough evidence.
- `average_score`: average score of the returned evidence.
- `keyword_coverage`: how many JD skills and keywords are covered by evidence keywords or evidence content.
- `source_diversity`: whether evidence comes from multiple source files.
- `traceability`: whether evidence has `source_path`, `chunk_id`, and `score`.

Suggested grade thresholds:

- `excellent`: total score >= 0.85 and all critical checks pass.
- `good`: total score >= 0.65 and traceability passes.
- `weak`: total score >= 0.35, but coverage or evidence count is limited.
- `failed`: no evidence, missing traceability, or total score < 0.35.

Thresholds should be constants so tests can verify edge cases.

## State Changes

Extend `AgentTaskState` with:

```python
retrieval_query: str
retrieval_grade_report: RetrievalGradeReport | None
workflow_trace: list[str]
```

The state should remain serializable and easy to inspect. LangGraph nodes should update only their own fields and append short node names to `workflow_trace`.

## CLI Output Design

The CLI Markdown report should add a RAG diagnostics section:

```text
## RAG 检索诊断

Query:
Agent RAG Python LangGraph ...

Overall grade:
good (0.76)

Metrics:
- evidence_count: 5/5
- average_score: 0.68
- keyword_coverage: 0.72
- source_diversity: 3 sources
- traceability: passed

Top Evidence:
1. 项目 A
   score: 0.82
   source: data/samples/profile/project_agent.md
   matched_keywords: RAG, Agent, Python
   snippet: ...
```

The CLI remains the stable default demonstration path.

## Streamlit Output Design

The Streamlit demo should add a "RAG 检索效果" section with:

- overall grade and score;
- retrieval query;
- metrics table;
- expandable top evidence entries;
- source path, score, matched keywords, and snippet for each evidence item.

The UI should use the same `RetrievalGradeReport` produced by workflow state.

## Dependency and Packaging Design

Implementation may add `pyproject.toml` with:

- project metadata;
- package discovery for `src/career_agent`;
- dependency on `langgraph`;
- optional demo dependency for `streamlit`;
- pytest configuration with `pythonpath = ["src"]`, if supported by the chosen configuration.

The target run flow should become:

```bash
pip install -e .
pytest
python demo/cli/run_job_match_demo.py
streamlit run demo/streamlit/app.py
```

Default tests must not require real API keys or network calls.

## Testing Strategy

Implementation should add or update tests for:

- LangGraph workflow initialization and successful run.
- Node order and state updates.
- Retrieval query storage.
- Retrieval grading edge cases: no evidence, weak evidence, good evidence, missing traceability.
- CLI report includes the RAG diagnostics section.
- Streamlit static checks include the RAG diagnostics section.
- Existing workflow tests remain passing during migration.

Full verification command:

```bash
PYTHONPATH=src pytest tests -q
```

After `pyproject.toml` is added, the preferred command should become:

```bash
pytest tests -q
```

## Execution Boundaries

Because this crosses workflow, RAG, evaluation, demo, and packaging, implementation should be split into task cards. Recommended tasks:

1. `WORKFLOW-002`: LangGraph workflow skeleton and state trace.
2. `RAG-006`: retrieval grading schemas and rule-based grader.
3. `DEMO-003`: CLI and Streamlit RAG diagnostics display.
4. `PACKAGING-001`: `pyproject.toml` and run command cleanup.

Each task must declare allowed and prohibited files before execution.

## Risks and Mitigations

- LangGraph dependency may add installation friction. Mitigation: add `pyproject.toml` and keep default tests deterministic.
- RAG grading can look more precise than it is. Mitigation: label it as rule-based diagnostic scoring, not ground-truth evaluation.
- Too much UI output can distract from the demo. Mitigation: CLI uses concise Markdown; Streamlit uses expandable sections.
- Existing workflow behavior may regress. Mitigation: keep `JobMatchWorkflow` until LangGraph workflow passes equivalent tests.

## Acceptance Criteria

The design is implemented only when:

- LangGraph workflow can run the full job matching path.
- Retrieval grading appears in workflow state.
- CLI report shows query, overall grade, metrics, and top evidence details.
- Streamlit shows the same RAG diagnostics.
- Tests pass locally without external API keys.
- Documentation and task planning files are updated after implementation.
