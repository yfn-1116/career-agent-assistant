#!/usr/bin/env python3
"""Offline evaluation runner — runs all eval cases and prints metrics."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def load_cases(path: str) -> list[dict]:
    cases = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def run_eval(cases_path: str, profile_dir: str, output_dir: str = "outputs/eval"):
    from career_agent.service.agent_run import AgentRunRequest, AgentRunService

    cases = load_cases(cases_path)
    svc = AgentRunService(profile_dir=profile_dir)
    results = []

    for case in cases:
        request = AgentRunRequest(
            user_message=case["jd_text"],
            raw_jd=case["jd_text"],
            mode="analyze",
        )
        result = svc.run(request, output_dir=output_dir)
        results.append((case, result))

    return results


def compute_metrics(results: list) -> dict:
    total = len(results)
    if total == 0:
        return {}

    passed = sum(1 for _, r in results if r.status == "completed" and r.decision != "fallback")
    fallback = sum(1 for _, r in results if r.decision == "fallback")

    scores = [r.retrieval_total_score for _, r in results]
    avg_score = sum(scores) / len(scores) if scores else 0.0

    # Source Precision: how many expected sources appear in evidence
    source_precisions = []
    for case, r in results:
        expected = set(case.get("expected_sources", []))
        found = {Path(s).name for s in r.evidence_sources}
        prec = len(expected & found) / len(expected) if expected else 1.0
        source_precisions.append(prec)
    avg_source_precision = sum(source_precisions) / len(source_precisions) if source_precisions else 0.0

    # Hit@K: fraction of cases where at least one expected source appears in top-K
    hit_count = 0
    for case, r in results:
        expected = set(case.get("expected_sources", []))
        found_sources = {Path(s).name for s in r.evidence_sources}
        if expected & found_sources:
            hit_count += 1
    hit_at_k = hit_count / total if total else 0.0

    # MRR: Mean Reciprocal Rank — avg 1/rank of first relevant source
    mrr_scores = []
    for case, r in results:
        expected = set(case.get("expected_sources", []))
        for rank, src in enumerate(r.evidence_sources, 1):
            if Path(src).name in expected:
                mrr_scores.append(1.0 / rank)
                break
        else:
            mrr_scores.append(0.0)
    mrr = sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0

    # Faithfulness pass rate
    faith_pass = sum(1 for _, r in results if r.status == "completed")
    faith_rate = faith_pass / total if total else 0.0

    # Skill Coverage
    skill_coverages = [r.retrieval_total_score for _, r in results]
    avg_skill_coverage = sum(skill_coverages) / len(skill_coverages) if skill_coverages else 0.0

    return {
        "total_cases": total,
        "passed": passed,
        "fallback": fallback,
        "pass_rate": passed / total if total else 0,
        "hit_at_k": round(hit_at_k, 4),
        "mrr": round(mrr, 4),
        "avg_retrieval_score": round(avg_score, 4),
        "avg_source_precision": round(avg_source_precision, 4),
        "avg_skill_coverage": round(avg_skill_coverage, 4),
        "faithfulness_pass_rate": round(faith_rate, 4),
    }


def main():
    import argparse
    p = argparse.ArgumentParser(description="Offline evaluation runner")
    p.add_argument("--cases", default="data/eval/jd_cases.jsonl")
    p.add_argument("--profile", default="data/samples/profile")
    p.add_argument("--output", default="outputs/eval")
    args = p.parse_args()

    print(f"Running eval on {args.cases}...")
    results = run_eval(args.cases, args.profile, args.output)
    metrics = compute_metrics(results)

    print()
    for case, r in results:
        status = "✅" if r.status == "completed" and r.decision != "fallback" else "❌"
        print(f"  {status} {case['case_id']}: grade={r.retrieval_grade}, "
              f"score={r.retrieval_total_score:.2f}, decision={r.decision}")

    print()
    print("Metrics:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")

    # Write report
    Path(args.output).mkdir(parents=True, exist_ok=True)
    report_path = Path(args.output) / "eval_report.json"
    report_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f"\nReport: {report_path}")


if __name__ == "__main__":
    main()
