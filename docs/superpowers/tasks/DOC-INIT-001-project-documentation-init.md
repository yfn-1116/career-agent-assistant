# DOC-INIT-001 初始化项目文档体系

## 任务编号

DOC-INIT-001

## 建议执行者

Codex

## 任务目标

从空仓库初始化中文项目文档体系、AI 协作规范和基础目录骨架。

## 允许修改文件

- `README.md`
- `AGENTS.md`
- `.gitignore`
- `.env.example`
- `documents/`
- `docs/superpowers/`
- `src/.gitkeep`
- `tests/.gitkeep`
- `data/samples/.gitkeep`
- `outputs/demo/.gitkeep`

## 禁止修改文件

- 业务代码。
- RAG 实现。
- Agent 实现。
- frontend/backend/server 目录。
- 依赖配置文件。

## 输入

- 用户提供的 Phase 0 初始化要求。

## 输出

- 中文 `documents/` 文档体系。
- `docs/superpowers/` Agent 执行规范体系。
- 根目录入口文档和协作规则。
- 基础目录占位。

## 实现要求

- 所有 Markdown 使用中文。
- 不实现业务代码。
- 不引入依赖。

## 验收标准

- 指定目录和文件全部存在。
- Markdown 文档均为中文内容。
- 项目日志和规划已更新。

## 测试命令

```bash
git status --short
find . -path './.git' -prune -o -name '*.md' -type f -empty -print
find . -path './.git' -prune -o -type d \( -name frontend -o -name backend -o -name server \) -print
```

## 提交信息建议

```text
chore: initialize Chinese documentation system and agent workflow rules
```
