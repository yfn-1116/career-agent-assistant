# Demo 文档目录

## 用途

本目录组织第一阶段 demo 的脚本、数据说明和展示流程。

## 应放内容

- CLI demo 操作流程。
- Streamlit 轻量展示流程。
- 固定示例资料和示例 JD 的说明。
- 演示失败时的兜底方案。

## 当前状态

Phase 1 明确 demo 应先保证 CLI + Markdown 输出稳定，再扩展 Streamlit 展示。当前没有业务代码或页面实现。

## 后续维护规则

- Demo 文档不实现业务逻辑。
- Demo 必须对应可复现的固定输入。
- Streamlit 只调用已有 workflow，不在页面内写核心 RAG 或 Agent 逻辑。
