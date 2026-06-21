# Phase 2 任务拆分（更新版）

## 任务顺序

| Task | 名称 | 层 | 状态 |
|------|------|-----|------|
| B | Domain Schema Standardization | domain | ✅ |
| C | Environment / Configuration / Docker | infrastructure | ⏳ |
| D | LLM Provider Abstraction | infrastructure | ⏳ |
| E | Industrial Hybrid Retrieval | infrastructure | ✅ |
| F | Reranker | infrastructure | ⏳ |
| G | Agentic Retry Workflow | graph | ⏳ |
| H | Grounded Generation / Faithfulness Checker | application | ⏳ |
| I | Unified Agent Run Service | application | ⏳ |
| J | Codex-like Streamlit Agent UI | interface | ⏳ |
| K | Diagnostics / Offline Evaluation | interface | ⏳ |

**依赖关系**：
```
B ──► C ──► D ──► E ──► F ──► G ──► H ──► I ──► J ──► K
                              │                        │
                              └────────────────────────┘
```
C 必须前置（后续所有模块从 settings 读配置）。

---

## Task B：Domain Schema Standardization ✅

已完成。364 测试通过。11 个 dataclass schema + score validation。

---

## Task C：Environment / Configuration / Docker Standardization

**目标**：所有参数集中配置，零硬编码。

### C1. 依赖管理
- `pyproject.toml` 区分 core / dev / demo / optional 依赖
- core: langgraph, pydantic (if needed), python-dotenv, pyyaml
- rag: (current deps)
- ui: streamlit
- dev: pytest

### C2. .env.example
```
APP_ENV=local
LOG_LEVEL=INFO
LLM_PROVIDER=mock
LLM_API_KEY=
LLM_MODEL=
EMBEDDING_PROVIDER=mock
EMBEDDING_MODEL=
EMBEDDING_DIM=1024
VECTOR_STORE_BACKEND=memory
CHUNK_SIZE=800
CHUNK_OVERLAP=100
RETRIEVAL_TOP_K=8
RERANK_TOP_K=5
MIN_RETRIEVAL_SCORE=0.65
MAX_RETRIES=2
HYBRID_VECTOR_WEIGHT=0.40
HYBRID_KEYWORD_WEIGHT=0.35
HYBRID_METADATA_WEIGHT=0.15
HYBRID_PRIORITY_WEIGHT=0.10
OUTPUT_DIR=outputs
RAG_REPORT_DIR=outputs/rag_reports
DIAGNOSTICS_DIR=outputs/diagnostics
STREAMLIT_PORT=8501
```

### C3. Settings 模块
`src/career_agent/core/settings.py`：
- `AppSettings` — env, log_level, output dirs
- `LLMSettings` — provider, api_key, model, timeout, max_retries
- `EmbeddingSettings` — provider, model, dim, batch_size
- `RAGSettings` — chunk_size, chunk_overlap, top_k, rerank_top_k
- `HybridRetrievalSettings` — vector/kw/meta/priority weights, min_retrieval_score
- `OutputSettings` — output_dir, rag_report_dir, diagnostics_dir, trace_dir

校验规则：
- weights 总和 ≈ 1.0（0.99-1.01）
- top_k > 0, chunk_size > 0, max_retries >= 0
- score thresholds ∈ [0, 1]

### C4. Docker
- `Dockerfile` — python:3.12-slim, pip install -e ., streamlit
- `docker-compose.yml` — app service, volumes: data/ + outputs/, env_file: .env, ports: 8501
- `.dockerignore` — .git, __pycache__, .pytest_cache, outputs/

### C5. 接入
- 后续 Task D-K 全部从 settings 读参数
- 业务代码不直接 os.getenv

### 测试
- `tests/core/test_settings.py`
- 默认 settings 加载
- hybrid weights 合法
- 非法 top_k / chunk_size 报错
- bool score 配置拒绝
- output dirs 可从 env 覆盖
- LLM provider 默认 mock

### 验收
```bash
python -m pytest -q tests/core/test_settings.py
cp .env.example .env && docker compose up --build  # 可选验证
```

---

## Task D：LLM Provider Abstraction

**目标**：统一 LLM 接口，支持 Qwen/DeepSeek/Mock，不散落在业务代码里。

### 文件
- `src/career_agent/infrastructure/llm/__init__.py` (NEW)
- `src/career_agent/infrastructure/llm/base.py` (NEW)
- `src/career_agent/infrastructure/llm/qwen_provider.py`
- `src/career_agent/infrastructure/llm/deepseek_provider.py`
- `src/career_agent/infrastructure/llm/mock_provider.py`
- `tests/infrastructure/test_llm_providers.py` (NEW)

### 接口
```python
class LLMProvider(ABC):
    def generate(prompt, system_prompt=None) -> str
    def generate_structured(prompt, schema) -> dict
    @property
    def model_name() -> str
    @property
    def is_available() -> bool
```

### LLM 使用边界
- 允许：结构化解析、query rewrite、匹配分析、生成回答、faithfulness check
- 禁止：编造经历、绕过 evidence、直接执行工具

### Fallback
- LLM 不可用 → 回退规则
- trace 记录 llm_unavailable

### 测试
- MockLLMProvider 可构造
- Qwen/DeepSeek provider 从 settings 读配置
- 无 API key 时 is_available=False
- generate_structured 返回合法 JSON

---

## Task E：Industrial Hybrid Retrieval ✅

已完成。HybridRetriever + normalize_scores + metadata_score。22 tests。

---

## Task F：Reranker

**目标**：检索后 lightweight 重排序。

### 文件
- `src/career_agent/rag/reranker.py` (NEW)
- `tests/rag/test_reranker.py` (NEW)

### 约束
- 默认规则实现
- 输入 list[RetrievedChunk]，输出 re-ranked list[RetrievedChunk]
- 每个 chunk 写入 rerank_score + rerank_reason
- 从 settings 读 rerank_top_k

### 测试
- skill overlap 高分排名上升
- duplicate source 被惩罚
- 太短/太长被惩罚
- rerank_reason 非空
- score 范围合法

---

## Task G：Agentic Retry Workflow

**目标**：LangGraph 条件分叉 + rewrite_query retry + fallback。

### 文件
- `src/career_agent/workflows/langgraph_workflow.py`
- `tests/workflows/test_langgraph_workflow.py`

### 约束
- score >= MIN_RETRIEVAL_SCORE → analyze_match
- score < threshold 且 retry < max → rewrite_query
- retry >= max → fallback
- fallback 不编造经历
- 从 settings 读 min_retrieval_score 和 max_retries

### 测试
- low score 触发 retry
- high score 直接通过
- max retry 后 fallback
- retry_history 写入

---

## Task H：Grounded Generation / Faithfulness Checker

**目标**：每条生成内容可溯源，防止幻觉。

### 文件
- `src/career_agent/evaluation/faithfulness.py` (NEW)
- `tests/evaluation/test_faithfulness.py` (NEW)

### 约束
- GeneratedBullet 必须有 evidence_ids
- 检测夸大 claims
- faithfulness_score < 0.75 → revise_required
- LLM 可用于 faithfulness check（可选）

### 测试
- 无 evidence 的 bullet 被拒绝
- 夸大 claim 被标记
- 正常 bullet 通过
- unsupported_claims 输出

---

## Task I：Unified Agent Run Service

**目标**：UI 不拼流程，统一入口调用 LangGraph。

### 文件
- `src/career_agent/service/__init__.py` (NEW)
- `src/career_agent/service/agent_run.py` (NEW)
- `tests/service/test_agent_run.py` (NEW)

### 接口
```
AgentRunService.run(AgentRunRequest) → AgentRunResult
```

### 约束
- UI 不直接调 RAG/Agent 细节
- Service 内部调 LangGraph workflow
- 支持 mode: analyze / resume / chat

---

## Task J：Codex-like Streamlit Agent UI

**目标**：极简对话式 Agent 界面。

### 文件
- `demo/streamlit/app.py`（重写为 Agent 对话界面）

### 布局
- 输入框 + Ask Agent 按钮
- Agent 回答区域（最终结论）
- 展开详情（技术细节折叠）
- 执行步骤简洁展示

### 约束
- 不引入复杂前端框架
- 不做 dashboard
- 默认不展示技术细节
- 调用 AgentRunService

---

## Task K：Diagnostics / Offline Evaluation

**目标**：完整 diagnostics JSON + eval dataset + eval runner。

### 文件
- `src/career_agent/evaluation/diagnostics.py` (NEW)
- `data/eval/jd_cases.jsonl` (NEW)
- `scripts/run_eval.py` (NEW)
- `tests/evaluation/test_diagnostics.py` (NEW)
- `tests/evaluation/test_eval_runner.py` (NEW)

### 验收
- diagnostics JSON 含完整 trace
- Markdown report 含 hybrid table + retry history + source mapping
- eval runner 可跑 8+ JD
- Hit@K, MRR, Skill Coverage, Source Precision, Faithfulness Pass Rate 输出

---

## 质量门禁（每个 Task）

```bash
python -m pytest -q tests/rag/test_retrieval_grading.py  # 核心回归
python -m pytest -q tests/<new>/                          # 新增测试
python -m pytest -q tests/workflows/                     # workflow 不回归
python demo/cli/run_job_match_demo.py                    # demo 可运行
git status --short                                         # 干净
```
