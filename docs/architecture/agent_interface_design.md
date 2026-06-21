# Agent Interface Design — Codex-like Conversational UI

## 产品定位

面向大学生实习求职的**对话式 Agent**。

**是**：
- 帮助用户理解岗位、匹配经历、优化简历、生成沟通话术的智能助手
- 输入 JD 或问题，Agent 自动检索分析，给出有证据支持的回答
- 底层工业级 RAG/Agent，表层极简交互

**不是**：
- 自动投递机器人
- 平台爬虫
- 复杂管理后台
- 简历生成器网站

## 核心交互模型

类似 Codex / Claude Code 的 Agent 交互：

```
┌──────────────────────────────────────────┐
│  Smart Apply Agent                       │
│  ─────────────────────────────────────── │
│                                          │
│  🤖 我帮你分析了这个岗位...               │
│                                          │
│  岗位核心要求：                           │
│  1. RAG / 知识库应用                      │
│  2. Agent 工作流                          │
│  ...                                     │
│                                          │
│  你的匹配度：中高                         │
│                                          │
│  ✅ 优势：                                │
│  - 你有智能投递辅助 Agent 项目            │
│  ...                                     │
│                                          │
│  ⚠️ 短板：                                │
│  - MCP 经验还停留在设计阶段               │
│  ...                                     │
│                                          │
│  📝 建议简历 bullet：                     │
│  > 基于 LangGraph 构建...                │
│                                          │
│  💬 HR 沟通话术：                         │
│  > 您好，我对这个岗位很感兴趣...           │
│                                          │
│  ┌─ 📋 查看详情 ─────────────────────┐   │
│  │  ▸ Parsed JD                       │   │
│  │  ▸ 检索结果 (Top-5)                 │   │
│  │  ▸ Hybrid Scores                   │   │
│  │  ▸ Rerank Reasons                  │   │
│  │  ▸ 检索评分                         │   │
│  │  ▸ Retry History                   │   │
│  │  ▸ Tool Trace                      │   │
│  │  ▸ Faithfulness Check              │   │
│  │  ▸ Source Mapping                  │   │
│  │  ▸ Diagnostics JSON                │   │
│  └────────────────────────────────────┘   │
│                                          │
│  ─────────────────────────────────────── │
│  📎 粘贴 JD 或输入问题...                  │
│  [Ask Agent]                             │
└──────────────────────────────────────────┘
```

## 主要用户流程

### 场景 1：分析岗位匹配度
```
用户: 粘贴 JD + "我匹配这个岗位吗？"
Agent:
  1. 正在解析岗位需求...
  2. 正在检索你的项目经历...
  3. 正在评估匹配度...
  4. 正在生成建议...
  → 输出匹配分析 + 改进建议
```

### 场景 2：生成简历 bullet
```
用户: "帮我把这个岗位对应的项目经历改写一下"
Agent:
  1. 解析 JD...
  2. 检索相关项目...
  3. 生成有证据支持的 bullet...
  4. 检查真实性...
  → 输出简历 bullet + 证据来源
```

### 场景 3：生成沟通话术
```
用户: "帮我写一段联系 HR 的话"
Agent:
  1. 分析岗位要点...
  2. 匹配你的优势...
  3. 生成话术...
  → 输出沟通话术（100 字以内）
```

## UI 布局

### 推荐实现：Streamlit

| 区域 | 内容 | 默认 |
|------|------|------|
| 顶部 | 标题 "Smart Apply Agent" + 一句话说明 | 可见 |
| 主区域 | Agent 对话（问题和回答） | 可见 |
| 底部 | 输入框 + Ask Agent 按钮 | 可见 |
| 展开区 | 证据详情、RAG 评分、trace、diagnostics | 折叠 |

### 不做

- ❌ 复杂 sidebar 导航
- ❌ 多页面切换
- ❌ 仪表盘图表
- ❌ 配置表单
- ❌ 多用户管理

## Agent 回答格式

### 必须包含（默认可见）

```
1. 岗位核心要求（3-5 条）
2. 匹配度判断（高/中高/中/低）
3. 你的优势（每条有证据）
4. 你的短板（诚实标注未覆盖的技能）
5. 简历修改建议（可操作的 bullet）
6. 沟通话术（1 段）
7. 证据来源（文件列表）
8. 下一步建议
```

### 可选展开（技术细节）

```
- Parsed JD（结构化解析结果）
- Queries（检索查询列表）
- Top-K Evidence（每条含 hybrid scores）
- Retrieval Scores（5 维度评分）
- Rerank Reasons
- Retry History（每轮 query + score + decision）
- Tool Trace（每个 tool 的执行记录）
- Faithfulness Check（unsupported claims）
- Source Mapping（每条 bullet → evidence）
- Diagnostics JSON path
```

### 风格要求

- 使用中文输出
- 像求职助手，不像技术日志
- 不编造经历
- 每一条 conclusion 有证据支持
- 不确定的地方诚实标注

## LLM 集成边界

### LLM 可以做的

- 结构化解析 JD（提取技能、方向）
- Query rewrite（基于 missing keywords 生成新查询）
- 匹配分析（总结 strengths/weaknesses）
- 生成回答（用自然语言组织结论）
- Faithfulness check（判断生成内容是否有证据）

### LLM 不可以做的

- 凭空编造用户经历
- 绕过 evidence 直接生成简历
- 直接执行任意工具
- 修改文件或配置

### 回退策略

如果 LLM 不可用：回退到规则实现，在 UI 中标注 "规则模式（未使用 LLM）"。

## Agent Run Service

UI 不直接拼流程。所有请求通过统一入口：

```
AgentRunService.run(request) → AgentRunResult
```

Input: user_message, raw_jd, mode (analyze/resume/chat)
Output: final_answer, match_summary, generated_bullets, communication_script,
        evidence_sources, retrieval_scores, trace_id, report_path,
        diagnostics_path, warnings

UI 只负责展示，不负责编排。
