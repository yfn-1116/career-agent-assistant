# 设计文档目录

## 用途

本目录记录第一阶段核心架构设计，包括总体架构、RAG 模块、多 Agent 编排、Agent 状态、数据流、GitHub 仓库摘要策略和参考架构草案。

## 应放内容

- 模块职责和边界。
- 输入输出契约。
- 第一阶段实现范围与后续扩展点。
- 与任务卡对应的设计依据。
- 从开源项目调研转化出的本项目架构建议。

## 当前状态

Phase 1 已明确：第一阶段采用 CLI + Markdown 输出优先，Streamlit 轻量展示随后扩展；核心模块为 RAG 用户资料知识库和四个核心 Agent。ARCH-002 补充了参考架构启发文档。

## 重点文档

- `07-reference-inspired-architecture.md`：基于 LangGraph、RAGFlow、DeerFlow、OpenHands、Khoj、Flowise 等项目调研形成的本项目代码结构草案。

## 后续维护规则

- 核心 schema 和 workflow 变更必须由 Codex 或明确授权任务维护。
- 设计文档不直接写业务代码。
- 设计变化需要同步更新技术决策和任务卡。
- 参考架构草案不等于立即创建代码目录，目录创建必须进入后续实现任务。
