# Agent 上下文控制

## 问题描述

多个 Agent 如果共享过多上下文，可能出现信息污染、重复引用、错误传播和 prompt 过长。

## 风险影响

- Agent 输出不稳定。
- 生成内容混入无关项目。
- 成本和响应时间上升。
- 错误难以定位。

## 初步解决策略

- 使用 `AgentTaskState` 明确字段。
- 每个 Agent 只读取必要字段。
- 检索证据和最终生成内容分离保存。
- 每个任务卡明确 Agent 边界。

## 第一阶段处理方式

四个核心 Agent 按固定顺序执行，不做递归和复杂分支。上下文只通过 `parsed_jd`、`retrieved_evidence`、`match_analysis`、`generated_output` 等字段传递。

## 后续优化方向

- 引入 LangGraph 节点状态。
- 增加节点级 trace。
- 增加 ReviewAgent 对输出进行复核。

## 后续维护规则

新增 Agent 前必须说明它读取和写入哪些状态字段。
