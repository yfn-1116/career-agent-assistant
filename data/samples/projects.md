# 项目经历详情

> 说明：本文档为脱敏示例，补充 profile.md 中的项目细节，用于更精确的 RAG 检索。

## 项目 1：本地知识库 RAG 问答系统

### 项目背景
在实习和课程项目中，发现团队内部知识管理混乱——文档散落在不同平台，查找信息效率极低。因此开发了一个基于 RAG 的本地知识库问答系统。

### 技术架构
```
用户上传文档（Markdown / PDF）
  → Document Loader（LangChain）
  → Text Splitter（RecursiveCharacterTextSplitter）
  → Embedding（text-embedding-3-small）
  → Chroma VectorStore
  → Retrieval（相似度搜索 + MMR 多样性）
  → Rerank（Cross-Encoder）
  → LLM 生成（DeepSeek-Chat）
  → 返回答案 + 引用来源
```

### 核心实现
- **文档处理**：支持 Markdown 和 PDF 格式，使用 LangChain 的 Document Loader 统一接口
- **Chunk 策略**：chunk_size=500, chunk_overlap=50，按标题层级保留 section 信息
- **检索优化**：实现了 query rewriting（用 LLM 扩展查询）和 MMR（最大边际相关性）检索
- **Rerank**：使用 bge-reranker-base 对 top-20 结果重排序，取 top-5 送入 LLM
- **引用追溯**：每个 chunk 保留 source 和 position 信息，回答中标注引用来源

### 技术栈细节
- LangChain: Document loaders, text splitters, chains
- Chroma: 本地向量存储，持久化到磁盘
- FastAPI: 提供 REST API（/upload, /query, /documents）
- Streamlit: 前端展示，支持多轮对话和来源高亮

### 成果
- 在 500+ 份技术文档的测试集上，答案准确率 85%（人工评估）
- 单次查询端到端延迟 < 3 秒
- 代码开源在 GitHub（示例地址）

---

## 项目 2：多 Agent 协作任务管理原型

### 项目背景
课程大作业，探索多 Agent 在任务规划场景中的应用。核心问题是：单个 LLM 在处理复杂任务时容易遗漏步骤或产生幻觉，多 Agent 协作能否改善？

### Agent 设计
```
PlannerAgent: 分析用户输入 → 拆解为子任务列表 → 确定执行顺序
ExecutorAgent: 执行单个子任务 → 返回执行结果
ReviewerAgent: 检查执行结果 → 判断是否通过 → 决定重试或继续
```

### 状态设计
```python
class TaskState:
    user_input: str
    subtasks: list[SubTask]
    current_task_index: int
    execution_results: dict
    review_feedback: list
    final_output: str
    errors: list
```

### 核心实现
- 使用 LangGraph 的 StateGraph 构建 Agent 工作流
- Planner 和 Reviewer 使用 GPT-4，Executor 使用 GPT-3.5（降低延迟）
- 条件边：Reviewer 判断不通过 → 返回 Executor 重试（最多 3 次）
- Checkpoint：每个节点执行后保存状态，支持中断恢复

### 技术栈细节
- LangGraph: StateGraph, checkpoint, conditional edges
- OpenAI API: GPT-4 + GPT-3.5
- Python dataclass: 状态建模

### 成果
- 在 20 个测试任务（行程规划、报告撰写、数据分析）上，多 Agent 方案完成率 90%，单 Agent 方案 60%
- 错误恢复机制使任务失败率降低 50%

---

## 项目 3：GitHub 项目分析工具

### 项目背景
找实习时需要整理自己的 GitHub 项目经历，手动翻仓库很耗时。开发了一个自动分析工具。

### 功能
- 输入 GitHub 用户名，拉取所有公开仓库
- 按语言、star 数、更新时间排序
- 提取 README 摘要、技术栈、项目亮点
- 生成结构化的 Markdown 项目经历文档

### 技术实现
- 使用 GitHub REST API（PyGithub）
- 缓存 API 响应避免 rate limit
- 用简单的规则 + LLM 提取项目描述和亮点
- 输出可直接粘贴到简历或面试准备文档

### 成果
- 分析了自己的 15 个公开仓库，生成了一份 2000 字的项目经历文档
- 帮助在面试中更系统地介绍自己的项目
