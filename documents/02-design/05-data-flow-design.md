# 数据流设计

## 用途

本文档说明第一阶段从用户输入到最终展示的完整数据流，以及每一步的输入、输出和边界。

## 主流程

```text
用户输入 JD
-> JDParserAgent 解析岗位
-> RAGRetrieveAgent 检索用户资料
-> MatchAnalysisAgent 生成匹配分析
-> BuildAgent 生成最终输出
-> 输出 Markdown / Streamlit 展示
```

## 步骤一：用户输入 JD

- 输入：岗位 JD 文本或 Markdown。
- 输出：写入 `AgentTaskState.job_description`。
- 边界：第一阶段不自动爬取岗位网站。

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
- Streamlit：读取 workflow 输出并展示，不承载核心业务逻辑。

## 失败路径

- JD 解析失败：返回错误提示和原始 JD 检查建议。
- 检索证据不足：提示需要补充资料，而不是强行生成。
- 生成内容缺少证据：进入 review 或标记为需要人工确认。

## 当前状态

当前只定义数据流，不实现数据处理代码。

## 后续维护规则

- 新增 Agent 必须说明在数据流中的位置。
- 展示层不得绕过 workflow 直接调用底层 RAG。

## ARCH-003 代码结构决策

第一阶段数据流由 `src/career_agent/workflows/job_match_workflow.py` 串联。CLI 和 Streamlit demo 必须调用该 workflow，不允许在 demo 层重新实现 JD 解析、RAG 检索、匹配分析或输出生成。

`demo/cli/` 负责命令行入口，`demo/streamlit/` 负责轻量页面展示。两者共享同一个 workflow 输出。
