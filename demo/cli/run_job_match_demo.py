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

    if args.use_embedding:
        emb = state.metadata.get("embedding_provider", "Qwen text-embedding-v3")
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


def render_report(state, args: argparse.Namespace) -> str:
    """Build a self-contained Markdown report from AgentTaskState."""
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

    # -- Section 4 ----------------------------------------------------------
    L("## 4. 匹配分析")
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

    # -- Section 5 ----------------------------------------------------------
    L("## 5. 生成输出")
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

    # -- Section 6 ----------------------------------------------------------
    L(_render_usage_section(args, state))

    return "\n".join(lines)


def main() -> None:
    _ensure_in_path()

    from career_agent.workflows.job_match_workflow import JobMatchWorkflow

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
    if args.use_embedding:
        from career_agent.rag.embeddings.embedding_store import EmbeddingVectorStore
        from career_agent.rag.embeddings.qwen_embedding import QwenEmbeddingProvider
        from career_agent.rag.pipeline import RAGPipeline
        try:
            emb_provider = QwenEmbeddingProvider()
            emb_store = EmbeddingVectorStore(emb_provider)
            rag_pipeline = RAGPipeline(vectorstore=emb_store)
            print(f"🔍 已启用 Qwen Embedding 语义检索（model: {emb_provider.model}）")
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
    if args.use_embedding:
        state.metadata["embedding_provider"] = "Qwen text-embedding-v3"

    # Print brief summary to terminal
    direction = state.parsed_jd.job_direction if state.parsed_jd else "unknown"
    print(f"任务状态：{state.status}")
    print(f"岗位方向：{direction}")
    print(f"检索证据：{len(state.retrieved_evidence)} 条")

    if state.status == "failed":
        print(f"错误信息：{state.error_message}")

    # Write report
    output_file.parent.mkdir(parents=True, exist_ok=True)
    report = render_report(state, args)
    output_file.write_text(report, encoding="utf-8")
    print(f"输出文件：{output_file}")
    print("Done.")


if __name__ == "__main__":
    main()
