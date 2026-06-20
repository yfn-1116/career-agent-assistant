# Agent 执行规范目录

## 用途

本目录服务于 AI Agent 执行任务，不是普通项目介绍文档。所有执行任务都应先进入 `specs/`、`plans/` 或 `tasks/`，再进入代码或文档修改。

## 目录职责

- `specs/`：记录阶段规格和边界。
- `plans/`：记录可执行计划和验证方式。
- `tasks/`：记录可分配给具体 Agent 的任务卡。
- `reviews/`：记录任务完成后的范围复核。

## 当前状态

Phase 1 已补强架构边界和后续任务卡。后续实现必须按任务卡分批推进。

## Agent 分工

- Codex：核心架构、核心接口、schema、workflow 集成、疑难修复。
- Claude Code + DeepSeek：边界清晰的局部实现、文档补全、样例数据、测试和 demo。
- ChatGPT + User：方案判断、任务拆分、需求确认。

## 后续维护规则

- 每个任务卡必须声明允许修改和禁止修改的文件。
- 同一时间只能有一个执行 Agent 写仓库。
- 执行任务前必须查看 `git status`。
- 执行后必须更新 journal 和 project planning。
