"""JD parser agent — rule-based with optional LLM enhancement."""

import json
import re

from career_agent.agents.state import ParsedJD
from career_agent.models.provider import ModelProvider


# Skill keyword pools for first-phase rule matching (fallback).
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

    Uses rule-based matching by default.  When *model_provider* and
    *use_llm* are both set, the LLM is used for structured extraction
    with rule-based fallback on failure.
    """

    def __init__(
        self,
        model_provider: ModelProvider | None = None,
        use_llm: bool = False,
    ) -> None:
        self.model_provider = model_provider
        self.use_llm = use_llm and model_provider is not None

    def parse(self, job_description: str) -> ParsedJD:
        """Parse raw JD text and return a ``ParsedJD``."""
        text = job_description.strip()
        if not text:
            return ParsedJD(
                raw_text=job_description, metadata={"parser": "jd_parser_agent"}
            )

        if self.use_llm:
            llm_result = self._llm_parse(text, job_description)
            if llm_result is not None:
                return llm_result
            # fall through to rule-based

        return self._rule_parse(text, job_description)

    # -- LLM path ------------------------------------------------------------

    def _llm_parse(self, text: str, original: str) -> ParsedJD | None:
        system = (
            "你是一个岗位 JD 解析助手。请从以下 JD 文本中提取关键信息，"
            "以 JSON 格式返回。\n"
            "{\n"
            '  "job_title": "岗位名称",\n'
            '  "job_direction": "agent/rag/backend/ai_application/general",\n'
            '  "hard_skills": ["技能1", "技能2"],\n'
            '  "bonus_skills": ["加分项1"],\n'
            '  "soft_skills": ["软技能1"],\n'
            '  "keywords": ["关键词1", "关键词2"]\n'
            "}\n"
            "只返回 JSON，不要加任何解释或 markdown 标记。"
        )
        try:
            assert self.model_provider is not None
            raw = self.model_provider.generate(text, system_prompt=system).strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1]
                if raw.endswith("```"):
                    raw = raw[:-3]
            data = json.loads(raw)
            return ParsedJD(
                job_title=str(data.get("job_title", "")),
                job_direction=str(data.get("job_direction", "general")),
                hard_skills=list(data.get("hard_skills", [])),
                bonus_skills=list(data.get("bonus_skills", [])),
                soft_skills=list(data.get("soft_skills", [])),
                keywords=list(data.get("keywords", [])),
                raw_text=original,
                metadata={"parser": "jd_parser_agent_llm"},
            )
        except Exception:
            return None

    # -- rule-based path (unchanged) -----------------------------------------

    def _rule_parse(self, text: str, original: str) -> ParsedJD:
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
            raw_text=original,
            metadata={"parser": "jd_parser_agent"},
        )

    @staticmethod
    def _extract_job_title(text: str) -> str:
        match = re.search(r"^#\s*(?:岗位 JD[：:]\s*)?(.+)$", text, re.MULTILINE)
        if match:
            return match.group(1).strip()
        match = re.search(r"岗位[：:]\s*(.+)$", text, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return ""

    @staticmethod
    def _infer_direction(text: str) -> str:
        scores: dict[str, int] = {}
        for direction, keywords in _DIRECTION_KEYWORDS.items():
            score = 0
            for kw in keywords:
                score += len(re.findall(re.escape(kw), text, re.IGNORECASE))
            scores[direction] = score
        if not scores or max(scores.values()) == 0:
            return "general"
        return max(scores, key=scores.get)

    @staticmethod
    def _match_skills(text: str, pool: list[str]) -> list[str]:
        matched: list[str] = []
        for skill in pool:
            if re.search(re.escape(skill), text, re.IGNORECASE):
                matched.append(skill)
        return matched

    @staticmethod
    def _extract_keywords(text: str) -> list[str]:
        all_pools = set(_HARD_SKILLS + _BONUS_SKILLS)
        keywords: list[str] = []
        for kw in all_pools:
            if re.search(re.escape(kw), text, re.IGNORECASE):
                keywords.append(kw)
        return sorted(keywords)
