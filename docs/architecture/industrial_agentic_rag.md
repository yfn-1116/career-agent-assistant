# Industrial Agentic RAG：架构设计

## 项目定位

面向大学生实习投递场景的智能投递辅助 Agent。非自动投递机器人，不做平台爬虫。
核心链路：解析 JD → 检索用户经历 → 评估证据质量 → 生成有来源的简历 bullet / 沟通话术 → 输出诊断报告。

## Phase 1 能力边界（已完成）

| 能力 | 实现 | 局限性 |
|------|------|--------|
| 文档加载 | MarkdownProfileLoader | 仅 Markdown |
| 文本切分 | TextChunker (800/100) | 固定窗口 |
| 关键词检索 | MemoryVectorStore | 独立使用 |
| 语义检索 | QwenEmbeddingProvider + EmbeddingVectorStore | 独立使用 |
| RAG Pipeline | RAGPipeline | 单次检索 |
| 检索评分 | grade_retrieval() 5 维度 | 规则型 |
| JD 解析 | JDParserAgent (规则+LLM) | — |
| 匹配分析 | MatchAnalysisAgent | 规则型 |
| 输出生成 | BuildAgent | 模板型 |
| LangGraph | 7 节点线性 StateGraph | 无条件分支 |
| CLI/Streamlit | 可用 | 展示层 |

## Phase 2 工业级升级目标

从"线性 RAG demo"升级为"可解释、可评分、可重试、可扩展工具调用的 Agentic RAG 系统"。

## 分层架构

```
┌──────────────────────────────────────────────┐
│              interface 层                     │
│  CLI (demo/cli/)    Streamlit (demo/streamlit/)│
│  API routes (future)                          │
│  只调用 graph / application，不操作 RAG 细节    │
└────────────────────┬─────────────────────────┘
                     │
┌────────────────────▼─────────────────────────┐
│              graph 层                         │
│  LangGraph StateGraph                         │
│  nodes → 调用 application use case            │
│  edges → 条件分支控制                          │
│  不放复杂业务逻辑                              │
└────────────────────┬─────────────────────────┘
                     │
┌────────────────────▼─────────────────────────┐
│           application 层                      │
│  业务用例和编排逻辑                            │
│  parse_jd_use_case                            │
│  plan_queries_use_case                        │
│  retrieve_evidence_use_case                   │
│  grade_retrieval_use_case                     │
│  rerank_chunks_use_case                       │
│  select_evidence_use_case                     │
│  generate_resume_use_case                     │
│  check_faithfulness_use_case                  │
│  write_report_use_case                        │
└────────────────────┬─────────────────────────┘
                     │
┌────────────────────▼─────────────────────────┐
│           infrastructure 层                   │
│  具体实现，可替换                              │
│  markdown loader | chunker | embedding provider│
│  vector store | hybrid retriever | reranker    │
│  LLM provider | report writer | diagnostics    │
└────────────────────┬─────────────────────────┘
                     │
┌────────────────────▼─────────────────────────┐
│              domain 层                         │
│  纯数据模型，零依赖                            │
│  JobDescription | ParsedJD | DocumentChunk     │
│  RetrievalQuery | RetrievedChunk | Evidence    │
│  RetrievalScore | MatchAnalysis               │
│  GeneratedBullet | AgentDecision              │
│  ToolCallTrace | WorkflowTrace                │
└──────────────────────────────────────────────┘
```

### 依赖方向

```
interface → graph → application → infrastructure → domain
                   application → domain
                   infrastructure → domain
```

上层可以依赖下层，下层**绝不**依赖上层。domain 层不依赖任何其他层。

## RAG Pipeline 图

```
                    ┌──────────────┐
                    │  JD 文本输入  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  parse_jd    │ → ParsedJD
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ plan_queries │ → [RetrievalQuery, ...]
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
     ┌────────▼───┐ ┌──────▼──────┐    │
     │ keyword    │ │ embedding   │    │
     │ retriever  │ │ retriever   │    │
     └────────┬───┘ └──────┬──────┘    │
              │            │            │
              └────────────┼────────────┘
                           │
                    ┌──────▼───────┐
                    │ hybrid fuse  │ → 分数归一化 + 融合
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  reranker    │ → 重排序 + rerank_reason
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ grade        │ → RetrievalScore
                    └──────┬───────┘
                           │
                    ┌──────┴───────┐
                    │ score >= 0.65│
                    └──────┬───────┘
                      yes  │  no
                    ┌──────┐ ┌──────────┐
                    │ 继续 │ │ retry < 3│
                    └──┬───┘ └────┬─────┘
                       │      yes │  │ no
                       │  ┌───────┘  │
                       │  │  ┌───────┘
                       │  │  │
                       │  │  │  ┌──────────┐
                       │  │  └──► fallback │
                       │  │     └──────────┘
                       │  │
                       │  └────► rewrite_query → 回到检索
                       │
                ┌──────▼───────┐
                │ 生成 + 校验   │
                └──────────────┘
```

## Agent Workflow 图

```
START
  │
  ▼
parse_jd ───────────────────── JDParserAgent / parse_jd_use_case
  │
  ▼
plan_queries ───────────────── 生成初始 queries
  │
  ▼
retrieve ───────────────────── Hybrid RAG (keyword + vector)
  │
  ▼
rerank ─────────────────────── Reranker
  │
  ▼
grade ──────────────────────── RetrievalScore
  │
  ├── score >= 0.65 ──────────► select_evidence
  │
  ├── score < 0.65 ───────────► rewrite_query ──► retrieve (loop)
  │    retry < max
  │
  └── retry >= max ───────────► fallback ──► END (safe exit)
  │
  ▼
select_evidence ─────────────── 选最 relevant 的 evidence
  │
  ▼
generate ───────────────────── BuildAgent / generate_resume_use_case
  │
  ▼
check_faithfulness ─────────── FaithfulnessChecker
  │
  ├── pass ───────────────────► write_report
  │
  └── fail ───────────────────► mark revise_required
  │
  ▼
write_report ───────────────── Markdown + JSON diagnostics
  │
  ▼
END
```

## 数据流

```
User (JD text)
  │
  ▼
[parse] → ParsedJD
  │
  ▼
[plan] → [RetrievalQuery]
  │
  ▼
[retrieve] → [RetrievedChunk]  ← keyword + embedding results
  │
  ▼
[rerank] → [RetrievedChunk]    ← rerank_score, rerank_reason
  │
  ▼
[grade] → RetrievalScore       ← 5-dimension grading
  │
  ├── pass → [select_evidence] → [Evidence]
  │                                │
  │                                ▼
  │                          [generate] → [GeneratedBullet]
  │                                │
  │                                ▼
  │                          [check] → FaithfulnessReport
  │                                │
  │                                ▼
  │                          [write] → report.md + diagnostics.json
  │
  └── retry → [rewrite_query] → 回到 retrieve
```

## 错误处理策略

| 层级 | 错误类型 | 策略 |
|------|---------|------|
| domain | schema validation | raise clear error, log |
| infrastructure | embedding API fail | 回退到 keyword-only |
| infrastructure | vector store fail | 回退到 MemoryVectorStore |
| application | retrieval 返回空 | mark grade=failed, trigger retry |
| application | LLM generate fail | 回退到 template-based |
| application | faithfulness fail | mark revise_required, 不输出 |
| graph | node exception | 写 error_message, 进入 fallback |
| interface | demo crash | 捕获异常, 显示友好错误 |

## 可观测性策略

- 每次运行生成 `outputs/diagnostics/{trace_id}.json`
- 每次 tool call 记录 `ToolCallTrace`
- LangGraph node 执行生成 `WorkflowTrace`
- RAG 每轮检索记录 `retry_history`
- 最终报告含 source mapping

## Evaluation 策略

- 离线 eval dataset：`data/eval/jd_cases.jsonl`（8+ JD）
- 指标：Hit@K, MRR, Skill Coverage, Source Precision, Faithfulness Pass Rate
- 规则型 grading 作为 baseline，后续可接 LLM judge
- 不要求在线 A/B

## Security / Safety 边界

- 不自动发送任何内容到外部平台
- 不操作浏览器或模拟用户行为
- LLM 调用仅做文本分析和生成，不做代码执行
- 不在生成内容中编造用户没有的经历
- 所有生成内容标记 evidence source
