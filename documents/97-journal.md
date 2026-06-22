# 项目日志

## 2026-06-22

### STREAMLIT-001 Streamlit demo 薄 UI 拆分

- Executor: Codex
- Type: refactor / test
- Summary:
  - 新增 `KnowledgeBaseService`，负责 runtime 上传文件保存、文本 chunking、知识库 JSONL 持久化、知识库检索和 GitHub README/公开仓库导入。
  - 新增 `ApplicationService`，封装 `ApplicationRepository`，从 `AgentRunResult` 保存投递记录到 ignored runtime 路径。
  - 重写 `demo/streamlit/app.py` 为薄 UI：页面布局、按钮、聊天展示保留在 Streamlit；上传、GitHub 导入、投递记录保存、JD 分析分别委托给 service/repository/AgentRunService。
  - 移除 Streamlit 中对 `data/uploads`、`data/applications`、`data/knowledge_base` 的直接写入，也移除 UI 层直接网络读取 GitHub 的逻辑。
  - 补充 runtime service 测试和 Streamlit 静态边界测试。
- Changed files:
  - `src/career_agent/service/knowledge_base.py`
  - `src/career_agent/service/application_service.py`
  - `demo/streamlit/app.py`
  - `tests/service/test_runtime_services.py`
  - `tests/demo/test_streamlit_app_static.py`
  - `documents/97-journal.md`
  - `documents/99-project-planning.md`
- Validation:
  - `python -m pytest tests/service/test_runtime_services.py -q` — 3 passed
  - `python -m pytest tests/demo/test_streamlit_app_static.py -q` — 12 passed
- Next:
  - Continue with `AgentRunService` entrypoint consolidation for API / UI / Browser demo paths.

### DATA-001 / DOC-SYNC-002 运行数据边界与 Phase 2 文档同步

- Executor: Codex
- Type: chore / docs
- Summary:
  - 将本地生成的知识库索引、上传简历和投递记录识别为运行产物，保留在本地 ignored 路径，不作为可提交样例数据。
  - 更新 `.gitignore`，默认忽略 `runtime/`、`.local/`、上传文件、投递记录、知识库索引、生成 PDF、diagnostics、日志和临时文件。
  - 新增 `data/samples/README.md`，明确 `data/samples/` 只放脱敏样例，真实运行数据放 `runtime/` 或 `outputs/`。
  - 从 Git 跟踪中移除 `data/knowledge_base/chunks.jsonl`，避免提交真实简历内容或个人信息派生的 chunks。
  - 同步 README、项目总览、规划、运行手册和 AGENTS 当前状态，统一为 Phase 2 Internship Copilot / 实习求职投递管家 Agent 原型。
  - 在 README 和 overview 中补充演示边界：不自动投递、不自动发送 HR 消息、不自动爬取招聘平台，浏览器插件只辅助提取和生成内容。
- Changed files:
  - `.gitignore`
  - `data/samples/README.md`
  - `data/knowledge_base/chunks.jsonl` (removed from Git tracking)
  - `README.md`
  - `documents/00-project-overview.md`
  - `documents/99-project-planning.md`
  - `documents/98-runbook/README.md`
  - `AGENTS.md`
  - `documents/97-journal.md`
- Validation:
  - `git diff --cached --check` — Phase 1 commit clean before commit.
  - Full test suite will run after code refactor and evidence-gate phases.
- Next:
  - Continue with Streamlit thin-UI extraction and AgentRunService entrypoint consolidation.

## 2026-06-21

### DEMO-003 RAG 检索诊断展示

- Executor: Claude Code
- Type: feature / demo
- Summary:
  - CLI 报告新增 "RAG 检索诊断" 章节（section 4），展示 query、综合评级、指标明细表、Top Evidence 详情。
  - Streamlit 新增 "RAG 检索效果" 区域，展示 grade、总分、关键词覆盖率、指标明细、evidence expandable sections。
  - 两个 demo 均在 workflow 完成后调用 `grade_retrieval()` 生成 `RetrievalGradeReport`，展示层只读取结果不实现评分逻辑。
  - CLI 和 Streamlit 均标注评分是规则型诊断，非人工标注或 LLM judge。
- Changed files:
  - `demo/cli/run_job_match_demo.py`
  - `demo/streamlit/app.py`
  - `tests/demo/test_cli_demo_smoke.py`
  - `tests/demo/test_streamlit_app_static.py`
  - `documents/97-journal.md`
- Validation:
  - `python -m pytest -q` — 290 passed
  - `python demo/cli/run_job_match_demo.py` — 报告含 RAG 检索诊断章节
  - `python demo/cli/run_job_match_demo.py --use-langgraph` — LangGraph 路径不变
- Next:
  - 可按需继续后续任务卡或进入展示准备阶段。

### WORKFLOW-002 LangGraph Workflow 迁移

- Executor: Claude Code (接管自 Codex)
- Type: feature / workflow
- Summary:
  - 新增 `src/career_agent/workflows/langgraph_workflow.py`，实现 LangGraph StateGraph。
  - State 包含 raw_jd, parsed_jd, queries, retrieved_chunks, retrieval_scores, missing_keywords, decision, match_analysis, generated_result, report_path, trace_id, logs, retry_count, next_action。
  - 7 个节点：parse_jd, rewrite_query, retrieve_context, grade_retrieval, analyze_match, build_output, write_report。
  - 节点复用现有 Agent/RAG/grading 逻辑，不重写业务代码。
  - 线性流程，预留 decision/retry_count/next_action 供后续条件边使用。
  - Demo 新增 `--use-langgraph` 选项。
  - 保留现有 `JobMatchWorkflow` 不动。
- Changed files:
  - `src/career_agent/workflows/langgraph_workflow.py` (NEW)
  - `demo/cli/run_job_match_demo.py`
  - `tests/workflows/test_langgraph_workflow.py` (NEW)
  - `docs/superpowers/tasks/WORKFLOW-002-langgraph-workflow.md`
  - `documents/97-journal.md`
- Validation:
  - `python -m pytest -q` — 287 passed
  - `python demo/cli/run_job_match_demo.py --use-langgraph` — 4 JD 全部通过
  - retrieval grading 15 tests 全部通过
  - 已有 JobMatchWorkflow 11 tests 全部通过
- Next:
  - Task 3: demo RAG diagnostics (CLI + Streamlit 展示检索诊断报告)

### PACKAGING-001 pyproject 与依赖规范化

- Executor: Codex
- Type: packaging / docs
- Summary:
  - 新增 pyproject.toml，声明 src layout、pytest pythonpath/testpaths 和 langgraph 依赖。
  - 将 README 与本地/服务器 runbook 的主命令切换为 editable install、pytest tests -q、CLI demo 和可选 demo extra。
- Changed files:
  - pyproject.toml
  - README.md
  - documents/98-runbook/01-local-development.md
  - documents/98-runbook/03-school-server-deploy.md
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - python -m pip install -e .
  - pytest tests -q
  - python demo/cli/run_job_match_demo.py
- Next:
  - 继续按任务卡推进 WORKFLOW-002 / DEMO-003。

### RAG-006 布尔检索评分覆盖补充

- Executor: Codex
- Type: test / docs
- Summary:
  - 补充 bool score 拒绝测试，固定 True 不能作为检索 score 通过 traceability。
  - 更新 traceability 文案，明确 score 必须是 0.0 到 1.0 的有限归一化数值。
- Changed files:
  - src/career_agent/rag/grading.py
  - tests/rag/test_retrieval_grading.py
  - documents/05-evaluation/01-rag-evaluation.md
  - documents/97-journal.md
- Validation:
  - PYTHONPATH=src pytest tests/rag/test_retrieval_grading.py::test_boolean_score_fails_traceability -v
  - PYTHONPATH=src pytest tests/rag/test_retrieval_grading.py -v
  - PYTHONPATH=src pytest tests/rag -q
- Next:
  - 继续按任务卡推进 RAG 诊断展示。

### RAG-006 检索评分范围质量修复

- Executor: Codex
- Type: quality-fix / rag-evaluation
- Summary:
  - traceability score 校验新增 0.0 到 1.0 的归一化范围约束。
  - 超过 1.0 或小于 0.0 的 evidence score 不再计入 average_score，避免抬高总评分。
- Changed files:
  - src/career_agent/rag/grading.py
  - tests/rag/test_retrieval_grading.py
  - documents/97-journal.md
- Validation:
  - PYTHONPATH=src pytest tests/rag/test_retrieval_grading.py::test_score_above_one_fails_traceability -v
  - PYTHONPATH=src pytest tests/rag/test_retrieval_grading.py -v
  - PYTHONPATH=src pytest tests/rag -q
- Next:
  - 继续按任务卡推进 RAG 诊断展示。

### RAG-006 检索评分非有限值质量修复

- Executor: Codex
- Type: quality-fix / rag-evaluation
- Summary:
  - traceability score 校验显式拒绝 bool、NaN 和 inf。
  - 非有限 score 不再计入 average_score，避免评分被异常值抬高。
  - 将 EmbeddingVectorStore 文档表述从有限语义理解修正为 lexical / fuzzy substring similarity。
- Changed files:
  - src/career_agent/rag/grading.py
  - tests/rag/test_retrieval_grading.py
  - documents/05-evaluation/01-rag-evaluation.md
  - documents/97-journal.md
- Validation:
  - PYTHONPATH=src pytest tests/rag/test_retrieval_grading.py::test_nan_score_fails_traceability -v
  - PYTHONPATH=src pytest tests/rag/test_retrieval_grading.py -v
  - PYTHONPATH=src pytest tests/rag -q
- Next:
  - 继续按任务卡推进 RAG 诊断展示。

### RAG-006 检索关键词覆盖质量修复

- Executor: Codex
- Type: quality-fix / rag-evaluation
- Summary:
  - 修复 keyword_coverage 对 evidence content 的原始子串匹配问题，避免 Go 误命中 Django。
  - matched_keywords 改为标准化后精确匹配，content 改为 term boundary 匹配。
  - 用行为边界测试替换常量快照测试，并固定代表性 good / excellent 评分用例。
  - 补充 RAG 评估文档中的 RetrievalGradeReport 单次诊断指标表。
- Changed files:
  - src/career_agent/rag/grading.py
  - tests/rag/test_retrieval_grading.py
  - documents/05-evaluation/01-rag-evaluation.md
  - documents/97-journal.md
- Validation:
  - PYTHONPATH=src pytest tests/rag/test_retrieval_grading.py::test_keyword_coverage_does_not_match_inside_longer_word -v
  - PYTHONPATH=src pytest tests/rag/test_retrieval_grading.py -v
  - PYTHONPATH=src pytest tests/rag -q
- Next:
  - 继续按任务卡推进后续 RAG 诊断展示。

### RAG-006 检索评分与诊断报告合规修复

- Executor: Codex
- Type: implementation / rag-evaluation
- Summary:
  - 补齐 RetrievalGradeReport 规则型评分合规项。
  - 将检索评分阈值提取为命名常量。
  - traceability 同时检查 source_path、chunk_id 和 numeric score。
  - 补充 RetrievalGradeReport 与 EvaluationReport 的职责边界说明。
- Changed files:
  - src/career_agent/rag/grading.py
  - tests/rag/test_retrieval_grading.py
  - documents/05-evaluation/01-rag-evaluation.md
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - PYTHONPATH=src pytest tests/rag/test_retrieval_grading.py -v
  - PYTHONPATH=src pytest tests/rag -q
- Next:
  - DEMO-003 RAG 检索诊断展示。

### LANGGRAPH-RAG-DESIGN 文档先行设计与任务拆分

- Executor: Codex
- Type: architecture / planning
- Summary:
  - 新增 LangGraph workflow 与标准 RAG 可观测性设计 spec。
  - 确认采用“标准化重构”：LangGraph 编排 + 标准 RAG 流程 + 规则型检索评分。
  - 新增 WORKFLOW-002 / RAG-006 / DEMO-003 / PACKAGING-001 任务卡。
  - 新增实施计划，后续按任务卡和计划执行代码修改。
- Changed files:
  - docs/superpowers/specs/2026-06-21-langgraph-rag-standardization-design.md
  - docs/superpowers/tasks/WORKFLOW-002-langgraph-workflow.md
  - docs/superpowers/tasks/RAG-006-retrieval-grading.md
  - docs/superpowers/tasks/DEMO-003-rag-diagnostics-display.md
  - docs/superpowers/tasks/PACKAGING-001-pyproject-and-dependencies.md
  - docs/superpowers/plans/2026-06-21-langgraph-rag-standardization.md
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 本轮为文档先行与计划编写，未修改核心实现代码。
  - 设计 spec 已由用户确认。
- Next:
  - 按计划执行 WORKFLOW-002 / RAG-006 / DEMO-003 / PACKAGING-001。

## 2026-06-20

### REVIEW-002 / PRESENTATION-001 / RESUME-001 最终审查与展示材料

- Executor: Claude Code + DeepSeek
- Type: review / presentation
- Summary:
  - 最终项目审查：完成度 95%，216 tests，全部规划模块完成。
  - 风险检查清单：10 项全部通过，无阻塞问题。
  - 5-8 分钟口语化展示脚本。
  - 简历项目描述（4 个版本）+ 可写/不可写清单。
  - GitHub README 审查建议。
- Changed files:
  - documents/07-review/04-final-project-review.md
  - documents/07-review/05-final-risk-checklist.md
  - documents/08-presentation/06-final-demo-script.md
  - documents/08-presentation/07-resume-polish.md
  - documents/08-presentation/08-github-readme-review.md
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 本轮未修改核心代码。
  - 所有表述基于当前真实能力。
  - 无夸大、无虚构。
  - 216 tests passed.
- Next:
  - 可选：添加 README 截图和架构图
  - 可选：GitHub Repo Agent
  - 可选：Embedding 检索

### EVAL-003 评估文档补充

- Executor: Claude Code + DeepSeek
- Type: documentation / evaluation
- Summary:
  - 补充评估模块说明文档。
  - 更新 RAG/Agent 输出/Demo case 评估文档。
  - 新增评估 runner 使用说明。
  - README 添加评估命令。
- Changed files:
  - README.md
  - documents/05-evaluation/
  - documents/97-journal.md
- Validation:
  - 仅补充文档，未修改核心代码。
  - 216 tests passed.
- Next:
  - 可考虑 GitHub Repo Agent 或 Embedding 检索增强。

### EVAL-002 多 JD 评估 Runner

- Executor: Claude Code + DeepSeek
- Type: evaluation / demo
- Summary:
  - 新增评估 runner，对 4 个示例 JD 执行批量评估。
  - 生成 Markdown 评估报告到 outputs/demo/。
  - 8 个 runner smoke test 通过。
- Changed files:
  - demo/evaluation/run_evaluation.py
  - tests/demo/test_evaluation_runner.py
  - documents/97-journal.md
- Validation:
  - 评估 runner 不依赖外部模型。
  - 未修改核心 RAG / Agent / Workflow 逻辑。
  - 216 tests passed.
- Next:
  - EVAL-003 评估文档补充

### EVAL-001 评估数据结构与基础规则

- Executor: Claude Code + DeepSeek
- Type: implementation / evaluation
- Summary:
  - 新增 EvaluationItem / EvaluationReport 数据结构。
  - 新增 5 条轻量评估规则（status/evidence count/output non-empty/refs/coverage）。
  - 18 个评估测试全部通过。
- Changed files:
  - src/career_agent/evaluation/
  - tests/evaluation/test_evaluation_rules.py
  - documents/97-journal.md
- Validation:
  - 未修改 RAG / Agent / Workflow 核心逻辑。
  - 未调用外部模型或网络。
  - 208 tests passed.
- Next:
  - EVAL-002 多 JD 评估 runner

### MODEL-002 BuildAgent 可选模型生成

- Executor: Claude Code + DeepSeek
- Type: implementation / agent-model-integration
- Summary:
  - BuildAgent 支持可选 ModelProvider，默认规则型。
  - use_llm=True 时 communication_message 使用 LLM 生成。
  - LLM 失败时 fallback 到规则型。
  - 8 个新测试覆盖 LLM 路径、fallback、不编造约束。
- Changed files:
  - src/career_agent/agents/build_agent.py
  - tests/agents/test_build_agent.py
  - documents/97-journal.md
- Validation:
  - 190 tests passed（新增 8 个 build_agent LLM 测试）。
  - 默认 use_llm=False，行为与 Phase 1 完全一致。
  - 所有测试使用 MockProvider，不依赖真实 API。
- Next:
  - Phase D: Demo 层 LLM 说明

### MODEL-001 Phase B：模型 Provider 实现

- Executor: Claude Code + DeepSeek
- Type: implementation / model-provider
- Summary:
  - 实现 ModelProvider 抽象接口、MockProvider、DeepSeekProvider。
  - MockProvider 返回固定/可预测文本，记录 prompt。
  - DeepSeekProvider 使用标准库 urllib 调用 API，从环境变量读取配置。
  - 17 个 model 测试，全部不依赖真实网络。
- Changed files:
  - src/career_agent/models/
  - tests/models/
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 182 tests passed（165 已有 + 17 model）。
  - 无 API Key 时代码不崩溃，仅 generate 时报清晰错误。
  - 未引入第三方依赖。
- Next:
  - Phase C: BuildAgent 可选接入 ModelProvider

### MODEL-001 模型 Provider 抽象决策文档

- Executor: Claude Code + DeepSeek
- Type: documentation / decision
- Summary:
  - 新增模型 Provider 抽象技术决策文档。
  - 新增 MODEL-001 任务卡。
- Changed files:
  - documents/03-technical-decisions/07-model-provider-abstraction.md
  - docs/superpowers/tasks/MODEL-001-provider-abstraction.md
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 仅文档，未改代码。
  - 165 tests passed.
- Next:
  - Phase B: 实现 ModelProvider / MockProvider / DeepSeekProvider

### PRESENTATION-001 展示材料整理 + 文档一致性修复

- Executor: Claude Code + DeepSeek
- Type: documentation / presentation
- Summary:
  - 创建答辩/展示大纲（10-12 分钟完整流程 + 备用方案）。
  - 创建简历表达参考（按 RAG/Agent/工程/架构 4 个侧重点提供 bullet）。
  - 完成 README 与代码一致性检查，确认无过时描述。
- Changed files:
  - documents/07-review/04-presentation-outline.md
  - documents/07-review/05-resume-bullets.md
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 未修改任何 src/ 或 tests/ 代码。
  - README 与实际代码状态一致。
  - 所有文档描述基于真实已完成的功能。
- Next:
  - 可选：接入 LLM API
  - 可选：LangGraph 迁移

### REVIEW-001 项目整体审查

- Executor: Claude Code + DeepSeek
- Type: review / documentation
- Summary:
  - 完成项目整体审查：完成度、亮点、不足、建议。
  - 识别 5 个风险点并给出修复优先级。
  - 完成 GitHub 展示就绪检查清单。
- Changed files:
  - documents/07-review/（4 文件）
  - documents/97-journal.md
  - documents/99-project-planning.md
- Key findings:
  - 项目适合期末实训展示和写进简历。
  - 165 tests 全部通过，零外部依赖。
  - 主要不足：关键词检索精度、规则型 Agent 质量、缺少 pyproject.toml 和 CI。
  - 最值得增强：接入 LLM API + Embedding 检索。
- Next:
  - PRESENTATION-001 展示材料整理

### DEPLOY-001 学校服务器部署文档

- Executor: Claude Code + DeepSeek
- Type: documentation / deployment
- Summary:
  - 重写学校服务器部署文档，补充 Streamlit 运行方式和端口说明。
  - 补充展示前检查清单。
  - 补充分布式问题排查项。
- Changed files:
  - documents/98-runbook/03-school-server-deploy.md
  - documents/98-runbook/04-troubleshooting.md
  - documents/98-runbook/05-server-demo-checklist.md
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 未创建 server/FastAPI/backend。
  - 未新增部署脚本或密钥文件。
  - 未引入外部依赖。
- Next:
  - 可开始准备答辩展示材料。
  - 后续可接入真实模型 API。

### DEMO-002 Streamlit Demo

- Executor: Claude Code + DeepSeek
- Type: demo / streamlit
- Summary:
  - 创建 Streamlit 可视化 demo。
  - 支持选择示例 JD 或粘贴 JD 文本，设置 top_k。
  - 调用 JobMatchWorkflow 展示完整分析结果。
  - 添加 15 个 Streamlit 静态测试。
- Changed files:
  - demo/streamlit/app.py
  - tests/demo/test_streamlit_app_static.py
  - .gitignore
  - documents/06-demo/
  - documents/98-runbook/
  - README.md
- Validation:
  - Streamlit demo 只调用 workflow，不重写核心逻辑。
  - 未引入 FastAPI / LangGraph / LangChain。
  - 未调用外部模型或网络。
  - 165 tests passed.
- Next:
  - DEPLOY-001 学校服务器部署文档

### README 当前状态更新

- Executor: Claude Code + DeepSeek
- Type: documentation / readme
- Summary:
  - 更新 README 反映当前真实项目状态。
  - 添加已完成模块表、快速运行命令、项目结构总览。
  - 更新后续开发流程状态标记。
- Changed files:
  - README.md
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 仅更新 README。
  - 未修改业务代码。
- Next:
  - push 到 GitHub。

### DEMO-DOC-001 Demo 展示文档补强

- Executor: Claude Code + DeepSeek
- Type: documentation / demo
- Summary:
  - 补充 CLI demo 展示脚本（10 分钟完整讲解）。
  - 补充样例数据说明与使用建议。
  - 补充答辩与实习展示流程（12 分钟 + 兜底方案）。
- Changed files:
  - documents/06-demo/（4 文件）
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 仅补充文档。
  - 未修改业务代码。
  - 未实现 Streamlit。
- Next:
  - README 当前状态更新

### DOC-RUNBOOK-001 运行手册补充

- Executor: Claude Code + DeepSeek
- Type: documentation / runbook
- Summary:
  - 补充本地开发运行手册。
  - 补充 GitHub 同步手册。
  - 补充学校服务器部署与 CLI demo 复现说明。
  - 补充常见问题排查。
- Changed files:
  - documents/98-runbook/（5 文件）
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 文档仅描述当前已存在的 CLI demo。
  - 未假设 frontend/backend/server。
  - 未修改业务代码。
- Next:
  - DEMO-DOC-001 演示文档补强

### DEMO-001 CLI Demo

- Executor: Claude Code + DeepSeek
- Type: demo / cli
- Summary:
  - 创建 CLI demo 入口 run_job_match_demo.py。
  - 支持 --profile-dir / --job-file / --output-file / --top-k 参数。
  - 输出 Markdown 报告到 outputs/demo/，包含 6 个章节。
  - 添加 10 个 CLI smoke test。
- Changed files:
  - demo/cli/run_job_match_demo.py
  - tests/demo/test_cli_demo_smoke.py
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - CLI demo 只调用 workflow，不重写核心逻辑。
  - 未引入外部依赖。
  - 未实现 Streamlit 或 FastAPI。
  - 150 tests passed.
- Next:
  - DOC-RUNBOOK-001 运行手册

### WORKFLOW-001 JobMatchWorkflow 集成

- Executor: Claude Code + DeepSeek
- Type: implementation / workflow
- Summary:
  - 实现 JobMatchWorkflow，串联全部 Agent。
  - 链路：JD 文本 → JDParser → RAGRetrieve → MatchAnalysis → Build → AgentTaskState。
  - 出错时 status=failed 并记录 error_message。
  - 不引入 LangGraph，不调用外部模型。
- Changed files:
  - src/career_agent/workflows/__init__.py
  - src/career_agent/workflows/job_match_workflow.py
  - tests/workflows/test_job_match_workflow.py
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 未修改 RAG 模块和所有 Agent。
  - 完整链路 4 份 JD 均返回 status=completed。
  - 140 tests passed (61 RAG + 68 agents + 11 workflow).
- Next:
  - DEMO-001 CLI demo
  - DEMO-002 Streamlit demo

### AGENT-005 BuildAgent

- Executor: Claude Code + DeepSeek
- Type: implementation / agent-build
- Summary:
  - 实现模板型 BuildAgent。
  - resume_bullets 严格基于 evidence，不编造经历。
  - evidence 为空时输出保守提示。
  - 不调用 LLM。
- Changed files:
  - src/career_agent/agents/build_agent.py
  - tests/agents/test_build_agent.py
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 未修改 RAG 模块和已有 Agent。
  - 129 tests passed.
- Next:
  - WORKFLOW-001 JobMatchWorkflow 集成

### AGENT-004 MatchAnalysisAgent

- Executor: Claude Code + DeepSeek
- Type: implementation / agent-match-analysis
- Summary:
  - 实现规则型 MatchAnalysisAgent。
  - 对比 ParsedJD 与 RetrievedEvidence，生成 strengths/weaknesses/recommended_projects/suggestions。
  - 不调用 LLM。
- Changed files:
  - src/career_agent/agents/match_analysis_agent.py
  - tests/agents/test_match_analysis_agent.py
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 未修改 RAG 模块和已有 Agent。
  - 120 tests passed.
- Next:
  - AGENT-005 BuildAgent

### AGENT-003 RAGRetrieveAgent

- Executor: Claude Code + DeepSeek
- Type: implementation / agent-rag-retrieve
- Summary:
  - 实现 RAGRetrieveAgent，包装 RAGPipeline。
  - build_query_from_parsed_jd 从 ParsedJD 构造检索 query。
  - 支持 retrieve 和 retrieve_by_query 两种检索方式。
- Changed files:
  - src/career_agent/agents/rag_retrieve_agent.py
  - tests/agents/test_rag_retrieve_agent.py
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 未修改 RAG 模块和已有 Agent。
  - 110 tests passed (61 RAG + 19 state + 18 jd_parser + 12 rag_retrieve).
- Next:
  - AGENT-004 MatchAnalysisAgent

### AGENT-002 JDParserAgent

- Executor: Claude Code + DeepSeek
- Type: implementation / agent-jd-parser
- Summary:
  - 实现规则型 JDParserAgent。
  - 从 JD 文本提取 job_title、job_direction、hard/bonus/soft skills、keywords。
  - 不调用 LLM，纯关键词匹配。
- Changed files:
  - src/career_agent/agents/jd_parser.py
  - tests/agents/test_jd_parser.py
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 未修改 state.py 和 RAG 模块。
  - 98 tests passed (61 RAG + 19 state + 18 jd_parser).
- Next:
  - AGENT-003 RAGRetrieveAgent

### AGENT-001 AgentTaskState 设计

- Executor: Claude Code + DeepSeek
- Type: implementation / agent-state
- Summary:
  - 实现 ParsedJD、MatchAnalysisResult、GeneratedOutput、AgentTaskState 四个 dataclass。
  - 使用 default_factory 避免可变对象共享。
  - task_id 自动生成，status 默认为 created。
  - retrieved_evidence 使用已有 RetrievedEvidence 类型。
- Changed files:
  - src/career_agent/agents/__init__.py
  - src/career_agent/agents/state.py
  - tests/agents/test_state.py
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 未修改 RAG 模块。
  - 未实现 Agent 逻辑。
  - 80 tests passed (61 RAG + 19 state).
- Next:
  - AGENT-002 JDParserAgent

### RAG-005 RAGPipeline 集成

- Executor: Codex
- Type: implementation / rag-pipeline
- Summary:
  - 实现 SimpleRetriever。
  - 实现 RAGPipeline。
  - 串联 MarkdownProfileLoader、TextChunker、MemoryVectorStore。
  - 支持从本地 Markdown 目录构建索引并返回 RetrievedEvidence。
- Changed files:
  - src/career_agent/rag/retrievers/__init__.py
  - src/career_agent/rag/retrievers/simple_retriever.py
  - src/career_agent/rag/pipeline.py
  - tests/rag/test_rag_pipeline.py
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 未修改 schema、loader、chunking、vectorstore。
  - 未实现 Agent 或 workflow。
  - 未引入 Chroma / FAISS / LangChain / LangGraph。
  - 测试不依赖外部模型或网络。
- Next:
  - AGENT-001 AgentTaskState 建议交给 Codex。
  - AGENT-002 JDParserAgent 可交给 Claude Code + DeepSeek。

### RAG-004 VectorStore 接口与 MemoryVectorStore

- Executor: Codex
- Type: implementation / rag-vectorstore
- Summary:
  - 定义 VectorStore 抽象接口。
  - 实现 MemoryVectorStore。
  - 支持添加 DocumentChunk、关键词检索、top_k、clear、count。
  - 返回 RetrievedEvidence 列表。
- Changed files:
  - src/career_agent/rag/vectorstores/__init__.py
  - src/career_agent/rag/vectorstores/base.py
  - src/career_agent/rag/vectorstores/memory_store.py
  - tests/rag/test_vectorstore_interface.py
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 未修改 schema、loader、chunking。
  - 未实现 retriever/pipeline。
  - 未引入 Chroma / FAISS / LangChain / LangGraph。
  - 测试不依赖外部模型或网络。
- Next:
  - RAG-005 RAGPipeline 集成建议交给 Codex。

### RAG-003 文本清洗与 Chunk 切分

- Executor: Claude Code + DeepSeek
- Type: implementation / rag-chunking
- Summary:
  - 实现 TextChunker。
  - 支持文本清洗、单文档切分、多文档切分、overlap。
  - 将 ProfileDocument 转换为 DocumentChunk。
  - 添加 chunking 单元测试。
- Changed files:
  - src/career_agent/rag/chunking/__init__.py
  - src/career_agent/rag/chunking/text_chunker.py
  - tests/rag/test_text_chunker.py
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 未修改 RAG schema。
  - 未修改 MarkdownProfileLoader。
  - 未实现 vectorstore/retriever/pipeline。
  - 测试不依赖外部模型或网络。
  - 49 tests passed (6 schema + 20 loader + 23 chunker).
- Next:
  - RAG-004 VectorStore interface 建议交给 Codex。
  - RAG-005 RAG Pipeline 建议交给 Codex。

### RAG-002 Markdown 用户资料加载器

- Executor: Claude Code + DeepSeek
- Type: implementation / rag-loader
- Summary:
  - 实现 MarkdownProfileLoader。
  - 支持读取单个 Markdown 文件和目录。
  - 将 Markdown 文件转换为 ProfileDocument。
  - 添加 loader 单元测试。
- Changed files:
  - src/career_agent/rag/loaders/__init__.py
  - src/career_agent/rag/loaders/markdown_loader.py
  - tests/rag/test_markdown_loader.py
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 未修改 RAG schema。
  - 未实现 chunking/vectorstore/retriever/pipeline。
  - 测试不依赖外部模型或网络。
  - 26 tests passed (6 schema + 20 loader).
- Next:
  - RAG-003 Text Chunking 可继续由 Claude Code + DeepSeek 实现。
  - RAG-004 VectorStore interface 建议交给 Codex。

### SAMPLE-001 示例用户资料与岗位 JD（v2 按新结构重建）

- Executor: Claude Code + DeepSeek
- Type: data / sample
- Summary:
  - 按新目录结构重建 SAMPLE-001：`data/samples/profile/` + `data/samples/jobs/`。
  - 创建 9 份脱敏示例数据文件。
  - 用户资料贴合化学+计算机交叉背景，项目包含智能投递 Agent、自动滴定、Smart Journey、CNN 分类。
  - 4 份 JD 覆盖 Agent 开发、RAG 工程师、AI 应用开发、后端 AI 方向。
- Changed files:
  - data/samples/profile/resume.md
  - data/samples/profile/projects.md（4 个项目）
  - data/samples/profile/github_repos.md（5 个仓库）
  - data/samples/profile/skills.md（7 个技能分区）
  - data/samples/profile/internship.md（2 段实习/实践）
  - data/samples/jobs/agent_intern_jd.md
  - data/samples/jobs/rag_engineer_intern_jd.md
  - data/samples/jobs/ai_application_intern_jd.md
  - data/samples/jobs/backend_ai_intern_jd.md
  - documents/06-demo/02-demo-data.md
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 所有数据为脱敏虚构内容，无真实手机号/邮箱/学号/API Key。
  - 未修改 src/、tests/、outputs/。
  - 未写 Python 业务代码。
  - projects.md 严格按照统一结构：类型/背景/技术栈/个人负责/核心亮点/可匹配岗位/简历依据。
  - JD 覆盖 Agent、RAG、AI 应用、后端四个方向。
- Key decisions:
  - 用户设定为化学+计算机交叉背景，更贴合真实大学生情况（非纯 CS）。
  - 项目经历不过度包装，不使用"精通""独立上线大型平台"等措辞。
  - 智能投递 Agent 项目本身成为用户资料的一部分，体现"自用工具"的产品思维。
- Next:
  - RAG-002 Markdown Loader 可基于新结构读取 `data/samples/profile/`。
  - RAG-003 Text Chunking 可针对 resume/skills/projects 等不同内容类型设计 chunk 策略。

### SAMPLE-001 示例用户资料与岗位 JD（v1 已废弃，被 v2 替代）

- Executor: Claude Code + DeepSeek
- Type: data / sample
- Summary:
  - 第一版创建了 4 份扁平样例数据文件。
  - 已被 v2 按新目录结构替代。
- Changed files (v1, superseded):
  - data/samples/profile.md（已删除）
  - data/samples/projects.md（已删除）
  - data/samples/github_summary.md（已删除）
  - data/samples/jd_agent_intern.md（已删除）



### RAG-001 RAG 核心数据结构设计

- Executor: Codex
- Type: implementation / schema
- Summary:
  - 创建 RAG 核心 schema。
  - 实现 ProfileItem、ProfileDocument、DocumentChunk、RetrievedEvidence。
  - 添加 schema 单元测试。
- Changed files:
  - src/career_agent/rag/schemas.py
  - tests/rag/test_schemas.py
  - documents/97-journal.md
  - documents/99-project-planning.md
- Validation:
  - 仅实现 schema，不实现 loader/chunking/vectorstore/pipeline。
  - 测试不依赖外部模型或网络。
- Next:
  - RAG-002 Markdown Loader 可交给 Claude Code + DeepSeek。
  - RAG-003 Text Chunking 可交给 Claude Code + DeepSeek。
  - RAG-004 VectorStore interface 建议交给 Codex。

### ARCH-003 代码目录结构决策与第一阶段工程骨架规划

- Executor: Codex
- Type: architecture / codebase planning
- Summary:
  - 基于 ARCH-002 开源项目调研结果，确定第一阶段代码目录结构建议。
  - 决定采用 src/career_agent 作为 Python package。
  - 决定第一阶段不做完整 frontend/backend/server。
  - 决定第一阶段先使用普通 Python workflow，后续再接 LangGraph。
  - 决定第一阶段先抽象 VectorStore interface，具体向量库后续替换。
  - 决定 demo 层只调用 workflow，不重写业务逻辑。
  - 补强 RAG、Agent、Workflow、Demo 后续实现任务卡。
- Changed files:
  - documents/02-design/
  - documents/03-technical-decisions/
  - docs/superpowers/tasks/
  - documents/99-project-planning.md
  - documents/97-journal.md
- Validation:
  - 本轮未实现业务代码。
  - 本轮未修改 src/、tests/、data/、outputs/。
  - 本轮未引入依赖。
- Next:
  - RAG-001 可交给 Codex。
  - SAMPLE-001、RAG-002、RAG-003 可交给 Claude Code + DeepSeek。
  - RAG-004、RAG-005、AGENT-001 建议交给 Codex。

### DOC-REFERENCE-001 开源项目参考文档补全

- Executor: Claude Code + DeepSeek
- Type: documentation / research
- Summary:
  - 基于 ARCH-002 调研结果，对 8 个开源项目进行深入分析。
  - 每个项目补充了：项目定位、典型目录结构、RAG 设计参考点、Agent 编排参考点、工程化/demo 参考点、不适合照搬原因、对本项目具体启发。
  - 新增八个项目横向对比表（定位、RAG、Agent、工程化四个维度）。
  - 明确第一阶段技术路线确认矩阵（输入/RAG/Agent/状态/输出/部署/模型/评估/文档）。
  - 确认本项目不采用 Dify/RAGFlow/Flowise 重型平台路线，不采用 DeerFlow/OpenHands 过度设计，不照搬 LangGraph 框架依赖。
- Changed files:
  - documents/99-knowledge-base/05-open-source-reference-projects.md（大幅扩充）
  - documents/97-journal.md（本记录）
  - documents/99-project-planning.md（状态更新）
- Validation:
  - 本轮未实现业务代码。
  - 本轮未修改 src/、tests/、data/、outputs/。
  - 本轮未修改 02-design/、03-technical-decisions/ 已有文件内容。
  - 所有新增内容为中文 Markdown。
  - 未复制开源项目 README 大段内容。
- Key findings:
  - LangGraph：状态化 workflow 思想值得采用，但第一阶段用普通 Python workflow，预留迁移路径。
  - LangGraph RAG：检索后评估（document grading）和 query analysis 思想值得吸收，但多轮自校正第一阶段不需要。
  - Dify：知识库生命周期管理和 workflow 可视化思维值得借鉴，但平台架构不照搬。
  - RAGFlow：RAG pipeline 分层（loader/chunker/vectorstore/retriever/pipeline）是核心启发，但复杂文档解析不需要。
  - DeerFlow：Agent 边界和 memory 分层思想值得采用，但 supervisor/sandbox/skills 过度设计。
  - OpenHands：任务卡声明允许/禁止操作是重要启发，但代码执行和 sandbox 不需要。
  - Khoj："个人知识库"定位是本项目最接近的参考，但功能范围需裁剪为求职场景。
  - Flowise：流程可视化思想用于 demo 展示，但不做低代码平台。
- Next:
  - ARCH-003 代码目录结构决策（Codex 执行）。

### ARCH-002 开源项目调研与参考架构沉淀

- Executor: Codex
- Type: architecture / research / documentation
- Summary:
  - 调研 RAG、多 Agent、个人知识库、AI 应用平台相关开源项目。
  - 总结 LangGraph、Dify、RAGFlow、DeerFlow、OpenHands、Khoj、Flowise 等项目的可借鉴设计。
  - 明确本项目不照搬重型平台，而是裁剪吸收状态化 workflow、RAG pipeline、sub-agent 边界、个人知识库和轻量 demo 设计。
  - 新增参考架构决策文档和后续任务卡。
- Changed files:
  - documents/99-knowledge-base/05-open-source-reference-projects.md
  - documents/03-technical-decisions/06-reference-architecture-selection.md
  - documents/02-design/07-reference-inspired-architecture.md
  - docs/superpowers/tasks/ARCH-002-open-source-reference-research.md
  - docs/superpowers/tasks/DOC-REFERENCE-001-open-source-reference-docs.md
  - docs/superpowers/tasks/ARCH-003-codebase-structure-decision.md
- Validation:
  - 本轮未实现业务代码。
  - 本轮未修改 src/、tests/、data/、outputs/。
  - 本轮未引入依赖。
- Next:
  - 可交给 Claude Code + DeepSeek 继续补充开源项目参考细节。
  - 可由 Codex 执行 ARCH-003，最终确定代码目录结构。

### ARCH-001 补强核心架构边界与模块契约

- Executor: Codex
- Type: architecture / documentation
- Summary:
  - 补强项目总览、需求边界、RAG 模块设计、多 Agent 编排设计。
  - 明确第一阶段采用 CLI + Streamlit，不做完整前后端。
  - 明确第一阶段 RAG 只处理本地 Markdown 用户资料和 GitHub 仓库摘要。
  - 明确第一阶段多 Agent 只包含 JDParserAgent、RAGRetrieveAgent、MatchAnalysisAgent、BuildAgent。
  - 补强后续 RAG、Agent、Workflow、Demo 任务卡。
- Changed files:
  - README.md
  - documents/00-project-overview.md
  - documents/01-requirements/
  - documents/02-design/
  - documents/03-technical-decisions/
  - documents/04-challenges/
  - documents/05-evaluation/
  - documents/06-demo/
  - documents/97-journal.md
  - documents/99-project-planning.md
  - docs/superpowers/
- Validation:
  - 本轮未实现业务代码。
  - 本轮未修改 src/、tests/、data/、outputs/。
  - 本轮未引入依赖。
- Next:
  - 可将 DOC-RUNBOOK-001、SAMPLE-001 交给 Claude Code + DeepSeek。
  - 可将 RAG-001、AGENT-001 保留给 Codex。

### DOC-INIT-001 初始化项目文档体系

- Executor: Codex
- Type: documentation / structure
- Summary:
  - 初始化中文 documents 文档体系。
  - 初始化 docs/superpowers Agent 执行规范体系。
  - 创建 AGENTS.md 多 AI 协作规则。
  - 创建基础目录占位。
- Changed files:
  - README.md
  - AGENTS.md
  - documents/
  - docs/superpowers/
  - src/
  - tests/
  - data/
  - outputs/
- Validation:
  - 本轮未实现业务代码。
  - 本轮未创建 frontend/backend/server。
  - 文档目录采用分层结构，避免 documents 下平铺大量 md。
- Next:
  - 补充 requirements 文档。
  - 补充 RAG 模块设计文档。
  - 补充多 Agent 编排设计文档。
