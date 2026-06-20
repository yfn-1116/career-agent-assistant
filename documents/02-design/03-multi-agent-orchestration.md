# 多 Agent 编排设计

## 用途

本文档定义第一阶段多 Agent 的职责、边界和后续扩展路径。

## 第一阶段核心 Agent

### JDParserAgent

负责解析岗位 JD，输出岗位标题、职责、技术栈、能力要求、加分项、关键词和检索查询。

边界：不调用 RAG，不生成简历，不做匹配分析。

### RAGRetrieveAgent

负责根据 `parsed_jd` 调用 RAG pipeline，返回 `RetrievedEvidence` 列表。

边界：不评价匹配程度，不改写简历，不生成最终输出。

### MatchAnalysisAgent

负责比较岗位要求和检索证据，生成匹配分析。

边界：不直接读取原始资料，不生成最终简历段落。

### BuildAgent

负责基于 `retrieved_evidence` 和 `match_analysis` 生成最终 Markdown 输出，包括简历项目描述和沟通话术。

边界：不得编造未被证据支持的经历。

## Orchestrator 策略

第一阶段可以先使用普通 Python workflow 或轻量状态流，按固定顺序串联四个 Agent。后续当需要状态恢复、分支路由、节点级可观测性和复杂人审节点时，再引入 LangGraph。

## 第一阶段不做

- 复杂多层递归 Agent。
- 自动浏览器操作。
- 自动投递。
- 多用户协作。
- 复杂权限系统。

## 后续扩展 Agent

- `PlanAgent`：拆解求职准备计划。
- `ReviewAgent`：复核输出是否可信。
- `GitHubRepoAgent`：按需读取 GitHub 仓库资料。
- `OCRAgent`：处理证书、截图、PDF 图片材料。
- `SearchAgent`：外部搜索辅助。
- `ApplicationTrackerAgent`：投递记录管理。

## 当前状态

当前只完成职责设计，未实现 Agent。

## 后续维护规则

- 每个 Agent 必须有独立任务卡。
- Agent 之间只能通过明确状态字段传递信息。
- workflow 集成必须由 Codex 负责或复核。
