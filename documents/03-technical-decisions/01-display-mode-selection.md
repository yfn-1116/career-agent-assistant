# 展示方式选择

## 用途

本文档比较 CLI、Streamlit、FastAPI + Web 前端三种展示方式，并确定第一阶段展示策略。

## 候选方案

### CLI + Markdown 输出

优点：

- 稳定，适合先验证 RAG 和 Agent 核心链路。
- 开发成本低，不需要额外前端工程。
- 适合本地调试、日志追踪和学校服务器命令行复现。
- 输出 Markdown 便于保存、对比和展示。

缺点：

- 交互体验较弱。
- 不适合作为最终对外产品形态。

### Streamlit

优点：

- 展示成本低，适合学校服务器演示。
- 可以快速展示输入 JD、检索证据、匹配分析和最终输出。
- 不需要完整前后端分离。

缺点：

- 不应承载核心业务逻辑。
- 复杂交互和工程化能力有限。

### FastAPI + Web 前端

优点：

- 更适合第二阶段服务化和长期扩展。
- 可以承载多用户、账号、任务记录和更完整 UI。

缺点：

- 第一阶段成本过高。
- 会把重点从 RAG + Agent 编排转移到 Web CRUD 和部署。

## 决策

第一阶段采用 CLI + Markdown 输出，随后扩展 Streamlit 轻量展示。FastAPI + Web 前端分离作为第二阶段扩展。

## 原因

1. 项目核心是 RAG 和 Agent 编排，不是 Web CRUD。
2. CLI 更稳定，适合先测试核心链路。
3. Streamlit 展示成本低，适合学校服务器展示。
4. FastAPI + 前端分离应在核心链路稳定后再引入。

## 后续维护规则

- `DEMO-001` 负责 CLI demo。
- `DEMO-002` 负责 Streamlit demo。
- 不允许在第一阶段新增 frontend/backend/server 目录。

## ARCH-003 决策补充

第一阶段 demo 层采用：

- `demo/cli/`：CLI demo，优先实现。
- `demo/streamlit/`：Streamlit 轻量展示，第二步实现。

不采用 `app/streamlit_app.py`，因为 `app/` 容易演化成独立应用层或服务入口，不符合第一阶段“demo 只调用 workflow”的边界。
