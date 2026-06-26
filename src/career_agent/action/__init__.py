"""Action 执行层 — 15 个 Tool + RAG Pipeline + Evidence Gate。

- ToolRegistry：统一工具注册和调用
- RAG Pipeline：BM25 → Embedding → RRF → CrossEncoder
- Matching：JD 技能匹配评分
- Generation：简历 bullet + 沟通话术生成
- Verification：真实性检查 + 证据门
"""

from career_agent.agents.build_agent import BuildAgent
from career_agent.agents.match_analysis_agent import MatchAnalysisAgent
from career_agent.agents.rag_retrieve_agent import RAGRetrieveAgent
from career_agent.evaluation.faithfulness import FaithfulnessChecker, FaithfulnessReport
from career_agent.evidence.gate import EvidenceGate
from career_agent.matching.scorer import JobMatchScorer, JobMatchResult
from career_agent.messages.agent import MessageAgent, MessageDraft
from career_agent.rag.embeddings.qwen_embedding import QwenEmbeddingProvider
from career_agent.rag.grading import RetrievalGradeReport, grade_retrieval
from career_agent.rag.reranker import CrossEncoderReranker, LightweightReranker
from career_agent.rag.retrievers.bm25_retriever import BM25Retriever
from career_agent.rag.retrievers.hybrid_retriever import HybridRetriever
from career_agent.rag.retrievers.rrf_fusion import reciprocal_rank_fusion, rrf_fuse_evidence_lists
from career_agent.tools.registry import ToolRegistry, create_standard_registry

__all__ = [
    "BM25Retriever",
    "BuildAgent",
    "CrossEncoderReranker",
    "EvidenceGate",
    "FaithfulnessChecker",
    "FaithfulnessReport",
    "HybridRetriever",
    "JobMatchResult",
    "JobMatchScorer",
    "LightweightReranker",
    "MatchAnalysisAgent",
    "MessageAgent",
    "MessageDraft",
    "QwenEmbeddingProvider",
    "RAGRetrieveAgent",
    "RetrievalGradeReport",
    "ToolRegistry",
    "create_standard_registry",
    "grade_retrieval",
    "reciprocal_rank_fusion",
    "rrf_fuse_evidence_lists",
]
