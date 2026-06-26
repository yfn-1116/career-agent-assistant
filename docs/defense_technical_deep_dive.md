# 基于证据约束的智能实习投递 Agent

> 毕业答辩 PPT 素材 · PPAM 认知 Agent 架构

---

## 一、项目定位

| 是 | 不是 |
|---|---|
| 基于个人知识库的求职匹配分析 | 自动投递机器人 / GPT 包装壳 |
| 所有声称有据可查（Evidence-Grounded） | 简历生成器（编造经历） |

**一句话：** 一个"不能说谎"的求职助手。

---

## 二、系统架构：PPAM 认知 Agent

按认知 Agent 四组件（PPAM）设计，代码按层组织：

```
用户输入 → Perception → Planning → Action → 输出
               │            │          │
               └────────────┴──────────┘
                        │
                     Memory

RAG 是贯穿层 —— Perception 写入、Memory 存储、Action 检索
```

| 组件 | 包 | 一句话 | 核心能力 |
|---|---|---|---|
| **Perception** | `perception/` | 看懂世界 | LLM 自主调用 Skill/MCP 解析 PDF/JD/GitHub |
| **Planning** | `planning/` | 决定做什么 | LLM 自主循环 + LangGraph DAG + 16 个 Tool |
| **Action** | `action/` | 干活 | Skill 内置 + MCP 外部 + SubAgent 并行 |
| **Memory** | `memory/` | 记住一切 | 短时(20条) + 长时(JSONL+BM25) + 知识库 |

### 贯穿层：RAG

```
Perception → FileLoader → chunks.jsonl (Memory) → BM25+Embedding+RRF+CrossEncoder (Action)
```

RAG 不是单独一层——它横跨三层。Perception 负责写入知识库，Memory 负责持久化，Action 负责检索和利用。

---

## 三、Perception（感知层）

**LLM 自主调用 Skill/MCP 来"看懂"外部信息，处理完自动进 Memory。**

```
用户输入
    │
    ├── "这是 JD 文本" → LLM 调 parse_jd skill → ParsedJD → Memory
    │
    ├── "这是 PDF 简历" → LLM 调文件解析 skill → 纯文本 → chunk → Memory
    │
    └── "这是 GitHub 链接" → LLM 调 MCP github → README → chunk → Memory
```

| 感知能力 | 实现方式 | 技术 |
|---|---|---|
| JD 文本解析 | Skill: `parse_jd` | JDParserAgent（规则+LLM 双路径） |
| PDF/DOCX 读取 | Skill: 文件加载 | pypdf / python-docx |
| GitHub 仓库拉取 | MCP: `@modelcontextprotocol/server-github` | GitHub API + raw.githubusercontent |
| 互联网搜索 | Skill: `web_search` | DuckDuckGo |

---

## 四、Planning（规划层）

**LLM 自主决策循环：LLM 看 16 个 Tool 列表 → 自己决定先做什么后做什么。**

```
用户消息
    │
    ▼
LLM (Qwen-Plus / DeepSeek)
    │
    │  System Prompt 里列出了 16 个 Tool 的 name + description
    │  LLM 自己推理：
    │    "用户给了 JD + GitHub 链接，我应该：
    │     ① parse_jd 解析岗位
    │     ② github_repo 拉取项目
    │     ③ retrieve_profile 检索经历
    │     ④ analyze_match 做匹配
    │     ⑤ check_faithfulness 验证
    │     ⑥ 给出最终答案"
    │
    ├── tool_call: parse_jd(text="...")     → ParsedJD
    ├── tool_call: github_repo(repo="...")   → README
    ├── tool_call: retrieve_profile(query)   → 5 evidence
    ├── tool_call: analyze_match(jd, ev)     → strengths/weaknesses
    ├── tool_call: check_faithfulness(...)    → pass
    └── "匹配度 74%，建议调整简历后投递..."  ← 最终回答
```

**后退模式：** LLM 不可用时，回退到 LangGraph 确定性 DAG（10 节点固定流水线）。

---

## 五、Action（执行层）

**16 个内置 Skill + MCP 外部服务 + SubAgent 并行模式。**

### 5.1 内置 Skill（16 个）

| 类别 | Tool | 触发条件 |
|---|---|---|
| 感知 | `parse_jd` | 用户粘贴招聘信息 |
| 感知 | `github_repo` | 用户粘贴 GitHub 链接 |
| 感知 | `web_search` | 用户询问公司背景 |
| 检索 | `retrieve_profile` | 需要查找用户经历 |
| 检索 | `rerank_chunks` | 检索完成后精排 |
| 检索 | `grade_retrieval` | 5 维度评估检索质量 |
| 分析 | `analyze_match` | 判断用户是否适合岗位 |
| 生成 | `generate_grounded_answer` | 输出简历建议/话术 |
| 验证 | `check_faithfulness` | 生成后自动验证 |
| 安全 | `fallback` | 检索耗尽时兜底 |
| 工具 | `write_report` / `write_diagnostics` | 写诊断报告 |
| 并行 | **`task_agent`** | **spawn 子 Agent 独立执行** |

### 5.2 MCP 外部服务

| MCP Server | 命令 | 提供能力 |
|---|---|---|
| GitHub | `npx @modelcontextprotocol/server-github` | 搜索仓库/读文件/创建 Issue |
| resuml | `npx resuml mcp` | 简历 YAML 定义/渲染/ATS 评分/PDF 导出 |

```
Action 层扩展 = 注册 Skill（写 Python）+ 连 MCP（外部服务）+ spawn SubAgent（并行）
能力无限扩展，不需要改框架代码。
```

### 5.3 RAG Pipeline（贯穿层核心）

```
用户查询 → jieba 分词 → BM25 (top80) + Qwen Embedding (top80)
    → RRF 融合 (k=60) → CrossEncoder 精排 → top5
    → FaithfulnessChecker → EvidenceGate → LLM 生成
```

### 5.4 Evidence Gate（独有创新）

| 证据状态 | 简历权限 | 例子 |
|---|---|---|
| implemented | ✅ 可直接写入 | "实现了 Agent workflow" |
| designed | ⚠️ 需降级 | "实现了 MCP" → "设计了 MCP 方案" |
| planned | ❌ 阻止 | 不生成简历 bullet |

---

## 六、Memory（记忆层）

```python
from career_agent.memory import ConversationMemory, KnowledgeBaseService
```

| 层 | 怎么存 | 怎么查 | 作用 |
|---|---|---|---|
| 短时记忆 | 内存列表（最近 20 条） | 顺序读 | LLM 上下文 |
| 长时记忆 | `conversations.jsonl` | BM25 检索 | 跨会话回忆 |
| 知识库 | `chunks.jsonl` | BM25+Emb+RRF+CE | 证据支撑 |

---

## 七、对比 OpenCode

| | OpenCode（通用 Agent） | 本系统（垂直 Agent） |
|---|---|---|
| 决策方式 | LLM 自主 | LLM 自主 ✅ |
| Tool 注册 | 10 tools | 16 tools ✅ |
| Agent-as-Tool | ✅ `agentTool` | ✅ `TaskAgentTool` |
| MCP 支持 | ✅ | ✅ |
| **RAG Pipeline** | ❌ 只有 Sourcegraph 搜索 | ✅ BM25+Emb+RRF+CrossEncoder |
| **Evidence Gate** | ❌ | ✅ 四阶段证据约束 |
| **PPAM 认知架构** | ❌ 无显式建模 | ✅ Perception-Planning-Action-Memory |

---

## 八、测试与部署

| 指标 | 数值 |
|---|---|
| 测试用例 | **693 passed, 0 failed** |
| 支持格式 | PDF / DOCX / MD / TXT |
| 模型数 | 3 本地 + 2 API + 2 MCP |
| 部署 | `docker compose up -d` 一键启动 |

---

## 九、答辩常见问题

**Q1: 和 ChatGPT 有什么区别？** 
A: Evidence Gate 保证不编造——planned 的经历不会被写进简历。

**Q2: RAG 为什么设计成这样？**
A: 参考红楼梦 Boss Baseline（BM25+Embedding→RRF→Reranker），RAG 是贯穿 Perception-Memory-Action 的跨层能力。

**Q3: Agent 怎么决策的？**
A: LLM 自主循环——System Prompt 列 16 个 Tool，LLM 自己决定调用顺序。不可用时回退 LangGraph DAG。

**Q4: 和 OpenCode 有什么关系？**
A: 参考了它的 Tool 注册 + Agent-as-Tool + MCP 模式。但加了 Evidence Gate（他没用）和工业级 RAG Pipeline（他只有 Sourcegraph 搜索）。

---

> 详细技术手册：`defense_speaker_notes.md` · RAG 流程图：`rag_pipeline_flow.md`
> PPAM 详解：`ppam_architecture.md` · Evidence 设计：`evidence_design.md`
