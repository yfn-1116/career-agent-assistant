"""Memory 记忆层 — 短时+长时+知识库三重记忆。

- 短时记忆：内存列表（最近 20 条消息）→ LLM 上下文
- 长时记忆：JSONL 持久化 + BM25 检索 → 跨会话回忆
- 知识库：chunks.jsonl → 完整 RAG Pipeline 检索
"""

from career_agent.agents.memory import ConversationMemory, MemoryEntry
from career_agent.service.knowledge_base import KnowledgeBaseService, KnowledgeBaseIngestResult

__all__ = [
    "ConversationMemory",
    "KnowledgeBaseIngestResult",
    "KnowledgeBaseService",
    "MemoryEntry",
]
