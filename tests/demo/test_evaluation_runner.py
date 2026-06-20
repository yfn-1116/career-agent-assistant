"""Smoke tests for the evaluation runner."""

import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "demo" / "evaluation" / "run_evaluation.py"


def _run(*extra_args: str, cwd: str | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    return subprocess.run(
        [sys.executable, str(RUNNER), *extra_args],
        capture_output=True,
        text=True,
        cwd=cwd or str(REPO_ROOT),
        env=env,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRunnerExists:
    def test_file_exists(self):
        assert RUNNER.is_file()


class TestRunnerSmoke:
    def test_default_run_succeeds(self):
        result = _run()
        assert result.returncode == 0, result.stderr

    def test_default_run_produces_report(self):
        out = REPO_ROOT / "outputs" / "demo" / "evaluation_report.md"
        out.unlink(missing_ok=True)
        result = _run()
        assert result.returncode == 0
        assert out.is_file()

    def test_report_contains_heading(self):
        result = _run()
        assert result.returncode == 0
        text = (REPO_ROOT / "outputs" / "demo" / "evaluation_report.md").read_text(
            encoding="utf-8"
        )
        assert "评估报告" in text

    def test_report_contains_jd_filename(self):
        result = _run()
        assert result.returncode == 0
        text = (REPO_ROOT / "outputs" / "demo" / "evaluation_report.md").read_text(
            encoding="utf-8"
        )
        assert "agent_intern_jd" in text

    def test_report_contains_total_score(self):
        result = _run()
        assert result.returncode == 0
        text = (REPO_ROOT / "outputs" / "demo" / "evaluation_report.md").read_text(
            encoding="utf-8"
        )
        assert "Total Score" in text


class TestWithTmpOutput:
    def test_custom_output_path(self, tmp_path):
        custom_out = tmp_path / "eval.md"
        result = _run(
            "--output-file", str(custom_out),
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0
        assert custom_out.is_file()
        text = custom_out.read_text(encoding="utf-8")
        assert "评估报告" in text


class TestNoExternalDependencies:
    def test_no_network_required(self):
        result = _run()
        assert result.returncode == 0
