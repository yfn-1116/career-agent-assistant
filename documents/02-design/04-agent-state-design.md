# Agent 状态设计

## 用途

本文档定义 `AgentTaskState` 的字段方向、生命周期和边界，用于避免多 Agent 上下文混乱，并为后续 LangGraph 集成预留基础。

## 为什么需要状态

多 Agent 链路中，JD 解析、检索证据、匹配分析和最终输出来自不同节点。如果只靠 prompt 拼接传递上下文，容易出现信息污染、字段丢失、错误难追踪和幻觉扩散。统一状态对象可以让每一步输入输出可见、可记录、可复现。

## AgentTaskState 字段方向

第一阶段建议字段：

- `task_id`：一次求职辅助任务的唯一标识。
- `user_request`：用户原始请求。
- `job_description`：用户输入的岗位 JD。
- `parsed_jd`：`JDParserAgent` 输出的结构化岗位信息。
- `retrieved_evidence`：`RAGRetrieveAgent` 返回的资料证据。
- `match_analysis`：`MatchAnalysisAgent` 输出的匹配分析。
- `generated_output`：`BuildAgent` 生成的最终 Markdown 内容。
- `review_result`：后续 ReviewAgent 或人工复核结果。
- `status`：任务状态，例如 pending、running、completed、failed、needs_review。
- `error_message`：失败原因。
- `created_at`：任务创建时间。
- `updated_at`：任务更新时间。

## 第一阶段实现字段

第一阶段优先实现：

- `task_id`
- `user_request`
- `job_description`
- `parsed_jd`
- `retrieved_evidence`
- `match_analysis`
- `generated_output`
- `status`
- `error_message`

## 后续扩展字段

后续可扩展：

- `review_result`
- `human_feedback`
- `application_record`
- `model_trace`
- `cost_summary`
- `server_runtime_info`

## 状态如何服务于 LangGraph

LangGraph 的节点通常围绕共享状态读写。提前设计 `AgentTaskState` 可以降低从普通 workflow 切换到 LangGraph 的迁移成本，并让每个节点只更新自己负责的字段。

## 状态如何服务于日志追踪

每个 Agent 运行后都可以记录状态快照，便于定位是哪一步输出异常，例如 JD 解析错误、检索证据不足、匹配分析偏离或最终输出编造。

## 状态如何避免上下文混乱

- 每个 Agent 只读取必要字段。
- 每个 Agent 只写入自己的输出字段。
- 证据和生成内容分开保存。
- 错误信息进入 `error_message`，不混入最终输出。

## 当前状态

本轮只定义状态设计方向，不实现 schema 代码。

## 后续维护规则

- `AGENT-001` 负责把本文档转化为更具体的 schema 设计。
- 修改核心字段前必须评估对 workflow、日志和评估文档的影响。

## ARCH-003 代码结构决策

`AgentTaskState` 后续放在 `src/career_agent/agents/state.py`。第一阶段先服务普通 Python workflow，字段设计保留 LangGraph 迁移可能性。

第一阶段必须支持：

- `task_id`
- `user_request`
- `job_description`
- `parsed_jd`
- `retrieved_evidence`
- `match_analysis`
- `generated_output`
- `status`
- `error_message`
- `created_at`
- `updated_at`

后续 LangGraph 阶段再考虑 checkpoint、node trace、human feedback 等字段。
