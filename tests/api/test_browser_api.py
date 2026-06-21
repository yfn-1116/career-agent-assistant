"""Tests for browser API endpoints."""
import json
from pathlib import Path
from fastapi.testclient import TestClient
from career_agent.api.app import app

client = TestClient(app)
SAMPLES = Path(__file__).resolve().parents[2] / "data" / "browser_samples"


class TestHealth:
    def test_health(self):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


class TestJobDetail:
    def test_analyze_job_detail(self):
        text = (SAMPLES / "job_detail_boss.txt").read_text(encoding="utf-8")
        r = client.post("/api/browser/analyze-current-page", json={
            "url": "https://zhipin.com/job_detail/1", "title": "AI Agent 开发实习生",
            "platform": "boss", "text": text,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["page_type"] == "job_detail"
        assert data["job_posting"] is not None
        assert "match_score" in data
        assert data["match_score"] >= 0.0


class TestJobList:
    def test_analyze_job_list(self):
        text = (SAMPLES / "job_list_boss.txt").read_text(encoding="utf-8")
        r = client.post("/api/browser/analyze-current-page", json={
            "url": "https://zhipin.com/web/geek/job?query=AI", "title": "搜索AI实习",
            "platform": "boss", "text": text,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["page_type"] == "job_list"
        assert len(data["ranked_jobs"]) >= 1


class TestChat:
    def test_analyze_chat(self):
        text = (SAMPLES / "chat_boss.txt").read_text(encoding="utf-8")
        r = client.post("/api/browser/analyze-current-page", json={
            "url": "https://zhipin.com/chat/1", "title": "BOSS聊天",
            "platform": "boss", "text": text,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["page_type"] == "chat"
        assert data["reply_suggestion"] is not None
