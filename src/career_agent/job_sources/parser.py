"""Job posting parser — extracts structured fields from recruitment page text."""

from __future__ import annotations

import re
from typing import Any

from career_agent.job_sources.schema import JobPosting


# Skill keyword pools
_HARD_SKILLS_POOL = [
    "Python", "Java", "Go", "C++", "TypeScript", "JavaScript", "SQL",
    "RAG", "LLM", "LangChain", "LangGraph", "Agent", "embedding",
    "Chroma", "FAISS", "Milvus", "向量数据库", "Docker", "Kubernetes",
    "FastAPI", "Flask", "Django", "Spring", "React", "Vue",
    "PyTorch", "TensorFlow", "OpenCV", "CNN", "机器学习", "深度学习",
    "Redis", "PostgreSQL", "MySQL", "MongoDB", "Kafka", "RabbitMQ",
    "Git", "CI/CD", "Linux", "微服务", "分布式", "API",
    "Prompt Engineering", "Tool Calling", "MCP", "Reranker",
    "Streamlit", "Gradio", "Nginx", "gRPC", "GraphQL",
]

_SOFT_SKILLS_POOL = [
    "沟通", "协作", "独立开发", "文档", "学习能力", "工程化",
    "业务理解", "团队协作", "项目管理", "问题解决",
]

# Field extraction patterns
_PATTERNS = {
    "company": [
        r"(?:公司[：:]\s*)(.+?)(?:\n|$)",
        r"^([\w一-鿿（）]+?(?:科技|网络|软件|信息|数据|智能|云).+?)[\s\n]",
        r"(?:【.*?】\s*)?([\w一-鿿（）]+?(?:有限公司|股份|集团|科技))",
    ],
    "job_title": [
        r"(?:岗位|职位|招聘)[：:]\s*(.+?)(?:\n|$)",
        r"^#\s*(.+?)(?:\n|$)",
        r"(?:招聘|诚聘|急招)\s*(.+?)(?:实习生|工程师|开发|设计|产品|运营)",
    ],
    "salary": [
        r"(\d+[kK千]-?\d*[kK千]?)",
        r"(\d+[-~]\d+[kK千])",
        r"(?:薪资|工资|薪酬)[：:]\s*(.+?)(?:\n|$)",
    ],
    "location": [
        r"(?:地点|城市|地址|base)[：:]\s*(.+?)(?:\n|$)",
        r"(深圳|北京|上海|广州|杭州|成都|武汉|南京|香港)",
    ],
    "education": [
        r"(?:学历|教育)[：:要求]*\s*(.+?)(?:\n|$)",
        r"(本科|硕士|博士|大专)",
    ],
}


class JobPostingParser:
    """Extract structured JobPosting from raw recruitment text.

    Supports BOSS, 实习僧, and general recruitment page formats.
    """

    def parse(self, raw_text: str, source_type: str = "manual", platform: str = "") -> JobPosting:
        """Parse a single job posting from text."""
        text = raw_text.strip()
        posting = JobPosting(
            raw_text=text,
            source_type=source_type,
            platform=platform,
            jd_text=text,
        )

        # Extract fields
        posting.company = self._extract(text, _PATTERNS["company"])
        posting.job_title = self._extract(text, _PATTERNS["job_title"])
        posting.salary = self._extract(text, _PATTERNS["salary"])
        posting.location = self._extract(text, _PATTERNS["location"])
        posting.education = self._extract(text, _PATTERNS["education"])
        posting.hard_skills = self._match_skills(text, _HARD_SKILLS_POOL)
        posting.soft_skills = self._match_skills(text, _SOFT_SKILLS_POOL)
        posting.responsibilities = self._extract_bullets(text, ["岗位职责", "工作职责", "职责", "工作内容"])

        return posting

    def parse_batch(self, text: str, source_type: str = "manual") -> list[JobPosting]:
        """Parse multiple job postings from a list/search results page."""
        # Split by job separators: multiple ## or ---- or numbered items
        sections = re.split(r"\n(?=##\s|\d+\.\s*岗位|---{3,})", text)
        if len(sections) <= 1:
            sections = re.split(r"\n(?=岗位[：:\d])", text)

        postings = []
        for section in sections:
            section = section.strip()
            if len(section) < 30:  # too short to be a job
                continue
            postings.append(self.parse(section, source_type=source_type))
        return postings if postings else [self.parse(text, source_type=source_type)]

    # -- helpers --

    @staticmethod
    def _extract(text: str, patterns: list[str]) -> str:
        for p in patterns:
            m = re.search(p, text, re.MULTILINE)
            if m:
                return m.group(1).strip()
        return ""

    @staticmethod
    def _match_skills(text: str, pool: list[str]) -> list[str]:
        matched = []
        for skill in pool:
            if re.search(re.escape(skill), text, re.IGNORECASE):
                matched.append(skill)
        return matched

    @staticmethod
    def _extract_bullets(text: str, headers: list[str]) -> list[str]:
        """Extract bullet points after a section header."""
        for h in headers:
            m = re.search(rf"{h}[：:\s]*\n(.*?)(?=\n\n|\n[^\s\-•]|\Z)", text, re.DOTALL)
            if m:
                bullets = re.findall(r"[-•*\d.]\s*(.+?)(?:\n|$)", m.group(1))
                return [b.strip() for b in bullets if len(b.strip()) > 5]
        return []
