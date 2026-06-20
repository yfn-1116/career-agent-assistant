# 展示流程

## 用途

本文档记录从项目介绍到能力演示再到总结的展示流程，适用于答辩、实习面试展示或课程展示。

## 第一阶段展示路径

```text
问题引入（1min）
→ 技术路线（1min）
→ 文档体系（1min）
→ RAG MVP（2min）
→ Agent Workflow（2min）
→ CLI Demo 现场运行（2min）
→ 输出解读（2min）
→ 后续扩展（1min）
```

总计约 12 分钟。

## 详细流程

### 1. 问题引入（1 分钟）

**要讲的内容**：
- 找实习时面对多份 JD，需要反复翻自己的项目文档回忆哪些经历能对上
- 手动匹配效率低，容易遗漏经历
- 需要一个工具把经历文档化 + 自动匹配

**展示内容**：无代码演示，口头说明问题。

### 2. 技术路线（1 分钟）

**要讲的内容**：
- RAG（检索增强生成）：把个人经历存为知识库，用 JD 关键词检索最相关的经历片段
- Multi-Agent：JD 解析、证据检索、匹配分析、输出生成，各司其职
- 第一阶段不调用大模型，用规则和模板保证可复现

**展示内容**：口头讲解 + 架构图（可为 Mermaid 或手绘）。

### 3. 文档体系（1 分钟）

**要讲的内容**：
- 项目采用"文档先行"的开发方式
- 设计文档、技术决策、任务卡、运行手册分层组织
- 多 AI 协作规范：任务卡声明边界，独立 commit

**展示内容**：展示 `documents/` 目录结构。

### 4. RAG MVP（2 分钟）

**要讲的内容**：
- 五层 RAG pipeline：Loader → Chunker → VectorStore → Retriever → Pipeline
- 每层独立可替换
- 当前使用内存关键词检索，后续可换 Chroma / FAISS

**展示内容**：
```bash
PYTHONPATH=src pytest tests/rag -v
# 展示 61 个 RAG 测试全部通过
```

### 5. Agent Workflow（2 分钟）

**要讲的内容**：
- 四个 Agent：JDParser → RAGRetrieve → MatchAnalysis → Build
- 共享状态 AgentTaskState，每个 Agent 只读写自己负责的字段
- Workflow 串联整条链路

**展示内容**：
```bash
PYTHONPATH=src pytest tests/agents tests/workflows -v
# 展示 79 个 Agent + Workflow 测试全部通过
```

### 6. CLI Demo 现场运行（2 分钟）

```bash
PYTHONPATH=src python demo/cli/run_job_match_demo.py
```

终端实时显示运行状态。

### 7. 输出解读（2 分钟）

打开 `outputs/demo/job_match_result.md`，逐段讲解：

1. JD 解析结果 → 关键词提取
2. RAG 检索证据 → 证据溯源
3. 匹配分析 → strengths / weaknesses
4. 生成输出 → 简历 bullet + 沟通话术
5. 运行说明 → 不调用外部模型

### 8. 后续扩展（1 分钟）

**要讲的内容**：
- 接入 DeepSeek / OpenAI API 升级匹配质量
- Streamlit 可视化展示
- 支持更多文档格式（GitHub API、JSON Resume）
- 支持多轮交互
- 可能的部署方式

**不要讲的内容**：
- 尚未实现的功能当做已完成
- 过度的技术承诺

## 兜底方案

如果现场环境出现以下问题，使用预案：

| 问题 | 预案 |
|---|---|
| 模型不可用 | 提前保存的 `outputs/demo/job_match_result.md` 直接展示 |
| pytest 找不到 | 提前截图测试结果 |
| 路径问题 | 提前 `cd` 到项目根目录并确认 |
| 终端编码问题 | 用 `less` 或编辑器打开 Markdown |

## 当前状态

CLI demo 已实现，上述展示流程可完整执行。Streamlit demo 尚未开发，暂不演示。

## 后续维护规则

- 展示流程变化需要同步更新评估文档
- 新增功能后更新 demo 脚本和展示时间
- Streamlit 展示必须基于已有 workflow 输出
