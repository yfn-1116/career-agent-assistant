"""Career Agent Assistant project — fully implemented, high confidence."""
from __future__ import annotations

from career_agent.profile.schema import ProfileItem, STATUS_IMPLEMENTED


def make_item() -> ProfileItem:
    return ProfileItem(
        item_id="proj-career-agent-assistant",
        source_path="github/career-agent-assistant/README.md",
        source_type="github_repo",
        title="智能投递辅助 Agent（Career Agent Assistant）",
        project_name="career-agent-assistant",
        skills=[
            "Python", "RAG", "LangGraph", "LangChain", "FastAPI",
            "Chroma", "Streamlit", "DeepSeek API", "Qwen API",
            "Evidence Gate", "Prompt Engineering", "Tool Calling",
            "retriever", "reranker", "faithfulness checker",
            "pytest", "document processing", "chunking", "embedding",
        ],
        claims=[
            "独立开发基于 RAG 的智能投递辅助 Agent",
            "实现 Evidence Gate 防止编造经历",
            "搭建 LangGraph 多 Agent 协作流程",
            "构建 Hybrid 检索系统（关键词 + embedding 融合）",
            "开发 Chat-first Streamlit 前端",
        ],
        status=STATUS_IMPLEMENTED,
        confidence=0.95,
        raw_content="""# 智能投递辅助 Agent

基于证据约束的智能求职匹配 Agent。支持 JD 解析、RAG 检索、
匹配分析、简历 bullet 生成和 HR 沟通话术生成。

## 技术栈
- Python + FastAPI + Streamlit
- LangGraph 多 Agent workflow
- Hybrid 检索（MemoryVectorStore + EmbeddingVectorStore）
- Evidence Gate 保证不编造经历

## 核心能力
- 解析岗位 JD → 结构化 ParsedJD
- RAG 检索用户资料库 → evidence
- 匹配分析 → strengths/weaknesses/gaps
- 生成简历建议 + HR 沟通话术
""",
        metadata={
            "source_url": "https://github.com/yfn-1116/career-agent-assistant",
            "tags": ["agent", "rag", "langgraph", "fastapi", "full-stack"],
            "stars": 0,
            "language": "Python",
        },
    )
