"""Rule-based JD parser agent — no external model calls."""

import re

from career_agent.agents.state import ParsedJD


# Skill keyword pools for first-phase rule matching.
_HARD_SKILLS = [
    "Python", "Go", "Java", "C++", "TypeScript", "JavaScript", "SQL",
    "API", "RESTful", "FastAPI", "Flask", "Django",
    "数据库", "PostgreSQL", "MySQL", "Redis",
    "后端", "前端", "全栈",
    "RAG", "检索增强生成", "embedding", "向量数据库", "vector store",
    "Chroma", "FAISS", "Milvus", "Pinecone",
    "retriever", "检索",
    "LangChain", "LangGraph", "LlamaIndex",
    "LLM", "大模型", "大语言模型", "Agent", "Tool Calling",
    "Docker", "Kubernetes", "CI/CD",
    "Git", "GitHub Actions",
    "PyTorch", "TensorFlow", "机器学习",
]

_BONUS_SKILLS = [
    "MCP", "多 Agent", "workflow", "rerank", "evaluation", "评估",
    "prompt", "Prompt Engineering", "部署", "日志", "监控",
    "Streamlit", "Gradio",
    "开源项目", "技术博客",
]

_SOFT_SKILLS = [
    "沟通", "学习能力", "工程化", "业务理解", "文档", "协作",
    "团队协作", "独立开发",
]

_DIRECTION_KEYWORDS: dict[str, list[str]] = {
    "agent": ["Agent", "多 Agent", "agent", "Tool Calling", "LangGraph"],
    "rag": ["RAG", "检索增强生成", "embedding", "向量数据库", "retriever",
            "Chroma", "FAISS", "LangChain", "LlamaIndex"],
    "backend": ["后端", "FastAPI", "Flask", "API", "RESTful",
                 "PostgreSQL", "MySQL", "数据库", "Docker"],
    "ai_application": ["AI 应用", "智能问答", "文档分析", "大模型应用",
                       "Streamlit", "Gradio"],
}


class JDParserAgent:
    """Parse a raw job description into a structured ``ParsedJD``.

    Uses pure rule-based matching — no LLM calls, no network.
    """

    def parse(self, job_description: str) -> ParsedJD:
        """Parse raw JD text and return a ``ParsedJD``."""
        text = job_description.strip()
        if not text:
            return ParsedJD(metadata={"parser": "jd_parser_agent"})

        job_title = self._extract_job_title(text)
        job_direction = self._infer_direction(text)
        hard = self._match_skills(text, _HARD_SKILLS)
        bonus = self._match_skills(text, _BONUS_SKILLS)
        soft = self._match_skills(text, _SOFT_SKILLS)
        keywords = self._extract_keywords(text)

        return ParsedJD(
            job_title=job_title,
            job_direction=job_direction,
            hard_skills=hard,
            bonus_skills=bonus,
            soft_skills=soft,
            keywords=keywords,
            raw_text=job_description,
            metadata={"parser": "jd_parser_agent"},
        )

    # -- private ---------------------------------------------------------------

    @staticmethod
    def _extract_job_title(text: str) -> str:
        """Extract the first top-level heading as job title."""
        match = re.search(r"^#\s*(?:岗位 JD[：:]\s*)?(.+)$", text, re.MULTILINE)
        if match:
            return match.group(1).strip()
        # Fallback: look for 岗位： pattern
        match = re.search(r"岗位[：:]\s*(.+)$", text, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return ""

    @staticmethod
    def _infer_direction(text: str) -> str:
        """Infer job direction based on keyword density."""
        scores: dict[str, int] = {}
        for direction, keywords in _DIRECTION_KEYWORDS.items():
            score = 0
            for kw in keywords:
                score += len(re.findall(re.escape(kw), text, re.IGNORECASE))
            scores[direction] = score
        if not scores or max(scores.values()) == 0:
            return "general"
        return max(scores, key=scores.get)  # type: ignore[arg-type]

    @staticmethod
    def _match_skills(text: str, pool: list[str]) -> list[str]:
        """Return skill keywords from *pool* that appear in *text*."""
        matched: list[str] = []
        for skill in pool:
            if re.search(re.escape(skill), text, re.IGNORECASE):
                matched.append(skill)
        return matched

    @staticmethod
    def _extract_keywords(text: str) -> list[str]:
        """Extract notable technical keywords from the text."""
        # Combine hard + bonus pools as keyword source
        all_pools = set(_HARD_SKILLS + _BONUS_SKILLS)
        keywords: list[str] = []
        for kw in all_pools:
            if re.search(re.escape(kw), text, re.IGNORECASE):
                keywords.append(kw)
        return sorted(keywords)
