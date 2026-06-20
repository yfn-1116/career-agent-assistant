# 多 AI 协作规则

## 用途

本文档定义 `career-agent-assistant` 仓库内多个 AI 协作时的职责边界、执行流程和禁止事项。所有执行 Agent 在开始任务前必须阅读本文档。

## 角色分工

1. ChatGPT 负责架构讨论、方案判断、任务拆分、提示词生成，不直接作为仓库执行 Agent。
2. Codex 是主架构与核心实现 Agent，优先处理复杂架构、核心接口、RAG/Agent 集成、疑难修复。
3. Claude Code + DeepSeek 可以承担工作量较大的具体任务，包括文档补全、样例数据、局部模块实现、测试补充、runbook、demo，但必须严格遵守任务边界。

## 执行前规则

- 所有执行任务必须先有 `docs/superpowers/plans/` 或 `docs/superpowers/tasks/` 下的任务说明。
- 每个任务必须声明允许修改的文件和禁止修改的文件。
- 同一时间只能有一个执行 Agent 对仓库进行写入。
- 执行任务前必须查看 `git status`，确认是否存在未处理变更。

## 执行后规则

- 执行任务后必须更新 `documents/97-journal.md`。
- 执行任务后必须更新 `documents/99-project-planning.md`。
- 任务完成后需要说明实际修改范围、验证方式和遗留风险。

## 架构保护规则

- 没有明确授权，不允许修改全局架构、核心 schema、workflow 集成和技术选型。
- 不允许在一次任务中同时修改 RAG、Agent、Demo、部署多个大模块。
- 不允许为了完成局部任务而引入新的主框架、数据库、向量库或模型供应商。

## 当前状态

当前仓库处于 Phase 0：文档体系与 AI 协作规范初始化阶段。业务代码、RAG、Agent workflow、前端页面和部署脚本尚未实现。

## 后续维护规则

- 如果新增 Agent 类型，需要先在本文档中明确职责边界。
- 如果新增任务类型，需要同步更新 `docs/superpowers/tasks/README.md`。
- 如果协作规则和任务文件冲突，以更具体的任务文件为准；如果任务文件和用户明确指令冲突，以用户明确指令为准。
