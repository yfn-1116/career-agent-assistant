#!/usr/bin/env python3
"""Run evaluation across all sample JD files and produce a Markdown report.

Usage::

    PYTHONPATH=src python demo/evaluation/run_evaluation.py
    PYTHONPATH=src python demo/evaluation/run_evaluation.py \\
        --jobs-dir data/samples/jobs \\
        --top-k 3
"""

import argparse
import sys
from pathlib import Path


def _ensure_in_path() -> None:
    src_dir = str(Path(__file__).resolve().parents[2] / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="RAG / Agent 输出质量评估 Runner")
    p.add_argument(
        "--profile-dir",
        default="data/samples/profile",
        help="用户资料目录",
    )
    p.add_argument(
        "--jobs-dir",
        default="data/samples/jobs",
        help="岗位 JD 目录",
    )
    p.add_argument(
        "--output-file",
        default="outputs/demo/evaluation_report.md",
        help="评估报告输出路径",
    )
    p.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="检索证据数量",
    )
    return p


def render_report(reports: list, args: argparse.Namespace) -> str:
    """Build a Markdown evaluation report from a list of EvaluationReport."""
    lines: list[str] = []
    L = lines.append

    L("# RAG / Agent 输出质量评估报告")
    L("")

    L("## 1. 评估说明")
    L("")
    L("- 本报告为**第一阶段轻量评估**，不依赖外部大模型，不是严格学术 benchmark。")
    L("- 评估规则：workflow 状态、evidence 数量、生成输出非空、证据引用、关键词覆盖。")
    L(f"- 评估时间：自动生成")
    L("")

    L("## 2. 评估样例")
    L("")
    L(f"- Profile 目录：`{args.profile_dir}`")
    L(f"- JD 目录：`{args.jobs_dir}`")
    L(f"- Top-K：{args.top_k}")
    L(f"- 评估 JD 数量：{len(reports)}")
    L("")

    L("## 3. 总览")
    L("")
    L("| # | Job File | Total Score | Status | Evidence Count | Notes |")
    L("|---|---|---|---|---|---|")
    for i, (state, report) in enumerate(reports, 1):
        ev_count = len(state.retrieved_evidence)
        notes = f"{sum(1 for it in report.items if it.passed)}/{len(report.items)} passed"
        L(
            f"| {i} | {Path(report.job_file).name} "
            f"| {report.total_score:.2f} | {state.status} "
            f"| {ev_count} | {notes} |"
        )
    L("")

    L("## 4. 单样例详情")
    L("")
    for state, report in reports:
        fname = Path(report.job_file).name if report.job_file else "unknown"
        L(f"### {fname}")
        L("")
        L(f"- Workflow 状态：{state.status}")
        L(f"- Total Score：{report.total_score:.2f}")
        L(f"- Evidence 数量：{len(state.retrieved_evidence)}")
        L("")
        L("| Check | Passed | Score | Message |")
        L("|---|---|---|---|")
        for item in report.items:
            L(f"| {item.name} | {'✅' if item.passed else '❌'} | {item.score:.2f} | {item.message} |")
        L("")

        if state.generated_output:
            L(f"**Summary**：{state.generated_output.summary}")
            L("")

    L("## 5. 结论")
    L("")
    avg_score = sum(r.total_score for _, r in reports) / len(reports) if reports else 0
    L(f"- 平均 Total Score：{avg_score:.2f}")
    L("- 当前系统使用**规则型 Agent**，输出稳定性高，但分析深度受限于关键词匹配。")
    L("- **优势**：状态管理可靠，证据溯源完整，不编造经历。")
    L("- **不足**：检索为关键词匹配（非语义检索），分析和生成为模板（非 LLM）。")
    L("- 后续接入 Embedding 检索和 LLM 生成后，可重复运行本评估对比效果。")
    L("")

    return "\n".join(lines)


def main() -> None:
    _ensure_in_path()

    from career_agent.evaluation.rules import evaluate_state
    from career_agent.workflows.job_match_workflow import JobMatchWorkflow

    args = build_parser().parse_args()

    profile_dir = Path(args.profile_dir)
    jobs_dir = Path(args.jobs_dir)
    output_file = Path(args.output_file)

    if not profile_dir.is_dir():
        print(f"错误：profile 目录不存在 — {profile_dir}", file=sys.stderr)
        sys.exit(1)

    if not jobs_dir.is_dir():
        print(f"错误：JD 目录不存在 — {jobs_dir}", file=sys.stderr)
        sys.exit(1)

    jd_files = sorted(jobs_dir.glob("*.md"))
    if not jd_files:
        print(f"警告：{jobs_dir} 下未找到 .md 文件，生成空报告。")

    # Run workflow for each JD
    wf = JobMatchWorkflow(profile_dir=profile_dir)
    results: list = []
    for jd_file in jd_files:
        jd_text = jd_file.read_text(encoding="utf-8")
        state = wf.run(jd_text, top_k=args.top_k)
        report = evaluate_state(state, case_id=jd_file.stem, job_file=str(jd_file))
        results.append((state, report))
        print(f"  {jd_file.name}: score={report.total_score:.2f} status={state.status}")

    # Write report
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(render_report(results, args), encoding="utf-8")
    print(f"\n评估报告已写入：{output_file}")


if __name__ == "__main__":
    main()
