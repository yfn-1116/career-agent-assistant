# LangGraph 选择

## 用途

本文档记录是否以及何时引入 LangGraph 作为多 Agent 编排框架。

## 为什么项目适合 LangGraph

本项目天然包含多个节点：JD 解析、RAG 检索、匹配分析、输出生成、后续复核和展示。随着功能增长，节点状态、失败恢复、可观测性和分支流程会变得重要，LangGraph 适合管理这类状态驱动的 Agent workflow。

## 为什么第一阶段可以先用普通 workflow

第一阶段只有四个核心 Agent，流程固定，目标是验证核心业务链路。如果一开始引入 LangGraph，可能增加依赖、学习成本和调试复杂度。先用普通 Python workflow 或轻量状态流更利于快速验证。

## 什么时候切换到 LangGraph

满足以下条件时再切换：

- `AgentTaskState` 字段稳定。
- 四个核心 Agent 的输入输出边界稳定。
- 需要 ReviewAgent、人审节点或错误恢复分支。
- 需要可视化或节点级 trace。

## LangGraph 对 AgentTaskState 的意义

`AgentTaskState` 可以作为 LangGraph 共享状态的基础。每个节点只读取必要字段并写入自己的输出字段，降低上下文混乱风险。

## 决策

第一阶段先不强制使用 LangGraph，但设计上保留 LangGraph 迁移路径。`WORKFLOW-001` 由 Codex 负责评估是否进入 LangGraph。

## 后续维护规则

- 不允许局部 Agent 任务私自引入 LangGraph。
- 引入前必须更新 workflow 设计和运行手册。
