# 简历项目描述

> 以下是几个不同场景的版本，根据投递方向选用。

## 一、简洁版（一句话）

独立开发基于 RAG + 多 Agent 的实习岗位匹配分析原型，实现完整的检索增强生成 pipeline 和 Agent 协作 workflow，支持 CLI/Streamlit 双模式展示，216 个自动化测试全部通过。

## 二、详细版（3-4 个 bullet）

- 设计并实现了完整的 RAG pipeline（Loader → Chunker → VectorStore → Retriever → Pipeline），支持 Markdown 文档加载、关键词检索和证据溯源，每层可独立替换
- 设计并实现了 4 个协作文档 Agent（JD 解析、证据检索、匹配分析、输出生成），基于共享状态 AgentTaskState 进行状态传递，职责边界清晰
- 实现了可选的 ModelProvider 抽象层（MockProvider / DeepSeekProvider），支持默认规则型运行或接入 LLM API 增强，失败时自动回退
- 编写了 216 个自动化测试（pytest），覆盖全栈模块；30+ 份技术文档；20+ 个独立 commit，历史可追溯

## 三、面向 Agent / AI 应用开发实习

- 独立开发基于 RAG + 多 Agent 的实习岗位智能匹配原型
- 实现 4 个协作 Agent（JD Parser / RAG Retrieve / Match Analysis / Build），共享状态管理对齐 LangGraph 设计
- 设计 ModelProvider 抽象接口，支持 MockProvider（测试）和 DeepSeekProvider（可选 LLM 增强）
- 实现完整证据溯源机制，每个输出 bullet 可追溯到用户原始资料段落
- 216 个自动化测试，覆盖 RAG/Agent/Workflow/Demo 全栈
- 支持 CLI 命令行和 Streamlit 可视化两种展示方式

## 四、面向后端 / AI 工程实习

- 独立设计并实现五层 RAG pipeline（Loader/Chunker/VectorStore/Retriever/Pipeline），接口抽象支持多后端替换
- 实现 4 个 Agent + 1 个 Workflow 编排系统，共享状态管理，严格模块边界
- 实现 ModelProvider 抽象层，支持 MockProvider（测试）和 DeepSeekProvider（真实 API），统一接口、失败回退
- 实现轻量输出质量评估模块，5 条规则 + 批量评估 runner，支持多 JD 横向对比
- 30+ 份技术文档（需求/设计/决策/运行手册/审查），文档先行开发流程
- 216 个自动化测试，零外部依赖，可离线运行

## 五、真实亮点（可以写的）

- ✅ 完整的 RAG pipeline 分层设计，每层可替换
- ✅ 多 Agent 协作 workflow，共享状态管理
- ✅ ModelProvider 抽象接口（MockProvider + DeepSeekProvider）
- ✅ 证据溯源，输出不编造经历
- ✅ 216 个自动化测试，零外部依赖
- ✅ CLI + Streamlit 双模式展示
- ✅ 多 JD 批量评估 runner
- ✅ 30+ 份技术文档，文档先行开发
- ✅ 多 AI 协作开发（Codex + Claude Code + DeepSeek）

## 六、不建议写的夸大表述

- ❌ "基于 LLM 的智能匹配系统"（当前默认规则型）
- ❌ "语义向量检索"（当前为关键词匹配）
- ❌ "基于 LangGraph 的 Agent 系统"（当前为普通 Python workflow）
- ❌ "生产级 AI 求职平台"（这是原型项目）
- ❌ "支持自动投递"（没有）
- ❌ "服务 XX 用户"（没有生产部署）
- ❌ "精通 RAG / Agent / LLM"（这是学习项目）

## 七、技术栈关键词（简历技能栏）

`Python` `RAG` `Multi-Agent` `Streamlit` `pytest` `Markdown` `Git` `文档工程` `ModelProvider 抽象`
