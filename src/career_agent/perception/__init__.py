"""Perception 感知层 — 把原始输入变成结构化信息。

- 意图分类：识别用户意图（6 种）
- 文件加载：PDF/DOCX/MD → 纯文本
- JD 解析：招聘文本 → 结构化 ParsedJD
- GitHub 读取：公开仓库 README + 元数据
"""

from career_agent.agents.jd_parser import JDParserAgent
from career_agent.agents.orchestrator import OrchestratorAgent
from career_agent.github.local_repo_reader import LocalGitHubRepoReader
from career_agent.github.remote_repo_reader import GitHubRemoteReader
from career_agent.rag.loaders.file_loader import FileLoader
from career_agent.rag.loaders.markdown_loader import MarkdownProfileLoader

__all__ = [
    "FileLoader",
    "GitHubRemoteReader",
    "JDParserAgent",
    "LocalGitHubRepoReader",
    "MarkdownProfileLoader",
    "OrchestratorAgent",
]
