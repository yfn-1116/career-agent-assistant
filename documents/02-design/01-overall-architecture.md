# 总体架构设计

## 用途

本文档描述第一阶段整体架构边界和模块协作方式。

## 架构定位

第一阶段不是完整求职平台，也不是普通简历生成网页，而是面向大学生实习求职场景的 RAG + 多 Agent 原型系统。

## 第一阶段链路

```text
本地用户资料 Markdown
-> RAG 检索
-> JD 解析
-> 匹配分析
-> 简历项目描述 / 沟通话术生成
-> Markdown 或 Streamlit 展示
```

## 模块划分

### 资料层

存放本地 Markdown 用户资料、项目经历、GitHub 仓库摘要、技能与实习经历、示例 JD。第一阶段不做多用户数据隔离和复杂数据库。

### RAG 层

负责加载 Markdown、切分文本、建立检索索引、返回带来源的证据。第一阶段需要保留 `VectorStore` 接口，避免后续从内存方案切换到 Chroma / FAISS 时影响上层 Agent。

### Agent 层

第一阶段只包含四个核心 Agent：

- `JDParserAgent`：解析岗位 JD。
- `RAGRetrieveAgent`：基于岗位要求检索用户资料。
- `MatchAnalysisAgent`：分析岗位要求和用户经历的匹配关系。
- `BuildAgent`：基于证据和分析生成最终 Markdown 输出。

### Orchestrator 层

第一阶段可以先使用普通 Python workflow 或轻量状态流串联 Agent。后续当状态分支、失败恢复和可视化调试需求变强时，再切换到 LangGraph。

### 展示层

第一阶段优先 CLI + Markdown 输出，随后扩展 Streamlit 轻量展示。完整 FastAPI + Web 前端分离架构放到第二阶段。

## 当前状态

当前只有文档设计，没有业务实现。

## 后续维护规则

- 新模块必须先写任务卡。
- 不允许在 demo 层重新实现 RAG 或 Agent 逻辑。
- 集成任务由 Codex 负责，局部实现任务可交给 Claude Code + DeepSeek。

## ARCH-003 代码结构决策

第一阶段最终采用 `src/career_agent/` 作为 Python package。RAG、Agent、Workflow、Models、Evaluation、Utils 都放在该 package 下，测试按模块放在 `tests/` 下。

第一阶段不创建 `frontend/`、`backend/`、`server/`、`app/`、`scripts/`，不创建完整前后端架构。CLI 和 Streamlit demo 放在仓库根目录的 `demo/cli/` 与 `demo/streamlit/`，并且只能调用 workflow。
