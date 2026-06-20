# 前后端取舍

## 用途

本文档明确第一阶段不做完整前后端分离的原因和后续扩展条件。

## 决策

第一阶段不做完整前后端，不创建 frontend、backend、server 目录。优先 CLI + Markdown 输出，再做 Streamlit 轻量展示。

## 原因

1. 核心技术不在前端，而在 RAG 和 Agent 编排。
2. 避免项目过早膨胀成 Web CRUD。
3. CLI / Streamlit 更适合快速展示 RAG + Agent 流程。
4. 学校服务器展示更需要稳定复现，而不是复杂部署。
5. 后续服务化时再补 FastAPI 和前端。

## 第二阶段可能引入

- FastAPI 服务层。
- 前端页面。
- 用户任务历史。
- 投递记录管理。
- 多用户资料隔离。

## 后续维护规则

- 任何 frontend/backend/server 目录新增都必须先通过新的技术决策和任务卡。
- Streamlit 页面只能作为展示层，不写核心业务逻辑。

## ARCH-003 决策补充

第一阶段明确不创建：

- `frontend/`
- `backend/`
- `server/`
- `app/`
- `scripts/`

Streamlit demo 放在 `demo/streamlit/`，CLI demo 放在 `demo/cli/`。FastAPI 服务化、前端页面和 server 目录留到第二阶段。
