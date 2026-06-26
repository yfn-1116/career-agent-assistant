# 基于证据约束的智能实习投递 Agent

> 毕业答辩 PPT 素材

---

## 一、开发流程（1 页）

```
项目定位 → 需求分析 → 模块设计 → 技术选型 → Vibe Coding 实现 → 测试验证
```

| 阶段 | 内容 |
|---|---|
| 项目定位 | 一个"不能说谎"的求职 Agent — Evidence-Grounded |
| 需求分析 | 用户上传资料 → 粘贴 JD → 匹配分析 → 生成简历建议/话术 |
| 模块设计 | PPAM 认知架构：Perception → Planning → Action → Memory |
| 技术选型 | LangGraph + BM25 + Qwen Embedding + RRF + CrossEncoder |
| 实现 | 85 个 Python 模块 + Streamlit UI + FastAPI |
| 测试 | **693 passed, 0 failed** |

---

## 二、需求分析（1 页）

| 痛点 | 现有方案 | 我们的方案 |
|---|---|---|
| 投递前不确定是否匹配 | 人工逐条看 JD | 自动解析 JD → 匹配技能 → 匹配度 % |
| 简历不敢乱写经历 | 抄模板或瞎编 | 只从知识库检索真实经历，区分"实现了/设计了/计划中" |
| 和 HR 不知道怎么聊 | 百度搜模板 | 基于匹配结果生成个性化话术 |

### MVP 范围
- ✅ 上传 PDF/DOCX/MD → 自动分块入库
- ✅ 粘贴 JD → 解析 → 检索经历 → 匹配分析
- ✅ 生成简历 bullet（可直接写入/需确认/仅参考）
- ✅ 生成 BOSS 沟通话术
- ✅ GitHub 仓库拉取（MCP）

### 非目标
- ❌ 不自动投递、不爬取网站、不多用户系统

---

## 三、系统整体运行逻辑（1 页）

```
用户："帮我分析这个 JD：AI Agent 实习生，要求 Python RAG..."
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│  LLM 收到用户消息 + 看到 16 个可用 Tool 列表                   │
│                                                              │
│  LLM 自主推理：                                                 │
│  "用户给了 JD → 调 parse_jd 解析                              │
│   → 调 retrieve_profile 检索经历                              │
│   → 调 analyze_match 做匹配                                   │
│   → 调 check_faithfulness 验证"                               │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  系统执行 LLM 决定的 Tool 调用序列                              │
│                                                              │
│  parse_jd          → JDParserAgent → ParsedJD               │
│  retrieve_profile  → BM25+Emb+RRF+CrossEncoder → 5 evidence │
│  analyze_match     → strengths/weaknesses/gaps              │
│  generate_answer   → 简历 bullet + 沟通话术                   │
│  check_faithfulness → Evidence Gate → pass/reject            │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
                    最终输出：
          匹配度 74% | 5 条简历建议 | BOSS 话术
```

---

## 四、整体架构：PPAM 认知 Agent（1 页）

```
用户输入 → Perception → Planning → Action → 输出
               │            │          │
               └────────────┴──────────┘
                        │
                     Memory
```

| 组件 | 包 | 一句话 | 核心能力 |
|---|---|---|---|
| **Perception** | `perception/` | 看懂世界 | LLM 调用 Skill/MCP 解析 PDF/JD/GitHub |
| **Planning** | `planning/` | 决定做什么 | LLM 自主循环 + 16 个 Tool 列表 |
| **Action** | `action/` | 干活 | Skill + MCP + SubAgent + RAG Pipeline |
| **Memory** | `memory/` | 记住一切 | 短时(20条) + 长时(JSONL) + 知识库 |

**RAG 是贯穿层：Perception 写入 → Memory 存储 → Action 检索**

---

## 五、Perception 感知层（2 页）

**所属：PPAM 的 Perception 层。LLM 自主调用 Skill/MCP 解析外部输入。**

```
用户输入
    │
    ├── JD 文本 → LLM 调 parse_jd Skill → ParsedJD
    │               agents/jd_parser.py
    │
    ├── PDF/DOCX → LLM 调文件解析 Skill → 纯文本 → chunk → Memory
    │               rag/loaders/file_loader.py → TextChunker → JSONL
    │
    └── GitHub 链接 → LLM 调 MCP github → README → chunk → Memory
                       infrastructure/mcp_client.py → npx server-github
```

| 感知能力 | 类型 | 技术 |
|---|---|---|
| JD 文本解析 | Skill (Python) | JDParserAgent：规则 + LLM 双路径 |
| PDF/DOCX 读取 | Skill (Python) | pypdf / python-docx → TextChunker |
| GitHub 仓库拉取 | MCP (外部) | @modelcontextprotocol/server-github |
| 互联网搜索 | Skill (Python) | DuckDuckGo |

**数据流：所有感知结果最终都写入 Memory（chunks.jsonl + conversations.jsonl）**

---

## 六、Planning 规划层（2 页）

**所属：PPAM 的 Planning 层。LLM 看到 16 个 Tool → 自己决定执行顺序。**

```
System Prompt 列出 16 个 Tool：
  - parse_jd: 解析岗位 JD 文本，当用户粘贴招聘信息时触发
  - retrieve_profile: 从知识库检索经历，当需要查找用户技能时触发
  - github: GitHub 操作工具，当用户粘贴 GitHub 链接时触发
  - analyze_match: 对比 JD 与用户证据，判断是否适合岗位
  - check_faithfulness: 验证生成内容有证据支撑，生成后自动触发
  - task_agent: 启动子 Agent 独立执行并行任务
  ...

LLM 看到用户消息后自主推理 → 输出 tool_call JSON → 系统执行 → 结果追加到对话 → 继续循环
```

**循环逻辑（agents/autonomous_agent.py:56）：**

```
for step in range(max_steps):
    ① LLM 看历史对话 + 工具列表 → 返回 tool_call 或最终答案
    ② 如果是 tool_call → 执行 → 追加结果 → continue
    ③ 如果是普通文本 → 最终答案 → break
```

---

## 七、Action 执行层（4 页）★ 重点

**所属：PPAM 的 Action 层。三层扩展 + RAG Pipeline + Evidence Gate。**

### 7.1 三层扩展机制

```
Action 层
├── Skill（内置 Python） 15 个 Tool，ToolRegistry 统一管理
├── MCP（外部服务）     github, resuml, 可无限扩展
└── SubAgent（并行）     task_agent, LLM 自主 spawn
```

### 7.2 RAG Pipeline（Action 层核心检索链路）

```
用户查询 → jieba 分词 → BM25 (top80) + Qwen Embedding (top80)
    → RRF 融合 (k=60) → CrossEncoder 精排 (bge-reranker-base) → top5
    → FaithfulnessChecker → EvidenceGate → LLM 生成
```

### 7.3 Evidence Gate（独有创新）

| 证据状态 | 简历权限 | 例子 |
|---|---|---|
| implemented | ✅ 可直接写入 | "实现了 Agent workflow" |
| designed | ⚠️ 需降级 | "实现了 MCP" → "设计了 MCP 方案" |
| planned | ❌ 阻止 | 不生成简历 bullet |

---

## 八、Memory 记忆层（1 页）

**所属：PPAM 的 Memory 层。跨 Perception 和 Action 共享。**

```
Perception ──→ Memory ──→ Action
 (写入)        (存储)      (读取)

三层记忆体系：
  短时记忆：内存列表（最近 20 条）→ LLM 上下文窗口
  长时记忆：conversations.jsonl → BM25 检索历史对话
  知识库：  chunks.jsonl → 完整 RAG Pipeline 检索
```

---

## 九、模块连接关系（1 页）

```
┌─────────────────────────────────────────────────────────┐
│                      Streamlit UI                        │
│                  Chat Input → 意图路由                    │
└────────────────────────┬────────────────────────────────┘
                         │ orchestrator.handle(text)
                         ▼
┌─────────────────────────────────────────────────────────┐
│               OrchestratorAgent (总控)                   │
│                                                         │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐           │
│   │Perception│──→│ Planning │──→│  Action  │           │
│   └────┬─────┘   └──────────┘   └────┬─────┘           │
│        │                             │                  │
│        │    ┌──────────┐             │                  │
│        └───→│  Memory  │←────────────┘                  │
│             └──────────┘                                │
└─────────────────────────────────────────────────────────┘

各层连接方式：
  Perception → Memory：  FileLoader/TextChunker → chunks.jsonl
  Memory → Action：      BM25 + Embedding + RRF + CrossEncoder 检索
  Action → Memory：      生成结果 → conversations.jsonl
  Planning → Action：    LLM tool_call → ToolRegistry.invoke()
  Perception → Planning：意图/关键词 → LLM system prompt 上下文
```

---

## 十、对比 OpenCode（1 页）

| | OpenCode（通用） | 本系统（垂直） |
|---|---|---|
| 决策 | LLM 自主 ✅ | LLM 自主 ✅ |
| Tool 注册 | 10 tools | 15 Skill + 1 MCP |
| Agent-as-Tool | ✅ | ✅ TaskAgentTool |
| MCP 支持 | ✅ | ✅ |
| **RAG Pipeline** | ❌ | ✅ BM25+Emb+RRF+CE |
| **Evidence Gate** | ❌ | ✅ 四阶段约束 |

---

## 十一、测试与部署（1 页）

| 指标 | 数值 |
|---|---|
| 测试 | **693 passed, 0 failed** |
| 模型 | 3 本地 + 2 API + 2 MCP |
| 部署 | `docker compose up -d` |

---

> 详细代码路径见 `defense_speaker_notes.md`
> RAG 流程图见 `rag_pipeline_flow.md`
> PPAM 详解见 `ppam_architecture.md`
