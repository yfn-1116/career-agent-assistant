# 简历表达参考

> 以下内容供写简历时参考，请根据实际经历调整。

## 项目名称

**career-agent-assistant** — 基于 RAG + 多 Agent 的实习投递智能辅助原型

## 一句话概述

独立设计并实现了一个融合 RAG 检索增强生成与多 Agent 协作的实习岗位匹配分析工具，支持 CLI 和 Streamlit 双模式展示，165 个自动化测试全部通过。

## 可选的简历 bullet

### 侧重 RAG

- 设计并实现了完整的 RAG pipeline（Loader → Chunker → VectorStore → Retriever → Pipeline），支持 Markdown 文档加载、文本分块、向量检索和证据溯源
- 基于抽象接口设计 VectorStore，支持内存关键词检索（当前）和语义检索（预留 Chroma/FAISS 接入）

### 侧重 Agent

- 设计并实现了 4 个协作文档 Agent（JD 解析、证据检索、匹配分析、输出生成），基于共享状态 `AgentTaskState` 进行状态传递，每个 Agent 职责边界清晰
- 使用纯规则和模板实现（第一阶段），架构接口已预留 LLM API 接入位置

### 侧重工程

- 采用文档先行开发流程：设计文档 → 技术决策 → 任务卡 → 代码实现，完整记录了 20+ 个任务的执行日志
- 编写了 165 个自动化测试（pytest），覆盖 RAG/Agent/Workflow/Demo 全栈，全部通过
- 支持 CLI（argparse + Markdown 报告）和 Streamlit 两种展示方式

### 侧重架构

- 调研了 LangGraph、Dify、RAGFlow、Flowise、DeerFlow、OpenHands、Khoj 等 8 个开源项目，沉淀了详细的对比分析文档和架构决策记录
- 设计了可扩展的 RAG schema（ProfileItem → ProfileDocument → DocumentChunk → RetrievedEvidence），支持完整的数据溯源

## 技术栈（用于简历技能栏）

`Python` `RAG` `Multi-Agent` `Streamlit` `pytest` `Markdown` `Git` `文档工程`

## 不要写的内容

- ❌ "精通 RAG / Agent"（这是原型项目）
- ❌ "上线生产环境"（没有部署为服务）
- ❌ "接入 LLM 实现智能匹配"（当前是规则型）
- ❌ "支持自动投递"（没有这个功能）

## 面试时怎么讲

1. **问题**：找实习时手动匹配 JD 效率低
2. **方案**：把经历文档化，用 RAG 检索 + Agent 分析
3. **实现**：RAG pipeline + 4 Agent + Workflow 编排
4. **亮点**：证据溯源、零外部依赖、165 测试
5. **不足**：关键词检索 → 后续换 Embedding；规则分析 → 后续接 LLM
