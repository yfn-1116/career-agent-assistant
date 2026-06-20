# DOC-DESIGN-001 补充设计文档

## 用途

本任务用于补充 RAG 与多 Agent 设计文档，但不写代码。

## 当前状态

状态：TODO。

## 建议 Executor

Claude Code + DeepSeek，需基于 ChatGPT 方案或 Codex 已确认的架构输入。

## 允许修改

- `documents/02-design/`
- `documents/04-challenges/`
- `documents/05-evaluation/`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改

- `src/`
- `tests/`
- `.env.example`
- 依赖配置

## 验收标准

- 设计文档说明模块边界、输入输出和风险。
- 不引入具体实现代码。

## 后续维护规则

涉及核心 schema 的结论必须交给 Codex 复核。
