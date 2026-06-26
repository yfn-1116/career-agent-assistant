"""AI application intern JD fixture."""
from __future__ import annotations

from career_agent.domain.schemas import ParsedJD


def make_jd() -> ParsedJD:
    return ParsedJD(
        job_title="AI 应用开发实习生",
        job_direction="ai_application",
        hard_skills=[
            "Python", "LLM", "API", "Streamlit", "Gradio",
        ],
        bonus_skills=[
            "RAG", "Prompt Engineering", "Docker", "GitHub Actions",
            "数据库",
        ],
        soft_skills=["业务理解", "独立开发", "沟通"],
        keywords=[
            "LLM", "Python", "API", "Streamlit", "Gradio",
            "RAG", "Prompt", "Docker", "部署", "大模型应用",
        ],
        raw_text="""# 岗位 JD：AI 应用开发实习生

## 基本信息
- 公司：ZZ 创新科技（AI 应用方向，50 人）
- 岗位：AI 应用开发实习生
- 地点：杭州
- 类型：实习（每周 4 天以上，至少 2 个月）

## 岗位职责
1. 参与公司 AI 产品的 Demo 快速搭建和迭代
2. 基于 LLM API 开发面向用户的应用功能
3. 使用 Streamlit 或 Gradio 搭建产品 prototype
4. 参与产品需求的 AI 化方案设计

## 任职要求
1. 熟练使用 Python，能快速搭建 Web Demo
2. 了解 LLM API 的基本使用方式
3. 有 Streamlit 或 Gradio 的使用经验
4. 能独立完成从需求到 Demo 的开发

## 加分项
- 了解 RAG 的基本概念
- 有 Docker 和 CI/CD 经验
- 对产品和用户体验有感知""",
    )
