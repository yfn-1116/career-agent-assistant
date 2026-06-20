# 个人能力资料

> 说明：本文档为脱敏示例，用于 RAG 检索验证和 Demo 展示。所有信息均为虚构。

## 基本信息

- 姓名：张三（示例）
- 学校：XX 大学 计算机科学与技术 2025 届本科
- 求职方向：AI Agent / 大模型应用 实习
- 期望城市：北京 / 深圳
- GitHub：https://github.com/zhangsan-dev（示例）

## 技术能力

### 编程语言
- Python（熟练）：3 年使用经验，主要用 FastAPI、LangChain、数据处理
- TypeScript / JavaScript（了解）：可完成简单前端页面开发
- SQL：熟悉基本查询和数据库设计
- C++：课程项目中使用过，读得懂代码

### 框架与工具
- LangChain / LangGraph：使用 LangChain 构建过 RAG 问答系统，了解 LangGraph 的 StateGraph 概念
- FastAPI：独立开发过 3 个后端 API 项目
- Streamlit：开发过 2 个 AI 工具 demo
- Docker：能编写 Dockerfile 和 docker-compose
- Git / GitHub Actions：日常使用，配置过 CI 流程

### AI / LLM 相关
- 熟悉 RAG（检索增强生成）原理和实现
- 了解 Agent 的概念：工具调用、ReAct 模式、多 Agent 协作
- 使用过 OpenAI API、DeepSeek API
- 了解向量数据库（Chroma、FAISS）的基本使用
- 了解 Prompt Engineering 基础

### 基础知识
- 数据结构与算法（LeetCode 200+ 题）
- 操作系统、计算机网络基础
- 机器学习基础概念

## 项目经历

### 1. 本地知识库 RAG 问答系统
- 时间：2025.02 – 2025.04
- 角色：独立开发
- 技术栈：LangChain + Chroma + FastAPI + Streamlit
- 说明：
  - 基于 LangChain 构建了支持 Markdown、PDF 的本地知识库 RAG 系统
  - 使用 Chroma 作为向量数据库，实现了文档加载、文本切分、向量检索的完整 pipeline
  - 实现了 query rewriting 和 retrieval reranking 优化检索质量
  - 使用 Streamlit 搭建了前端，支持文档上传、问答交互和检索来源展示
- 亮点：
  - 检索命中率从初始 60% 提升到 85%（通过 chunk 策略和 rerank 优化）
  - 支持引用回溯，每个回答可以追溯到原文段落
  - 在 500+ 文档的测试集上，单次查询响应时间 < 3 秒

### 2. 多 Agent 协作任务管理原型
- 时间：2025.03 – 2025.05
- 角色：核心开发者
- 技术栈：Python + LangGraph + OpenAI API
- 说明：
  - 基于 LangGraph 构建了多 Agent 协作框架，包含规划 Agent、执行 Agent、审查 Agent
  - 实现了 Agent 间的状态传递和任务分解
  - 设计了任务状态追踪和错误恢复机制
- 亮点：
  - 规划 Agent 可将用户输入拆解为 2-5 个子任务
  - 执行失败时可自动触发重试或请求人工介入
  - 在 20 个测试任务上，多 Agent 方案的完成率比单 Agent 高 30%

### 3. GitHub 项目分析工具
- 时间：2024.10 – 2024.12
- 角色：独立开发
- 技术栈：Python + GitHub API + Markdown 生成
- 说明：
  - 分析用户 GitHub 仓库，提取项目描述、技术栈、贡献亮点
  - 自动生成项目经历摘要 Markdown，可用于简历或面试准备
  - 支持按语言、主题、star 数过滤和排序

## 实习经历

### XX 科技公司 — AI 应用开发实习生
- 时间：2024.07 – 2024.09
- 角色：后端开发实习生
- 工作内容：
  - 参与公司内部知识库系统的 RAG 模块开发，负责文档解析和向量检索部分
  - 使用 FastAPI 开发了 5 个内部 API 接口
  - 编写了 RAG 检索质量的自动化测试脚本
  - 参与 2 次模型切换（从 OpenAI 迁移到 DeepSeek），负责 API 适配和测试

## 教育经历

- XX 大学 计算机科学与技术 本科 2021.09 – 2025.06
- 相关课程：数据结构、算法设计、操作系统、计算机网络、数据库系统、机器学习、自然语言处理
- GPA：3.7 / 4.0

## 语言能力

- 英语：CET-6，能流畅阅读英文技术文档和论文
