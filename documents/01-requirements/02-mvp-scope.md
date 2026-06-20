# MVP 范围

## 用途

本文档定义第一阶段最小可用范围，确保项目先验证 RAG + 多 Agent 核心链路，而不是过早扩展成完整平台。

## 第一阶段必须做

1. 本地 Markdown 资料输入。
2. 示例 JD 输入。
3. RAG 检索相关经历。
4. JD 解析。
5. 匹配分析。
6. 简历项目描述生成。
7. HR / mentor 沟通话术生成。
8. Markdown 输出或轻量 Streamlit 展示。
9. 文档化运行流程，支持本地和学校服务器复现。

## 第一阶段推荐执行顺序

```text
样例资料
-> RAG schema
-> Markdown loader
-> chunking
-> VectorStore interface
-> RAG pipeline
-> AgentTaskState
-> 四个核心 Agent
-> workflow 集成
-> CLI demo
-> Streamlit demo
```

## 成功标准

输入一个示例 JD 后，系统能够解析岗位要求，从用户资料中检索相关经历，生成匹配分析，并输出一段不编造事实的简历项目描述或沟通话术。

## 当前状态

当前只完成需求和架构文档补强，尚未进入业务代码实现。

## 后续维护规则

- MVP 任务必须能被 demo 验证。
- 新增功能必须先判断是否影响核心链路。
- 不允许把第二阶段功能伪装成第一阶段必做内容。
