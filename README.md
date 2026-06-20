# career-agent-assistant

## 项目定位

`career-agent-assistant` 是一个面向大学生实习求职场景的 RAG + 多 Agent 原型系统。它不是完整求职平台，也不是普通简历生成器，而是用来验证个人能力知识库、岗位理解、匹配分析和求职材料生成这一条核心链路。

## 核心模块

- RAG 用户资料知识库：将本地 Markdown 简历、项目经历、GitHub 仓库摘要、课程项目、实习经历、技能材料等整理为可检索资料。
- 多 Agent 编排：围绕 JD 解析、资料检索、匹配分析、简历项目描述生成、HR / mentor 沟通话术生成等任务拆分职责。
- 文档先行工程流程：所有实现任务先进入 `documents/` 和 `docs/superpowers/`，再进入代码实现。
- 本地开发到服务器展示：本地验证后推送 GitHub，再由学校服务器拉取并复现 demo。

## 第一阶段目标

第一阶段跑通以下链路：

```text
本地用户资料 Markdown
-> RAG 检索
-> JD 解析
-> 匹配分析
-> 简历项目描述 / 沟通话术生成
-> Markdown 或 Streamlit 展示
```

第一阶段优先采用 CLI + Markdown 输出，随后扩展 Streamlit 轻量展示。暂不做完整 frontend/backend/server 分离架构。

## 当前状态

项目已完成 Phase 0：中文文档体系、AI 协作规范和基础目录骨架初始化。当前进入 Phase 1：核心架构边界、模块设计文档与后续任务卡补强。仓库尚未实现业务代码。

## 后续开发流程

后续开发遵循：

```text
文档设计
-> specs / plans / tasks
-> RAG schema
-> RAG pipeline
-> AgentTaskState
-> 核心 Agent
-> workflow 集成
-> CLI demo
-> Streamlit demo
-> GitHub 同步
-> 学校服务器部署展示
```

## 协作规则

- Codex 负责核心架构、核心接口、RAG / Agent 集成和疑难修复。
- Claude Code + DeepSeek 负责边界清晰的文档补全、样例数据、局部模块、测试和 demo。
- ChatGPT + User 负责方案讨论、任务拆分和需求确认。
- 所有执行任务必须先有 `docs/superpowers/plans/` 或 `docs/superpowers/tasks/` 下的任务说明。
