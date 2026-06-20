"""Smoke tests for the CLI demo — validate it runs and produces output."""

import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_SCRIPT = REPO_ROOT / "demo" / "cli" / "run_job_match_demo.py"
DEFAULT_OUTPUT = REPO_ROOT / "outputs" / "demo" / "job_match_result.md"


def _run_demo(*extra_args: str) -> subprocess.CompletedProcess:
    """Invoke the CLI demo with PYTHONPATH set."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    cmd = [sys.executable, str(DEMO_SCRIPT), *extra_args]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        env=env,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDemoFileExists:
    def test_demo_script_exists(self):
        assert DEMO_SCRIPT.is_file(), f"Missing {DEMO_SCRIPT}"


class TestDefaultRun:
    def test_default_run_succeeds(self):
        result = _run_demo()
        assert result.returncode == 0, result.stderr

    def test_default_run_produces_output_file(self):
        # Clean up first
        DEFAULT_OUTPUT.unlink(missing_ok=True)
        result = _run_demo()
        assert result.returncode == 0
        assert DEFAULT_OUTPUT.is_file(), f"Expected {DEFAULT_OUTPUT} to be created"

    def test_output_contains_expected_sections(self):
        result = _run_demo()
        assert result.returncode == 0
        text = DEFAULT_OUTPUT.read_text(encoding="utf-8")
        assert "JD 解析结果" in text
        assert "RAG 检索证据" in text
        assert "匹配分析" in text
        assert "生成输出" in text
        assert "运行说明" in text

    def test_terminal_output_shows_status(self):
        result = _run_demo()
        stdout = result.stdout
        assert "任务状态" in stdout
        assert "输出文件" in stdout


class TestCustomArgs:
    def test_custom_job_file(self):
        custom_out = REPO_ROOT / "outputs" / "demo" / "custom_result.md"
        custom_out.unlink(missing_ok=True)

        result = _run_demo(
            "--job-file", "data/samples/jobs/rag_engineer_intern_jd.md",
            "--output-file", "outputs/demo/custom_result.md",
            "--top-k", "3",
        )
        assert result.returncode == 0
        assert custom_out.is_file()

    def test_custom_top_k_respected(self):
        result = _run_demo("--top-k", "1")
        assert result.returncode == 0
        text = DEFAULT_OUTPUT.read_text(encoding="utf-8")
        # Should have at most 1 evidence entry
        assert "共检索到" in text


class TestNoExternalDependencies:
    def test_no_network_calls(self):
        """CLI demo must complete without network access."""
        result = _run_demo()
        assert result.returncode == 0
        assert "任务状态" in result.stdout


class TestErrorHandling:
    def test_missing_job_file_reports_error(self):
        result = _run_demo("--job-file", "nonexistent.md")
        assert result.returncode != 0
        assert "不存在" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_missing_profile_dir_reports_error(self):
        result = _run_demo("--profile-dir", "nonexistent_dir")
        assert result.returncode != 0
