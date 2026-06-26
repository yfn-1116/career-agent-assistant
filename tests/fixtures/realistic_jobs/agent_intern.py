"""Agent intern JD fixture."""
from __future__ import annotations

from career_agent.domain.schemas import ParsedJD


def make_jd() -> ParsedJD:
    return ParsedJD(
        job_title="AI Agent 开发实习生",
        job_direction="agent",
        hard_skills=[
            "Python", "LangGraph", "LangChain", "RAG", "LLM",
            "Agent 编排", "Tool Calling", "状态管理",
        ],
        bonus_skills=[
            "FastAPI", "Docker", "Prompt Engineering", "Streamlit",
            "MCP", "多 Agent",
        ],
        soft_skills=["沟通", "文档写作", "Git 协作", "工程化"],
        keywords=[
            "Agent", "LangGraph", "LangChain", "RAG", "LLM",
            "Tool Calling", "向量数据库", "Chroma", "FAISS",
            "Prompt", "Docker", "FastAPI", "Python",
        ],
        raw_text="""# 岗位 JD：AI Agent 开发实习生

## 基本信息
- 公司：XX 智能科技（AI 应用方向，约 200 人）
- 岗位：AI Agent 开发实习生
- 地点：深圳
- 类型：实习（每周 4 天以上，至少 3 个月）

## 岗位职责
1. 参与公司 AI Agent 平台的功能模块开发，包括 Agent 编排、工具调用、状态管理
2. 基于 LangChain / LangGraph 构建和优化多 Agent 协作流程
3. 参与 RAG 检索模块的开发和优化，提升召回率和准确率
4. 参与 Prompt 模板的设计与迭代
5. 编写单元测试和技术文档

## 任职要求
1. 计算机或相关专业本科及以上
2. 熟练掌握 Python，有 Web 后端或 AI 应用开发经验
3. 了解 RAG（检索增强生成）的基本原理，使用过 LangChain 或类似框架
4. 了解向量数据库（Chroma、FAISS 等）的基本使用
5. 了解 LLM API 调用（OpenAI / DeepSeek 等）
6. 了解 Git 和基本协作开发流程

## 加分项
- 有 Agent 或多 Agent 系统相关项目经验
- 了解 Prompt Engineering 和 LLM 评估方法
- 有 FastAPI / Streamlit 使用经验
- 了解 Docker 基本使用
- 有 GitHub 开源项目或技术博客者优先""",
    )
