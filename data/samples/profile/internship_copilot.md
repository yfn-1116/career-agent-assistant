# Internship Copilot — 智能求职投递管家

## 项目概述

个人独立开发的全流程实习求职辅助 Agent。解决投简历效率低、岗位匹配靠手动、沟通话术需要重复组织的问题。

## 技术栈

Python, LangGraph, RAG, Chroma, Qwen LLM, Qwen Embedding, Streamlit, FastAPI, Docker, Git, pytest

## 已实现能力

### RAG 检索
- MarkdownProfileLoader 加载个人资料 (resume/projects/skills/internship/github_repos)
- TextChunker 文档切分 + QwenEmbeddingProvider 1024 维语义向量
- HybridRetriever: keyword + semantic 并行检索 + 分数融合 (0.40×vector + 0.35×keyword + 0.15×metadata + 0.10×priority)
- LightweightReranker: 5 信号重排序 (skill/source/specificity/length/dedup)
- RetrievalGrading: 5 维度评分 (count/score/coverage/diversity/traceability)

### Agent Workflow
- LangGraph StateGraph 管理 10 节点流程
- 条件分支: score >= 0.65 → analyze, score < 0.65 → retry rewrite_query, retry >= max → fallback
- 低分自动 retry, 耗尽后 fallback 不编造经历
- ToolRegistry: 15 个注册工具 + ControlledPlanner 规则型决策
- ToolCallTrace 全链路可观测

### Evidence Grounding
- Profile Knowledge Base: 区分 implemented/designed/planned/uncertain
- Evidence Gate: 阻止把"设计了"写成"实现了", 降级/阻止不合规 claims
- FaithfulnessChecker: 每条 bullet 必须有 evidence 支持

### Job Matching
- Job Matching Scorer: 5 因子评分 (skill_coverage + evidence_strength + project_relevance + source_confidence + gap_penalty)
- Hiring Intent Analyzer: 招聘意图分析 (JD具体度/技能一致性/风险信号)
- 岗位真实性验证问题自动生成

### 沟通 + 简历
- Message Agent: BOSS/邮件/微信/HR回复 4 种话术
- Resume Generator: 3 套模板 (default/minimal/full), markdown 输出
- Application Memory: JSONL 持久化投递记录

### Engineering
- 522 自动化测试
- Settings 集中配置, .env.example, Dockerfile, docker-compose
- Diagnostics JSON + Markdown 全链路报告
- Streamlit Codex-like 极简 UI
- Human Approval Gate: 所有发送动作必须用户确认

## 项目状态

当前为 V1 单岗位可用闭环。V2 批量筛选、V3 HR回复辅助、V4 浏览器辅助在 roadmap 中。

## 技术亮点

- 不是 GPT 包装壳: 长期个人资料库 + 自动检索 + evidence 溯源
- 每条建议绑定 source_path 和 claim_status
- 不编造经历: 证据不足时 fallback 而非虚构
- 工业级分层: domain/application/infrastructure/graph/interface
