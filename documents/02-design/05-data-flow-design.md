# 数据流设计

## 用途

本文档说明当前 Internship Copilot 原型从用户输入到最终展示的完整数据流，以及每一步的输入、输出和边界。

## 主流程

```text
CLI / Streamlit / FastAPI / Browser Extension
-> AgentRunService
-> LangGraph workflow 或兼容 Python workflow
-> JDParserAgent 解析岗位
-> RAGRetrieveAgent / RAGPipeline 检索用户资料
-> RetrievalGradeReport / retry / fallback
-> MatchAnalysisAgent 生成匹配分析
-> BuildAgent 生成最终输出
-> FaithfulnessChecker / Evidence warnings
-> Markdown / Streamlit / API response / diagnostics / application record
```

## 步骤一：用户输入 JD

- 输入：岗位 JD 文本或 Markdown。
- 输出：写入 `AgentTaskState.job_description`。
- 边界：不自动爬取岗位网站；Browser Extension 只读取当前页面文本，发送和投递动作由用户确认。

## 步骤二：JDParserAgent 解析岗位

- 输入：`job_description`。
- 输出：`parsed_jd`，包含岗位标题、职责、技术栈、能力要求、关键词、检索查询。
- 边界：不调用 RAG，不生成简历。

## 步骤三：RAGRetrieveAgent 检索资料

- 输入：`parsed_jd` 中的关键词和检索查询。
- 输出：`retrieved_evidence`。
- 边界：只返回证据，不做匹配判断。

## 步骤四：MatchAnalysisAgent 生成匹配分析

- 输入：`parsed_jd`、`retrieved_evidence`。
- 输出：`match_analysis`，包含强匹配、弱匹配、缺口和建议。
- 边界：不编写最终简历段落。

## 步骤五：BuildAgent 生成最终输出

- 输入：`retrieved_evidence`、`match_analysis`、用户请求。
- 输出：`generated_output`，包括 Markdown 报告、简历项目描述、沟通话术。
- 边界：只能基于证据生成，不得编造经历。

## 步骤六：展示

- CLI：输出 Markdown 文件或终端摘要。
- Streamlit：调用 `KnowledgeBaseService`、`ApplicationService` 和 `AgentRunService`，只保留页面布局、按钮事件和展示逻辑。
- FastAPI / Browser Extension：调用 `AgentRunService` 处理岗位分析、岗位列表、HR 回复和话术生成。
- Application memory：通过 `ApplicationService` 写入 ignored runtime JSONL，不提交真实投递记录。

## 失败路径

- JD 解析失败：返回错误提示和原始 JD 检查建议。
- 检索证据不足：提示需要补充资料，而不是强行生成。
- 生成内容缺少证据：进入 review 或标记为需要人工确认。

## 当前状态

当前数据流已在 `src/career_agent/service/agent_run.py`、`src/career_agent/workflows/langgraph_workflow.py`、`demo/streamlit/app.py` 和 `src/career_agent/api/app.py` 中实现。后续优化重点是继续减少展示层直接调用底层模块，并加深 Evidence Gate / Faithfulness 对最终输出的影响。

## 后续维护规则

- 新增 Agent 必须说明在数据流中的位置。
- 展示层不得绕过 `AgentRunService` 直接重写 JD 解析、RAG 检索、匹配分析、话术生成或投递记录保存。

## ARCH-003 代码结构决策

历史 Phase 1 数据流由 `src/career_agent/workflows/job_match_workflow.py` 串联。当前 Phase 2 默认收敛到 `AgentRunService`，由它调用 LangGraph workflow、message/reply agent、job discovery、application repository 等能力。

`demo/cli/` 仍保留 CLI 演示入口；`demo/streamlit/` 负责轻量页面展示；`src/career_agent/api/` 为浏览器插件提供本地 API。三者的核心求职分析能力应共享 `AgentRunService` 或其下游 workflow。
