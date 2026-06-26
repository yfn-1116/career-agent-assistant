"""Tool Registry — all agent capabilities must be registered here.

No tool may be called outside the registry.
"""

from __future__ import annotations

import time
from typing import Any

from career_agent.tools.base import Tool, ToolResult


class ToolRegistry:
    """Central registry for all agent tools.

    Usage::

        reg = ToolRegistry()
        reg.register(ParseJDTool())
        tool = reg.get("parse_jd")
        result = tool.run(raw_jd="...")
    """

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool.  Raises ValueError on duplicate name."""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        """Get a tool by name.  Raises KeyError if not found."""
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry. Available: {sorted(self._tools.keys())}")
        return self._tools[name]

    def has(self, name: str) -> bool:
        return name in self._tools

    def list_tools(self) -> list[str]:
        return sorted(self._tools.keys())

    @property
    def tool_count(self) -> int:
        return len(self._tools)

    def invoke(self, name: str, **kwargs: Any) -> ToolResult:
        """Invoke a registered tool with timing and error handling.

        Never crashes — returns ``ToolResult(success=False, error=...)``
        on failure.
        """
        try:
            tool = self.get(name)
        except KeyError as e:
            return ToolResult(success=False, error=str(e), summary=f"tool '{name}' not found")

        start = time.perf_counter()
        try:
            result = tool.run(**kwargs)
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            return ToolResult(
                success=False,
                error=f"{type(exc).__name__}: {exc}",
                summary=f"tool '{name}' raised exception",
                duration_ms=round(elapsed, 2),
            )

        elapsed = (time.perf_counter() - start) * 1000
        result.duration_ms = round(elapsed, 2)
        if not result.summary:
            result.summary = f"tool '{name}' {'ok' if result.success else 'failed'}"
        return result


# ---------------------------------------------------------------------------
# Standard tool implementations
# ---------------------------------------------------------------------------


class ParseJDTool(Tool):
    name = "parse_jd"
    description = "解析岗位 JD 文本，提取岗位名称、方向、硬技能、加分技能、软技能和关键词。当用户粘贴或发送招聘信息、岗位描述、实习招聘文本时触发。"

    def run(self, raw_jd: str = "", **kwargs: Any) -> ToolResult:  # noqa: ARG002
        from career_agent.agents.jd_parser import JDParserAgent
        agent = JDParserAgent()
        pj = agent.parse(raw_jd)
        return ToolResult(
            success=True,
            output={"parsed_jd": pj},
            summary=f"parsed JD: title={pj.job_title}, direction={pj.job_direction}",
            state_changes=["parsed_jd"],
        )

    @property
    def safety_notes(self) -> list[str]:
        return ["只解析 JD 文本，不调用外部 API（规则模式）"]


class PlanQueriesTool(Tool):
    name = "plan_queries"
    description = "根据解析后的 JD 生成检索查询词。已完成 JD 解析后自动生成查询，用于从知识库检索匹配经历。"

    def run(self, parsed_jd: Any = None, **kwargs: Any) -> ToolResult:  # noqa: ARG002
        from career_agent.agents.rag_retrieve_agent import RAGRetrieveAgent
        if parsed_jd is None:
            return ToolResult(success=False, error="parsed_jd is required", summary="missing input")
        agent = RAGRetrieveAgent()
        query = agent.build_query_from_parsed_jd(parsed_jd)
        return ToolResult(
            success=True,
            output={"queries": [query]},
            summary=f"planned query: {query[:100]}",
            state_changes=["queries"],
        )

    @property
    def safety_notes(self) -> list[str]:
        return ["查询基于 JD 技能生成，不引入外部信息"]


class RewriteQueryTool(Tool):
    name = "rewrite_query"
    description = "当检索质量评分不达标时，根据缺失关键词重写查询以提高召回率。仅在检索评分 < 0.65 时触发。"

    def run(
        self, parsed_jd: Any = None, missing_keywords: list[str] | None = None,
        previous_query: str = "", retry_count: int = 0, **kwargs: Any,
    ) -> ToolResult:
        from career_agent.agents.rag_retrieve_agent import RAGRetrieveAgent
        if parsed_jd is None:
            return ToolResult(success=False, error="parsed_jd is required", summary="missing input")
        agent = RAGRetrieveAgent()
        base = agent.build_query_from_parsed_jd(parsed_jd)
        missing = missing_keywords or []
        query = f"{base} {' '.join(missing[:5])}" if missing else base
        return ToolResult(
            success=True,
            output={"queries": [query], "retry_count": retry_count + 1},
            summary=f"rewritten query (retry #{retry_count + 1}): {query[:100]}",
            state_changes=["queries", "retry_count"],
        )


class RetrieveProfileTool(Tool):
    name = "retrieve_profile"
    description = "从用户知识库检索与 JD 相关的项目经历和技能证据。使用 BM25 关键词 + Embedding 语义双路混合检索。当需要查找用户是否具备某技能时触发。"

    def run(
        self, queries: list[str] | None = None, top_k: int = 5,
        profile_dir: str = "", **kwargs: Any,
    ) -> ToolResult:
        if not queries or not queries[0]:
            return ToolResult(success=False, error="queries is empty", summary="no queries")
        from career_agent.rag.pipeline import RAGPipeline
        pipeline = RAGPipeline()
        if profile_dir:
            pipeline.build_index(profile_dir)
        chunks = pipeline.retrieve(queries[0], top_k=top_k)
        return ToolResult(
            success=True,
            output={"retrieved_chunks": chunks},
            summary=f"retrieved {len(chunks)} chunks for query: {queries[0][:80]}",
            state_changes=["retrieved_chunks"],
        )

    @property
    def safety_notes(self) -> list[str]:
        return ["只检索用户本地资料库，不访问外部数据"]


class RerankChunksTool(Tool):
    name = "rerank_chunks"
    description = "对检索返回的候选片段进行精排，使用 Cross-Encoder 模型逐对打分，输出最相关的 top 5 片段。在检索完成后触发。"

    def run(
        self, retrieved_chunks: list[Any] | None = None,
        parsed_jd: Any = None, **kwargs: Any,
    ) -> ToolResult:
        if not retrieved_chunks:
            return ToolResult(success=False, error="retrieved_chunks is empty", summary="no chunks to rerank")
        from career_agent.domain.schemas import RetrievedChunk
        from career_agent.rag.reranker import LightweightReranker

        domain_chunks = []
        for ev in retrieved_chunks:
            domain_chunks.append(RetrievedChunk(
                chunk_id=ev.chunk_id, source=ev.source_path, content=ev.content,
                summary=ev.content[:120], final_hybrid_score=ev.score,
                matched_skills=list(ev.matched_keywords) if ev.matched_keywords else [],
            ))
        jd_skills = set()
        if parsed_jd is not None:
            for s in (parsed_jd.hard_skills + parsed_jd.keywords):
                if s.strip():
                    jd_skills.add(s.strip().lower())
        reranker = LightweightReranker(top_k=len(domain_chunks))
        reranked = reranker.rerank(domain_chunks, jd_skills=jd_skills if jd_skills else None)
        return ToolResult(
            success=True,
            output={"reranked_chunks": reranked},
            summary=f"reranked {len(reranked)} chunks",
            state_changes=["reranked_chunks"],
        )


class GradeRetrievalTool(Tool):
    name = "grade_retrieval"
    description = "从证据数量、平均分数、关键词覆盖率、来源多样性、可追溯性 5 个维度评估检索质量。在精排完成后触发。"

    def run(
        self, query: str = "", evidence: list[Any] | None = None,
        parsed_jd: Any = None, top_k: int = 5, **kwargs: Any,
    ) -> ToolResult:
        from career_agent.rag.grading import grade_retrieval
        ev = evidence or []
        report = grade_retrieval(query=query, parsed_jd=parsed_jd, evidence=ev, top_k=top_k)
        return ToolResult(
            success=True,
            output={"retrieval_scores": report},
            summary=f"grade={report.grade} score={report.metadata.get('total_score', 0):.2f}",
            state_changes=["retrieval_scores"],
        )


class SelectEvidenceTool(Tool):
    name = "select_evidence"
    description = "从检索结果中筛选高质量证据片段（分数 ≥ 0.3），用于后续生成简历 bullet 和沟通话术。在评分完成后触发。"

    def run(
        self, retrieved_chunks: list[Any] | None = None,
        retrieval_scores: Any = None, **kwargs: Any,
    ) -> ToolResult:
        chunks = retrieved_chunks or []
        selected = []
        for ev in chunks:
            score = getattr(ev, "score", 0)
            if score >= 0.3:  # min threshold
                selected.append({
                    "evidence_id": getattr(ev, "evidence_id", ev.chunk_id),
                    "chunk_id": ev.chunk_id,
                    "source": ev.source_path if hasattr(ev, "source_path") else "",
                    "content": ev.content[:200],
                    "score": score,
                })
        return ToolResult(
            success=True,
            output={"selected_evidence": selected},
            summary=f"selected {len(selected)}/{len(chunks)} evidence items",
            state_changes=["selected_evidence"],
        )


class AnalyzeMatchTool(Tool):
    name = "analyze_match"
    description = "对比 JD 技能要求与检索到的用户证据，输出匹配优势、能力缺口、推荐项目和改进建议。当需要判断用户是否适合某岗位时触发。"

    def run(
        self, parsed_jd: Any = None, retrieved_chunks: list[Any] | None = None, **kwargs: Any,
    ) -> ToolResult:
        from career_agent.agents.match_analysis_agent import MatchAnalysisAgent
        agent = MatchAnalysisAgent()
        result = agent.analyze(parsed_jd, retrieved_chunks or [])
        return ToolResult(
            success=True,
            output={"match_analysis": result},
            summary=f"strengths={len(result.strengths)} weaknesses={len(result.weaknesses)}",
            state_changes=["match_analysis"],
        )


class GenerateGroundedAnswerTool(Tool):
    name = "generate_grounded_answer"
    description = "基于检索证据生成简历 bullet（按 evidence status 分级：可直接写入/需确认/仅学习计划）和 HR 沟通话术。当需要输出简历建议时触发。"

    def run(
        self, parsed_jd: Any = None, retrieved_chunks: list[Any] | None = None,
        match_analysis: Any = None, **kwargs: Any,
    ) -> ToolResult:
        from career_agent.agents.build_agent import BuildAgent
        from career_agent.agents.state import MatchAnalysisResult, ParsedJD
        agent = BuildAgent()
        pj = parsed_jd or ParsedJD()
        ma = match_analysis or MatchAnalysisResult()
        result = agent.build(pj, retrieved_chunks or [], ma)
        return ToolResult(
            success=True,
            output={"generated_result": result},
            summary=f"bullets={len(result.resume_bullets)} refs={len(result.evidence_refs)}",
            state_changes=["generated_result"],
        )

    @property
    def safety_notes(self) -> list[str]:
        return ["所有声称必须有 evidence_refs 支持", "不编造用户没有的经历"]


class CheckFaithfulnessTool(Tool):
    name = "check_faithfulness"
    description = "验证生成的简历 bullet 是否有证据支撑，检测夸大措辞（完整实现、大规模部署），无证据的声称将被拒绝。在生成输出后触发。"

    def run(
        self, generated_result: Any = None, retrieved_chunks: list[Any] | None = None, **kwargs: Any,
    ) -> ToolResult:
        from career_agent.domain.schemas import Evidence, GeneratedBullet
        from career_agent.evaluation.faithfulness import FaithfulnessChecker

        if generated_result is None:
            return ToolResult(success=False, error="generated_result is required", summary="missing input")

        # Build evidence map from retrieved chunks
        chunk_map = {}
        for ev in (retrieved_chunks or []):
            cid = getattr(ev, "chunk_id", "")
            chunk_map[cid] = ev
            if hasattr(ev, "evidence_id"):
                chunk_map[ev.evidence_id] = ev

        refs = getattr(generated_result, "evidence_refs", [])
        evidences = []
        for ref in refs:
            cv = chunk_map.get(ref)
            if cv is not None:
                evidences.append(Evidence(
                    evidence_id=ref, chunk_id=cv.chunk_id,
                    source=getattr(cv, "source_path", ""), content=getattr(cv, "content", ""),
                ))
            else:
                evidences.append(Evidence(evidence_id=ref, chunk_id=ref))

        bullets = [
            GeneratedBullet(text=b, evidence_ids=list(refs))
            for b in getattr(generated_result, "resume_bullets", [])
        ]

        checker = FaithfulnessChecker()
        report = checker.check(bullets, evidences)
        return ToolResult(
            success=True,
            output={"faithfulness_report": report},
            summary=f"score={report.faithfulness_score:.2f} decision={report.decision}",
            state_changes=["faithfulness_report"],
        )

    @property
    def safety_notes(self) -> list[str]:
        return ["检查生成内容是否有证据支持", "score < 0.75 时禁止作为最终输出"]


class FallbackTool(Tool):
    name = "fallback"
    description = "当检索质量经多次重试仍不达标时，生成安全输出，诚实告知用户当前资料不足以支撑完整分析。仅在检索耗尽时触发。"

    def run(
        self, missing_keywords: list[str] | None = None,
        retry_count: int = 0, max_retries: int = 2,
        output_dir: str = "/tmp", **kwargs: Any,
    ) -> ToolResult:
        missing = missing_keywords or []
        reason = (
            f"经过 {retry_count} 轮检索（最多 {max_retries} 轮），检索质量未达标。"
        )
        if missing:
            reason += f" 未覆盖技能：{', '.join(missing[:10])}。"
        return ToolResult(
            success=True,
            output={
                "decision": "fallback",
                "fallback_reason": reason,
                "suggested_inputs": [f"{kw} 相关项目经历或技能说明" for kw in missing[:5]],
                "safe_message": "当前资料不足以支持完整匹配分析，建议补充相关材料。",
                "insufficient_evidence": True,
            },
            summary=f"fallback: {len(missing)} missing keywords",
            state_changes=["decision", "fallback_reason"],
        )

    @property
    def safety_notes(self) -> list[str]:
        return ["绝对不编造用户经历", "诚实告知资料不足", "不生成虚假简历"]


class WriteReportTool(Tool):
    name = "write_report"
    description = "将完整分析结果（JD 解析、检索证据、匹配分析、生成输出、真实性检查）写入 Markdown 诊断报告。在分析流程结束时触发。"

    def run(self, state: dict[str, Any] | None = None, output_dir: str = "outputs/demo", **kwargs: Any) -> ToolResult:
        from pathlib import Path
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        trace_id = (state or {}).get("trace_id", "unknown")
        path = Path(output_dir) / f"agent_report_{trace_id}.md"
        lines = ["# Agent Run Report", "", f"Trace: `{trace_id}`"]
        path.write_text("\n".join(lines), encoding="utf-8")
        return ToolResult(
            success=True,
            output={"report_path": str(path)},
            summary=f"report written to {path}",
            state_changes=["report_path"],
        )


class WriteDiagnosticsTool(Tool):
    name = "write_diagnostics"
    description = "将工作流运行状态、工具调用追踪、重试历史写入 JSON 诊断文件，用于调试和离线评估。在报告写入后触发。"

    def run(self, state: dict[str, Any] | None = None, output_dir: str = "outputs/diagnostics", **kwargs: Any) -> ToolResult:
        from pathlib import Path
        from career_agent.evaluation.diagnostics import write_diagnostics
        path = write_diagnostics(state or {}, output_dir=output_dir)
        return ToolResult(
            success=True,
            output={"diagnostics_path": str(path)},
            summary=f"diagnostics written to {path}",
            state_changes=["diagnostics_path"],
        )


class WebSearchTool(Tool):
    name = "web_search"
    description = "搜索互联网获取公司背景、行业信息、岗位相关资讯。使用 DuckDuckGo。当用户询问公司情况或需要了解行业背景时触发。"

    @property
    def safety_notes(self) -> list[str]:
        return ["搜索结果作为参考，不作为 evidence 直接用于简历", "不搜索个人隐私"]

    def run(self, query: str = "", max_results: int = 5, **kwargs: Any) -> ToolResult:  # noqa: ARG002
        if not query.strip():
            return ToolResult(success=False, error="query is required")
        try:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append({"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")[:300]})
            return ToolResult(success=True, output={"results": results, "query": query},
                              summary=f"found {len(results)} results for: {query[:60]}")
        except Exception as e:
            return ToolResult(success=False, error=str(e), summary="web search failed")


class GitHubRepoTool(Tool):
    name = "github_repo"
    description = "拉取公开 GitHub 仓库的 README 和文档，分析项目技术栈并存入知识库。当用户粘贴 GitHub 链接或提到开源项目时触发。"

    @property
    def safety_notes(self) -> list[str]:
        return ["只读公开仓库", "不修改任何 GitHub 内容", "不使用 API key 访问私有仓库"]

    def run(self, repo_name: str = "", **kwargs: Any) -> ToolResult:  # noqa: ARG002
        if not repo_name.strip():
            return ToolResult(success=False, error="repo_name is required")
        try:
            from career_agent.github.remote_repo_reader import GitHubRemoteReader
            reader = GitHubRemoteReader()
            docs = reader.read_repo(repo_name)
            if docs:
                snippets = [{"title": d.title, "source": d.source_path, "snippet": d.content[:200]} for d in docs]
                return ToolResult(success=True, output={"repo": repo_name, "documents": snippets, "count": len(docs)},
                                  summary=f"read {len(docs)} docs from {repo_name}")

            # Fallback: try raw.githubusercontent.com (no rate limit)
            import urllib.request
            url = f"https://raw.githubusercontent.com/{repo_name}/main/README.md"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "smart-apply-agent"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    content = resp.read().decode("utf-8", errors="replace")
                return ToolResult(success=True,
                                  output={"repo": repo_name, "documents": [{"title": "README.md", "snippet": content[:500]}]},
                                  summary=f"read README from {repo_name} (raw)")
            except Exception:
                return ToolResult(success=True, output={"repo": repo_name, "documents": [], "count": 0},
                                  summary=f"unable to read {repo_name} (try setting GITHUB_TOKEN)")
        except Exception as e:
            return ToolResult(success=False, error=str(e), summary=f"github read failed: {repo_name}")


class TaskAgentTool(Tool):
    """Spawn a sub-agent for isolated parallel task execution.

    Reference: OpenCode agent-tool.go (Agent-as-Tool pattern).
    The sub-agent runs with restricted tools in an isolated context
    and returns a single consolidated result.
    """

    name = "task_agent"
    description = (
        "启动一个子 Agent 执行独立任务。子 Agent 有自己的上下文，"
        "看不到主对话的中间步骤。用于搜索、批量分析等可以独立完成的任务。"
        "当你需要并行处理多个任务、或某个任务不需要主对话上下文时触发。"
        "传入详细的 task 描述和 allowed_tools 列表。"
    )

    def run(self, task: str = "", allowed_tools: list[str] | None = None, **kwargs: Any) -> ToolResult:
        if not task.strip():
            return ToolResult(success=False, error="task is required", summary="empty task")

        try:
            from career_agent.agents.sub_agent import SubAgent
            from career_agent.infrastructure.llm import create_llm_provider

            llm = create_llm_provider()
            if not llm.is_available:
                return ToolResult(success=False, error="LLM not available for sub-agent")

            sub = SubAgent(llm=llm, tool_registry=None, max_steps=8)
            # Inject tool_registry at runtime
            from career_agent.tools.registry import create_standard_registry
            sub.tool_registry = create_standard_registry()

            result = sub.execute(task=task, allowed_tools=allowed_tools)

            return ToolResult(
                success=result.success,
                output={"answer": result.answer, "tools_called": result.tools_called},
                summary=result.answer[:200] if result.success else f"sub-agent error: {result.error}",
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e), summary="sub-agent execution failed")

    @property
    def safety_notes(self) -> list[str]:
        return ["子 Agent 不能修改文件", "子 Agent 独立上下文，不影响主对话"]


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_standard_registry() -> ToolRegistry:
    """Create a ToolRegistry with all 15 standard tools registered."""
    reg = ToolRegistry()
    for tool_cls in [
        ParseJDTool, PlanQueriesTool, RewriteQueryTool, RetrieveProfileTool,
        RerankChunksTool, GradeRetrievalTool, SelectEvidenceTool,
        AnalyzeMatchTool, GenerateGroundedAnswerTool, CheckFaithfulnessTool,
        FallbackTool, WriteReportTool, WriteDiagnosticsTool,
        WebSearchTool, GitHubRepoTool, TaskAgentTool,
    ]:
        reg.register(tool_cls())
    return reg
