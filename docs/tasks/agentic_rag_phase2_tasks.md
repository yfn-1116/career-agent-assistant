# Phase 2 任务拆分

## 总览

| Task | 名称 | 层 | 依赖 | 预计改动文件 |
|------|------|-----|------|-------------|
| B | Domain Schema Standardization | domain | — | ~6 |
| C | Industrial Hybrid Retrieval | infrastructure | B | ~5 |
| D | Reranker | infrastructure | B | ~4 |
| E | Agentic Retry Workflow | graph | C, D | ~3 |
| F | Tool Calling Agent Layer | application | B, C | ~6 |
| G | Faithfulness / Grounding Checker | application | B | ~4 |
| H | Diagnostics and Evaluation | interface | E, F, G | ~8 |

---

## Task B：Domain Schema Standardization

**目标**：统一核心数据结构，dataclass + 序列化 + 约束校验。

**文件**：
- `src/career_agent/domain/__init__.py` (NEW)
- `src/career_agent/domain/schemas.py` (NEW) — ParsedJD, RetrievalQuery, RetrievedChunk, RetrievalScore, Evidence, GeneratedBullet, ToolCallTrace, WorkflowTrace, AgentDecision, FaithfulnessReport
- `src/career_agent/domain/validation.py` (NEW) — score range check, bool rejection
- `tests/domain/__init__.py` (NEW)
- `tests/domain/test_schemas.py` (NEW)

**约束**：
- 不修改现有 RAG grading API
- 不修改现有 agent 业务逻辑
- domain 层零外部依赖

**测试**：
- score 必须是 [0, 1] finite float
- bool 拒绝为 score
- 序列化/反序列化
- generated content 必须可关联 evidence

**commit**: `feat: standardize agentic rag domain schemas`

---

## Task C：Industrial Hybrid Retrieval

**目标**：keyword + vector 并行检索 + 分数融合。

**文件**：
- `src/career_agent/rag/retrievers/hybrid_retriever.py` (NEW)
- `src/career_agent/rag/retrievers/__init__.py`
- `tests/rag/test_hybrid_retrieval.py` (NEW)

**依赖**：Task B (RetrievedChunk schema)

**约束**：
- keyword retriever 和 embedding retriever 可独立开关
- embedding 不可用时回退到 keyword-only
- 不破坏 MemoryVectorStore / EmbeddingVectorStore

**测试**：
- keyword only 命中
- vector only 命中
- hybrid fusion 后匹配项排名上升
- metadata boost 生效
- score 范围合法 [0, 1]
- 不回退 substring 误匹配

**commit**: `feat: implement industrial hybrid retriever`

---

## Task D：Reranker

**目标**：检索后 lightweight 重排序。

**文件**：
- `src/career_agent/rag/reranker.py` (NEW)
- `tests/rag/test_reranker.py` (NEW)

**依赖**：Task B (RetrievedChunk schema)

**约束**：
- 默认规则实现，不调 LLM
- 接口预留 LLM reranker 扩展点
- 每个 chunk 输出 rerank_score + rerank_reason

**测试**：
- skill overlap 高分项排名上升
- duplicate source 被惩罚
- 太短/太长内容被惩罚
- rerank_reason 非空
- score 范围合法

**commit**: `feat: add lightweight reranker`

---

## Task E：Agentic Retry Workflow

**目标**：LangGraph 条件分叉 + query rewrite retry + fallback。

**文件**：
- `src/career_agent/workflows/langgraph_workflow.py`
- `tests/workflows/test_langgraph_workflow.py`

**依赖**：Task C, Task D

**约束**：
- 不重写所有 node，只加条件边和 rewrite/fallback 逻辑
- 已有 7 个 LangGraph 测试不回归
- retrieval grading API 不变

**测试**：
- low score 触发 retry
- high score 直接进入 analyze
- max retry 后进入 fallback
- fallback 不生成 unsupported bullet
- retry_history 写入

**commit**: `feat: add agentic retry workflow with conditional branching`

---

## Task F：Tool Calling Agent Layer

**目标**：tool interface + registry + planner + trace。

**文件**：
- `src/career_agent/tools/__init__.py` (NEW)
- `src/career_agent/tools/base.py` (NEW) — Tool interface
- `src/career_agent/tools/registry.py` (NEW) — ToolRegistry
- `src/career_agent/tools/planner.py` (NEW) — RulePlanner
- `src/career_agent/tools/trace.py` (NEW) — ToolCallTrace
- `tests/tools/__init__.py` (NEW)
- `tests/tools/test_tool_calling.py` (NEW)

**依赖**：Task B, Task C

**约束**：
- planner 是规则型，但 tool 有标准接口（后续可换 LLM planner）
- 不能调用 registry 外 tool
- 每个 tool call 写入 trace

**测试**：
- registry 包含所有必需 tool
- planner 根据 state 选对 tool
- 未注册 tool 不能调用
- trace 记录完整

**commit**: `feat: add controlled tool calling agent layer`

---

## Task G：Faithfulness / Grounding Checker

**目标**：每条生成内容必须可溯源，防止幻觉。

**文件**：
- `src/career_agent/evaluation/faithfulness.py` (NEW)
- `tests/evaluation/test_faithfulness.py` (NEW)

**依赖**：Task B

**约束**：
- 默认规则实现
- 不修改 BuildAgent 内部逻辑
- faithfulness_score < 0.75 时标记 revise_required
- 不编造经历作为 evidence

**测试**：
- 无 evidence 的 bullet 被拒绝
- 夸大 claim 被标记
- 有 source 的 bullet 通过
- unsupported_claims 输出

**commit**: `feat: add grounded generation checker`

---

## Task H：Diagnostics and Evaluation

**目标**：JSON diagnostics + 增强 Markdown + eval dataset + eval runner。

**文件**：
- `src/career_agent/evaluation/diagnostics.py` (NEW) — JSON writer
- `src/career_agent/evaluation/report_writer.py` (NEW) — 增强 Markdown
- `data/eval/jd_cases.jsonl` (NEW) — 8+ JD eval dataset
- `scripts/run_eval.py` (NEW) — eval runner
- `demo/cli/run_job_match_demo.py` — 调用 diagnostics writer
- `demo/streamlit/app.py` — 展示增强内容
- `tests/evaluation/test_diagnostics.py` (NEW)
- `tests/evaluation/test_eval_runner.py` (NEW)

**依赖**：Task E, Task F, Task G

**验收**：
- diagnostics JSON 创建
- Markdown report 含 hybrid table, retry history, source mapping
- eval runner 可跑 8 个 JD
- Hit@K, MRR, Skill Coverage, Source Precision, Faithfulness Pass Rate 有输出

**commit**: `feat: add rag agent diagnostics and evaluation`

---

## 质量门禁（每个 Task）

```bash
# 1. 核心回归
python -m pytest -q tests/rag/test_retrieval_grading.py

# 2. 本任务新增测试
python -m pytest -q tests/<new_module>/

# 3. 已有 workflow 测试不回归
python -m pytest -q tests/workflows/

# 4. Demo 可运行
python demo/cli/run_job_match_demo.py

# 5. git status 干净（仅本任务文件）
git status --short
```

---

## 实现顺序

```
Task B (domain) ─────────────────────────────┐
                                              │
Task C (hybrid) ───┐                          │
                   ├── Task E (retry) ──┐     │
Task D (reranker) ─┘                    │     │
                                        │     │
                   Task F (tools) ──────┤     │
                                        │     │
                   Task G (faithfulness)┤     │
                                        ├── Task H (diagnostics)
                                        │
                                        │
```

Task B 必须先做（所有后续 task 依赖 schema）。
Task C 和 D 可并行。
Task E 依赖 C+D。
Task F 依赖 B+C。
Task G 依赖 B。
Task H 依赖 E+F+G。
