"""Skill alias mapping — normalize JD and profile skill names."""

SKILL_ALIASES: dict[str, list[str]] = {
    "agent": ["ai agent", "智能体", "agentic workflow", "多 agent", "agent 应用", "agent开发"],
    "rag": ["知识库", "向量检索", "检索增强生成", "retrieval augmented generation", "文档问答", "rag系统"],
    "langgraph": ["stategraph", "workflow", "状态图", "条件分支", "graph orchestration", "langgraph workflow", "langgraph", "agent workflow", "工作流", "编排"],
    "tool calling": ["工具调用", "tool registry", "function calling", "mcp", "外部工具", "tool use"],
    "llm": ["大模型", "llm app", "大模型应用", "llm application", "language model", "qwen", "deepseek", "openai"],
    "prompt engineering": ["prompt", "提示词", "提示工程", "prompt模板"],
    "streamlit": ["streamlit ui", "可视化", "界面"],
    "fastapi": ["api开发", "后端", "rest api", "web框架"],
    "python": ["python3", "python开发"],
    "docker": ["容器化", "docker部署", "container"],
    "kubernetes": ["k8s", "容器编排", "k8s集群"],
    "embedding": ["向量化", "embedding模型", "文本向量", "text embedding"],
    "chroma": ["chromadb", "向量数据库"],
    "faiss": ["向量检索库"],
    "reranker": ["重排序", "rerank", "re-rank"],
    "evaluation": ["评测", "评估", "打分", "grading", "评分"],
    "evidence": ["证据", "溯源", "grounding", "source tracking"],
    "ci/cd": ["持续集成", "部署流水线", "github actions"],
}


def normalize_skill(skill: str) -> str:
    """Normalize a skill name to its canonical form."""
    s = skill.strip().lower()
    for canonical, aliases in SKILL_ALIASES.items():
        if s == canonical or s in [a.lower() for a in aliases]:
            return canonical
    return s


def expand_skill(skill: str) -> list[str]:
    """Return all aliases for a skill (including itself)."""
    s = skill.strip().lower()
    for canonical, aliases in SKILL_ALIASES.items():
        if s == canonical or s in [a.lower() for a in aliases]:
            return [canonical] + aliases
    return [s]
