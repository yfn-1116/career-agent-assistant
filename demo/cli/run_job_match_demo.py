#!/usr/bin/env python3
"""CLI demo: run the full job-match workflow and write a Markdown report.

Usage::

    PYTHONPATH=src python demo/cli/run_job_match_demo.py
    PYTHONPATH=src python demo/cli/run_job_match_demo.py \\
        --job-file data/samples/jobs/rag_engineer_intern_jd.md \\
        --top-k 3
"""

import argparse
import sys
from pathlib import Path


def _ensure_in_path() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    src_dir = str(repo_root / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="智能投递辅助 Agent — CLI Demo"
    )
    p.add_argument(
        "--profile-dir",
        default="data/samples/profile",
        help="用户资料 Markdown 目录（默认: data/samples/profile）",
    )
    p.add_argument(
        "--job-file",
        default="data/samples/jobs/agent_intern_jd.md",
        help="岗位 JD 文件路径（默认: data/samples/jobs/agent_intern_jd.md）",
    )
    p.add_argument(
        "--output-file",
        default="outputs/demo/job_match_result.md",
        help="输出 Markdown 文件路径（默认: outputs/demo/job_match_result.md）",
    )
    p.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="检索返回的 evidence 数量（默认: 5）",
    )
    p.add_argument(
        "--use-llm",
        action="store_true",
        default=False,
        help="启用 LLM 增强生成（需设置对应 API_KEY 环境变量）",
    )
    p.add_argument(
        "--model-provider",
        default="deepseek",
        choices=["deepseek", "qwen"],
        help="LLM provider（默认: deepseek，可选: qwen）",
    )
    p.add_argument(
        "--use-embedding",
        action="store_true",
        default=False,
        help="启用真实语义检索（需设置 QWEN_API_KEY，使用 Qwen Embedding API）",
    )
    p.add_argument(
        "--use-langgraph",
        action="store_true",
        default=False,
        help="使用 LangGraph StateGraph workflow（替代默认 Python workflow）",
    )
    return p


def _render_usage_section(
    args: argparse.Namespace, state: "AgentTaskState"
) -> str:
    lines: list[str] = []
    L = lines.append  # noqa: E741

    L("## 6. 运行说明")
    L("")
    mode_parts: list[str] = []
    if args.use_llm:
        provider = "Qwen (通义千问)" if args.model_provider == "qwen" else "DeepSeek"
        mode_parts.append(f"LLM 增强：{provider}")
    else:
        mode_parts.append("JD 解析 / 匹配分析 / 输出生成：基于规则和模板")

    if state.metadata.get("embedding_provider"):
        emb = state.metadata["embedding_provider"]
        mode_parts.append(f"语义检索：{emb}")
    else:
        mode_parts.append("检索方式：内存关键词匹配（MemoryVectorStore）")

    for p in mode_parts:
        L(f"- {p}")

    L(f"- 任务状态：{state.status}")
    L(f"- Profile 目录：`{args.profile_dir}`")
    L(f"- JD 文件：`{args.job_file}`")
    L("")
    return "\n".join(lines)


def render_report(
    state,
    args: argparse.Namespace,
    grade_report=None,
    retrieval_query: str = "",
) -> str:
    """Build a self-contained Markdown report from AgentTaskState.

    If *grade_report* (a ``RetrievalGradeReport``) is provided, a
    dedicated RAG diagnostics section is included.
    """
    lines: list[str] = []
    L = lines.append  # noqa: E741

    L("# 智能投递辅助 Agent Demo 结果")
    L("")

    # -- Section 1 ----------------------------------------------------------
    L("## 1. 输入信息")
    L("")
    L(f"- Profile 目录：`{args.profile_dir}`")
    L(f"- JD 文件：`{args.job_file}`")
    L(f"- Top-K：{args.top_k}")
    L(f"- 任务状态：{state.status}")
    L("")

    pj = state.parsed_jd

    # -- Section 2 ----------------------------------------------------------
    L("## 2. JD 解析结果")
    L("")
    if pj is not None:
        L(f"- 岗位标题：{pj.job_title or '（未识别）'}")
        L(f"- 岗位方向：{pj.job_direction}")
        L(f"- 硬技能：{', '.join(pj.hard_skills) if pj.hard_skills else '（未识别）'}")
        L(f"- 加分技能：{', '.join(pj.bonus_skills) if pj.bonus_skills else '（无）'}")
        L(f"- 软技能：{', '.join(pj.soft_skills) if pj.soft_skills else '（未识别）'}")
        L(f"- 关键词：{', '.join(pj.keywords) if pj.keywords else '（无）'}")
    else:
        L("（JD 解析未产生结果）")
    L("")

    # -- Section 3 ----------------------------------------------------------
    L("## 3. RAG 检索证据")
    L("")
    L(f"共检索到 {len(state.retrieved_evidence)} 条证据：")
    L("")
    for i, ev in enumerate(state.retrieved_evidence, 1):
        L(f"### 3.{i} {ev.title or '证据 ' + ev.evidence_id}")
        L("")
        L(f"- evidence_id：`{ev.evidence_id}`")
        L(f"- source_path：`{ev.source_path}`")
        L(f"- score：{ev.score:.2f}")
        L(f"- matched_keywords：{', '.join(ev.matched_keywords)}")
        L("")
        snippet = ev.content[:300].replace("\n", " ")
        L(f"> {snippet}...")
        L("")

    # -- Section 4: RAG Diagnostics (only if grade_report provided) --------
    if grade_report is not None:
        L("## 4. RAG 检索诊断")
        L("")
        L(f"- 检索 Query：`{retrieval_query or grade_report.query}`")
        L(f"- 综合评级：**{grade_report.grade}**"
          f"（total_score={grade_report.metadata.get('total_score', grade_report.average_score):.2f}）")
        L("")
        L("### 指标明细")
        L("")
        L("| 指标 | 得分 | 通过 | 说明 |")
        L("|------|------|------|------|")
        for item in grade_report.items:
            icon = "✅" if item.passed else "❌"
            L(f"| {item.name} | {item.score:.2f} | {icon} | {item.message} |")
        L("")
        L(f"> ⚠️ 评分基于规则型诊断，不是人工标注或 LLM judge。"
          f"来源文件数={grade_report.source_diversity}，"
          f"关键词覆盖率={grade_report.keyword_coverage:.2f}。")
        L("")
        if grade_report.evidence_summaries:
            L("### Top Evidence 详情")
            L("")
            for i, summary in enumerate(grade_report.evidence_summaries, 1):
                L(f"**{i}. {summary.get('title', 'N/A')}**")
                L(f"- score：{summary.get('score', 0):.2f}")
                L(f"- source：`{summary.get('source_path', 'N/A')}`")
                L(f"- matched_keywords：{', '.join(summary.get('matched_keywords', []))}")
                L(f"- snippet：{summary.get('snippet', '')}")
                L("")

    # -- Section 5 ----------------------------------------------------------
    section_idx = 5 if grade_report is not None else 4
    L(f"## {section_idx}. 匹配分析")
    L("")
    ma = state.match_analysis
    if ma is not None:
        L("### Strengths")
        for s in ma.strengths:
            L(f"- {s}")
        L("")
        L("### Weaknesses")
        for w in ma.weaknesses:
            L(f"- {w}")
        L("")
        L("### Recommended Projects")
        for r in ma.recommended_projects:
            L(f"- {r}")
        L("")
        L("### Suggestions")
        for s in ma.suggestions:
            L(f"- {s}")
        L("")
        L(f"### Matched Keywords：{', '.join(ma.matched_keywords)}")
    else:
        L("（无匹配分析结果）")
    L("")

    # -- Section N+1 --------------------------------------------------------
    section_idx += 1
    L(f"## {section_idx}. 生成输出")
    L("")
    go = state.generated_output
    if go is not None:
        L("### Resume Bullets")
        for b in go.resume_bullets:
            L(f"{b}")
        L("")
        L("### Communication Message")
        L("")
        L(f"> {go.communication_message}")
        L("")
        L("### Summary")
        L("")
        L(go.summary)
        L("")
        L("### Evidence Refs")
        L(f"`{', '.join(go.evidence_refs) if go.evidence_refs else '（无）'}`")
    else:
        L("（无生成输出）")
    L("")

    # -- Section N+2 --------------------------------------------------------
    section_idx += 1
    # Rewrite the usage section header to match the dynamic number
    usage_text = _render_usage_section(args, state)
    usage_text = usage_text.replace("## 6. 运行说明", f"## {section_idx}. 运行说明")
    L(usage_text)

    return "\n".join(lines)


def main() -> None:
    _ensure_in_path()

    args = build_parser().parse_args()

    profile_dir = Path(args.profile_dir)
    job_file = Path(args.job_file)
    output_file = Path(args.output_file)

    # Validate inputs
    if not profile_dir.is_dir():
        print(f"错误：profile 目录不存在 — {profile_dir}", file=sys.stderr)
        sys.exit(1)

    if not job_file.is_file():
        print(f"错误：JD 文件不存在 — {job_file}", file=sys.stderr)
        sys.exit(1)

    job_text = job_file.read_text(encoding="utf-8")

    if args.use_langgraph:
        _run_langgraph_demo(args, job_text)
        return

    from career_agent.workflows.job_match_workflow import JobMatchWorkflow

    # Build workflow — optionally with LLM
    jd_parser = None
    match_analysis_agent = None
    build_agent = None

    if args.use_llm:
        from career_agent.agents.build_agent import BuildAgent
        from career_agent.agents.jd_parser import JDParserAgent
        from career_agent.agents.match_analysis_agent import MatchAnalysisAgent

        if args.model_provider == "qwen":
            from career_agent.models.qwen_provider import QwenProvider
            try:
                provider = QwenProvider()
                jd_parser = JDParserAgent(model_provider=provider, use_llm=True)
                match_analysis_agent = MatchAnalysisAgent(model_provider=provider, use_llm=True)
                build_agent = BuildAgent(model_provider=provider, use_llm=True)
                print(f"🤖 已启用 Qwen LLM（model: {provider.model}）— JD解析 + 匹配分析 + 输出生成")
            except Exception as e:
                print(f"⚠️  无法初始化 Qwen：{e}，回退到规则型")
        else:
            from career_agent.models.deepseek_provider import DeepSeekProvider
            try:
                provider = DeepSeekProvider()
                jd_parser = JDParserAgent(model_provider=provider, use_llm=True)
                match_analysis_agent = MatchAnalysisAgent(model_provider=provider, use_llm=True)
                build_agent = BuildAgent(model_provider=provider, use_llm=True)
                print(f"🤖 已启用 DeepSeek LLM（model: {provider.model}）— JD解析 + 匹配分析 + 输出生成")
            except Exception as e:
                print(f"⚠️  无法初始化 DeepSeek：{e}，回退到规则型")

    rag_pipeline = None
    use_embedding = args.use_embedding
    emb_provider = None

    # Auto-detect Qwen embedding if API key is set
    import os as _os
    if not use_embedding and _os.getenv("QWEN_API_KEY"):
        use_embedding = True

    if use_embedding:
        from career_agent.rag.embeddings.embedding_store import EmbeddingVectorStore
        from career_agent.rag.embeddings.qwen_embedding import QwenEmbeddingProvider
        from career_agent.rag.pipeline import RAGPipeline
        try:
            emb_provider = QwenEmbeddingProvider()
            emb_store = EmbeddingVectorStore(emb_provider)
            rag_pipeline = RAGPipeline(vectorstore=emb_store)
            print(f"🔍 已启用千问 Embedding 语义检索 (model={emb_provider.model}, dim={emb_provider.dimension})")
        except Exception as e:
            print(f"⚠️  无法初始化 Embedding：{e}，回退到关键词检索")

    wf = JobMatchWorkflow(
        profile_dir=profile_dir,
        rag_pipeline=rag_pipeline,
        jd_parser=jd_parser,
        match_analysis_agent=match_analysis_agent,
        build_agent=build_agent,
    )
    state = wf.run(job_text, top_k=args.top_k)
    # Attach provider metadata for report rendering
    if args.use_llm:
        state.metadata["llm_provider"] = args.model_provider
    if use_embedding and emb_provider is not None:
        state.metadata["embedding_provider"] = f"Qwen {emb_provider.model}"

    # Run retrieval grading for RAG diagnostics
    from career_agent.agents.rag_retrieve_agent import RAGRetrieveAgent
    from career_agent.rag.grading import grade_retrieval

    retrieval_query = ""
    if state.parsed_jd is not None:
        _rag_agent = RAGRetrieveAgent(pipeline=rag_pipeline or wf.rag_pipeline)
        retrieval_query = _rag_agent.build_query_from_parsed_jd(state.parsed_jd)
    grade_report = grade_retrieval(
        query=retrieval_query,
        parsed_jd=state.parsed_jd,
        evidence=state.retrieved_evidence,
        top_k=args.top_k,
    )
    print(f"检索诊断：grade={grade_report.grade}, "
          f"total={grade_report.metadata.get('total_score', 0):.2f}, "
          f"coverage={grade_report.keyword_coverage:.2f}")

    # Print brief summary to terminal
    direction = state.parsed_jd.job_direction if state.parsed_jd else "unknown"
    print(f"任务状态：{state.status}")
    print(f"岗位方向：{direction}")
    print(f"检索证据：{len(state.retrieved_evidence)} 条")

    if state.status == "failed":
        print(f"错误信息：{state.error_message}")

    # Write report
    output_file.parent.mkdir(parents=True, exist_ok=True)
    report = render_report(state, args, grade_report=grade_report, retrieval_query=retrieval_query)
    output_file.write_text(report, encoding="utf-8")
    print(f"输出文件：{output_file}")
    print("Done.")


def _run_langgraph_demo(args: argparse.Namespace, job_text: str) -> None:
    """Run the LangGraph workflow and print key diagnostics."""
    from career_agent.agents.build_agent import BuildAgent
    from career_agent.agents.jd_parser import JDParserAgent
    from career_agent.agents.match_analysis_agent import MatchAnalysisAgent
    from career_agent.workflows.langgraph_workflow import run_langgraph_workflow

    # Build optional LLM agents
    jd_parser = None
    match_agent = None
    build_agent = None
    rag_pipeline = None

    if args.use_llm:
        if args.model_provider == "qwen":
            from career_agent.models.qwen_provider import QwenProvider
            try:
                provider = QwenProvider()
                jd_parser = JDParserAgent(model_provider=provider, use_llm=True)
                match_agent = MatchAnalysisAgent(model_provider=provider, use_llm=True)
                build_agent = BuildAgent(model_provider=provider, use_llm=True)
                print(f"🤖 [LangGraph] 已启用 Qwen LLM（model: {provider.model}）")
            except Exception as e:
                print(f"⚠️  无法初始化 Qwen：{e}，回退到规则型")
        else:
            from career_agent.models.deepseek_provider import DeepSeekProvider
            try:
                provider = DeepSeekProvider()
                jd_parser = JDParserAgent(model_provider=provider, use_llm=True)
                match_agent = MatchAnalysisAgent(model_provider=provider, use_llm=True)
                build_agent = BuildAgent(model_provider=provider, use_llm=True)
                print(f"🤖 [LangGraph] 已启用 DeepSeek LLM（model: {provider.model}）")
            except Exception as e:
                print(f"⚠️  无法初始化 DeepSeek：{e}，回退到规则型")

    use_emb = args.use_embedding
    import os as _os2
    if not use_emb and _os2.getenv("QWEN_API_KEY"):
        use_emb = True

    if use_emb:
        from career_agent.rag.embeddings.embedding_store import EmbeddingVectorStore
        from career_agent.rag.embeddings.qwen_embedding import QwenEmbeddingProvider
        from career_agent.rag.pipeline import RAGPipeline
        try:
            emb_provider = QwenEmbeddingProvider()
            emb_store = EmbeddingVectorStore(emb_provider)
            rag_pipeline = RAGPipeline(vectorstore=emb_store)
            print(f"🔍 [LangGraph] 已启用千问 Embedding 语义检索（model: {emb_provider.model}）")
        except Exception as e:
            print(f"⚠️  无法初始化 Embedding：{e}，回退到关键词检索")

    final_state = run_langgraph_workflow(
        raw_jd=job_text,
        top_k=args.top_k,
        profile_dir=args.profile_dir,
        output_dir=str(Path(args.output_file).parent),
        jd_parser=jd_parser,
        rag_pipeline=rag_pipeline,
        match_agent=match_agent,
        build_agent=build_agent,
    )

    # Print LangGraph diagnostics
    print(f"Trace ID: {final_state['trace_id']}")
    print(f"Status: {final_state['status']}")

    pj = final_state["parsed_jd"]
    if pj is not None:
        print(f"Parsed JD: title={pj.job_title}, direction={pj.job_direction}")

    queries = final_state.get("queries", [])
    print(f"Rewritten Queries: {queries}")

    chunks = final_state.get("retrieved_chunks", [])
    print(f"Retrieved Chunks: {len(chunks)} 条")
    for ev in chunks:
        print(f"  - {ev.title or ev.evidence_id} score={ev.score:.2f}")

    rs = final_state.get("retrieval_scores")
    if rs is not None:
        print(f"Retrieval Scores: grade={rs.grade}, total={rs.metadata.get('total_score', 0):.2f}")
    else:
        print("Retrieval Scores: None")

    print(f"Missing Keywords: {final_state.get('missing_keywords', [])}")
    print(f"Decision: {final_state['decision']}")
    print(f"Retry Count: {final_state['retry_count']}")
    print(f"Report Path: {final_state.get('report_path', '')}")

    if final_state["status"] == "failed":
        print(f"Error: {final_state.get('error_message', '')}")

    print("Done.")


if __name__ == "__main__":
    main()
