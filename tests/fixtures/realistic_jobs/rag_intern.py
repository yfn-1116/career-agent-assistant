"""RAG engineer intern JD fixture."""
from __future__ import annotations

from career_agent.domain.schemas import ParsedJD


def make_jd() -> ParsedJD:
    return ParsedJD(
        job_title="RAG 应用开发实习生",
        job_direction="rag",
        hard_skills=[
            "Python", "RAG", "向量数据库", "Chroma", "FAISS",
            "embedding", "检索", "LLM",
        ],
        bonus_skills=[
            "LangChain", "LangGraph", "reranker", "Prompt Engineering",
            "Docker", "FastAPI",
        ],
        soft_skills=["文档", "业务理解", "学习能力"],
        keywords=[
            "RAG", "embedding", "向量数据库", "Chroma", "FAISS",
            "检索", "retriever", "LangChain", "Python", "LLM",
            "Prompt Engineering", "Docker",
        ],
        raw_text="""# 岗位 JD：RAG 应用开发实习生

## 基本信息
- 公司：YY 科技（知识库与智能问答方向）
- 岗位：RAG 应用开发实习生
- 地点：北京
- 类型：实习（每周 3 天以上）

## 岗位职责
1. 参与公司 RAG 知识库系统的检索模块开发
2. 优化 embedding 模型选型和向量数据库配置
3. 实现检索结果的重排序（rerank）模块
4. 参与文档分块策略（chunking）的设计与调优
5. 编写检索质量评估脚本

## 任职要求
1. 了解 RAG（检索增强生成）系统的完整链路
2. 掌握 Python，熟悉数据处理
3. 了解向量数据库（Chroma、FAISS、Milvus 等）
4. 了解 embedding 模型的基本概念
5. 了解常见的检索评估指标（recall、MRR 等）

## 加分项
- 使用过 LangChain 或 LlamaIndex
- 有检索系统或搜索引擎相关经验
- 了解 Prompt Engineering
- 对文档解析（PDF、DOCX）有实际经验""",
    )
