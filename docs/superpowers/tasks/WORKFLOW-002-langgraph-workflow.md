# WORKFLOW-002 LangGraph Workflow 集成

## 任务编号

WORKFLOW-002

## 建议执行者

Claude Code (接管自 Codex)

## 任务目标

将现有 `JobMatchWorkflow`（普通 Python 顺序调用）迁移为 LangGraph `StateGraph`，但**不重写所有业务逻辑**，不扩大范围到完整 Agentic RAG retry loop。

## 范围

### 1. LangGraph State
定义 `JobMatchState` (TypedDict)，至少包含：
- `raw_jd` — 原始 JD 文本
- `parsed_jd` — 解析后的 ParsedJD
- `queries` — query rewrite 生成的检索查询列表
- `retrieved_chunks` — 检索到的证据 (RetrievedEvidence)
- `retrieval_scores` — 检索评分报告 (RetrievalGradeReport | None)
- `missing_keywords` — 未覆盖的关键词
- `decision` — 下一步决策 (continue/retry/stop)
- `match_analysis` — 匹配分析结果 (MatchAnalysisResult | None)
- `generated_result` — 生成输出 (GeneratedOutput | None)
- `report_path` — 输出报告路径
- `trace_id` — 追踪 ID
- `logs` — 节点执行日志
- `retry_count` — 重试计数
- `next_action` — 下一个 action

### 2. LangGraph Nodes
将现有流程拆成明确节点，优先复用现有 agent/service 逻辑：
- `parse_jd_node` → 复用 `JDParserAgent`
- `rewrite_query_node` → 复用 `RAGRetrieveAgent.build_query_from_parsed_jd`
- `retrieve_context_node` → 复用 `RAGPipeline.retrieve`
- `grade_retrieval_node` → 复用 `rag.grading.grade_retrieval`
- `analyze_match_node` → 复用 `MatchAnalysisAgent`
- `build_output_node` → 复用 `BuildAgent`
- `write_report_node` → 写 Markdown 报告

### 3. Edges
本次只实现线性主流程：
```
parse_jd → rewrite_query → retrieve_context → grade_retrieval
→ analyze_match → build_output → write_report → END
```
预留条件边函数，但本次不实现复杂循环。

### 4. Demo
更新 `demo/cli/run_job_match_demo.py`，增加 `--use-langgraph` 选项。

运行后必须能看到：parsed JD, rewritten queries, retrieved chunks, retrieval scores, final decision, report path。

### 5. Tests
- `test_langgraph_workflow_runs` — 基本运行
- `test_state_contains_retrieval_scores` — 检索评分进入 state
- `test_workflow_writes_report` — 写报告
- `test_low_score_decision_is_preserved_in_state` — 低分决策保留

## 允许修改文件

- `src/career_agent/workflows/__init__.py`
- `src/career_agent/workflows/langgraph_workflow.py` (NEW)
- `src/career_agent/workflows/job_match_workflow.py` (保留不删)
- `demo/cli/run_job_match_demo.py`
- `tests/workflows/test_langgraph_workflow.py` (NEW)
- `tests/workflows/test_job_match_workflow.py` (不修改已有测试)
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/career_agent/rag/` — 不修改 RAG 底层逻辑
- `src/career_agent/agents/` — 不修改 Agent 内部实现
- `src/career_agent/rag/grading.py` — 不破坏 Task 1 API
- `tests/rag/test_retrieval_grading.py` — 不破坏已有测试

## 约束

- 不引入新依赖（langgraph 已在 pyproject.toml）
- 不做自动投递、不接平台爬虫
- 不做完整 Agentic RAG retry loop
- 不破坏已完成的 Task 1 retrieval grading API
- 不把 workflow、rag、evaluation 混成一个大文件

## 测试命令

```bash
python -m pytest -q tests/rag/test_retrieval_grading.py
python -m pytest -q tests/workflows/
python demo/cli/run_job_match_demo.py --use-langgraph
```

## 验收标准

- LangGraph workflow 能跑通完整链路
- State 中包含 retrieval_scores
- 15 个 retrieval grading 测试全部通过
- 已有 JobMatchWorkflow 测试不回归
- Demo 显示 parsed JD, rewritten queries, retrieved chunks, retrieval scores, decision, report path

## commit message

```text
feat: migrate job match workflow to LangGraph StateGraph
```
