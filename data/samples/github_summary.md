# GitHub 仓库摘要

> 说明：本文档为脱敏示例，描述了一个典型 AI 应用开发者的 GitHub 仓库概况。

## 仓库列表

### 1. local-rag-knowledge-base
- URL: https://github.com/zhangsan-dev/local-rag-knowledge-base（示例）
- 语言: Python
- Stars: 45
- 描述: 基于 LangChain + Chroma 的本地知识库 RAG 问答系统。支持 Markdown 和 PDF 文档上传，向量检索，引用来源展示。使用 Streamlit 搭建前端。
- 技术栈: Python, LangChain, Chroma, FastAPI, Streamlit, Docker
- 用户贡献:
  - 全部代码（独立开发）
  - 设计并实现了 RAG pipeline（Loader → Chunker → Embedder → Retriever）
  - 实现了 query rewriting 和 rerank 优化检索质量
  - 编写了 README 和快速开始指南
- 适配岗位方向: AI 应用开发、RAG 工程师、后端开发

### 2. multi-agent-task-planner
- URL: https://github.com/zhangsan-dev/multi-agent-task-planner（示例）
- 语言: Python
- Stars: 28
- 描述: 基于 LangGraph 的多 Agent 协作任务管理原型。包含规划 Agent、执行 Agent、审查 Agent，支持任务分解、状态追踪和错误恢复。
- 技术栈: Python, LangGraph, OpenAI API, Pydantic
- 用户贡献:
  - 核心开发者，负责 Agent 状态设计和 LangGraph 集成
  - 实现了条件边和 checkpoint 持久化
  - 设计并执行了 20 个测试用例的评估
- 适配岗位方向: AI Agent 开发、多 Agent 系统

### 3. github-profile-analyzer
- URL: https://github.com/zhangsan-dev/github-profile-analyzer（示例）
- 语言: Python
- Stars: 12
- 描述: 自动分析 GitHub 用户仓库，提取项目摘要和技术栈，生成结构化 Markdown 文档。
- 技术栈: Python, GitHub API, Markdown
- 用户贡献:
  - 全部代码（独立开发）
  - 设计了项目摘要提取的 prompt 模板
  - 实现了 API 缓存避免 rate limit
- 适配岗位方向: 工具开发、API 集成

### 4. fastapi-microservice-template
- URL: https://github.com/zhangsan-dev/fastapi-microservice-template（示例）
- 语言: Python
- Stars: 8
- 描述: FastAPI 微服务项目模板，包含项目结构、配置管理、错误处理、日志、Docker 部署。
- 技术栈: Python, FastAPI, Docker, SQLAlchemy
- 用户贡献:
  - 全部代码（独立开发）
  - 编写了完整的项目文档和使用指南
- 适配岗位方向: 后端开发

### 5. leetcode-solutions
- URL: https://github.com/zhangsan-dev/leetcode-solutions（示例）
- 语言: Python / C++
- Stars: 5
- 描述: 个人 LeetCode 刷题记录，200+ 题解，按数据结构和算法分类。
- 技术栈: Python, C++, 算法
- 适配岗位方向: 通用软件工程
