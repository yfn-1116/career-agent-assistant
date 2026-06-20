# 项目文档体系初始化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: 执行本计划前必须阅读 `AGENTS.md`，并通过任务卡确认允许修改范围。步骤使用 checkbox 语法便于执行记录。

**Goal:** 初始化中文文档体系、Agent 执行规范和基础目录骨架，不实现业务代码。

**Architecture:** 本阶段采用文档先行结构：`documents/` 服务于人类理解和项目沉淀，`docs/superpowers/` 服务于 AI Agent 执行，根目录文档提供入口和协作规则。业务代码目录仅保留占位。

**Tech Stack:** Markdown、Git、基础目录结构；不引入业务依赖。

---

## 文件范围

### 允许创建或修改

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

### 禁止创建或修改

- `frontend/`
- `backend/`
- `server/`
- RAG 实现代码
- Agent workflow 实现代码
- 依赖锁文件和依赖配置

## 执行步骤

- [x] 检查 `git status`，确认初始状态。
- [x] 创建 `documents/` 分层文档目录。
- [x] 创建 `docs/superpowers/` 规格、计划、任务和复盘目录。
- [x] 创建根目录项目入口和协作规范。
- [x] 创建基础目录占位。
- [x] 更新 `documents/97-journal.md`。
- [x] 更新 `documents/99-project-planning.md`。
- [x] 运行最终结构检查和 `git status`。

## 验证方式

- 检查要求中的文件路径全部存在。
- 检查 Markdown 文档为中文且非空。
- 确认未创建 frontend、backend、server 目录。
- 确认未引入业务依赖和业务代码。

## 后续维护规则

- 本计划只服务于 `DOC-INIT-001`。
- 后续实现任务不得复用本计划扩大范围。
