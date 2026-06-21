import tempfile
from pathlib import Path
from career_agent.applications.repository import ApplicationRecord, ApplicationRepository


class TestApplicationRepository:
    def test_save_and_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ApplicationRepository(f"{tmp}/apps.jsonl")
            rec = ApplicationRecord(application_id="app-1", job_title="Agent Intern", match_score=0.75)
            repo.save(rec)
            assert repo.count() == 1
            records = repo.list_all()
            assert records[0].job_title == "Agent Intern"

    def test_update_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ApplicationRepository(f"{tmp}/apps.jsonl")
            repo.save(ApplicationRecord(application_id="app-1", status="analyzed"))
            assert repo.update_status("app-1", "applied")
            assert repo.get("app-1").status == "applied"

    def test_jsonl_appends(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ApplicationRepository(f"{tmp}/apps.jsonl")
            repo.save(ApplicationRecord(application_id="a1"))
            repo.save(ApplicationRecord(application_id="a2"))
            assert repo.count() == 2

    def test_get_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ApplicationRepository(f"{tmp}/apps.jsonl")
            assert repo.get("nope") is None


class TestCapabilityGap:
    def test_empty_is_safe(self):
        from career_agent.capability.gap_analyzer import CapabilityGapAnalyzer
        report = CapabilityGapAnalyzer().analyze([], [])
        assert report.analyzed_jobs_count == 0

    def test_analyze_finds_gaps(self):
        from career_agent.capability.gap_analyzer import CapabilityGapAnalyzer
        from career_agent.applications.repository import ApplicationRecord
        from career_agent.profile.schema import STATUS_IMPLEMENTED, ProfileItem
        apps = [
            ApplicationRecord(application_id="a1", missing_skills=["Docker", "K8s"], matched_skills=["Python"]),
            ApplicationRecord(application_id="a2", missing_skills=["Docker", "MCP"], matched_skills=["Python"]),
        ]
        items = [ProfileItem(source_path="x", skills=["Python"], status=STATUS_IMPLEMENTED)]
        report = CapabilityGapAnalyzer().analyze(apps, items)
        assert report.analyzed_jobs_count == 2
        assert ("docker", 2) in report.missing_skills_ranked
        assert len(report.user_strong_skills) >= 1
