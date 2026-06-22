from fastapi.testclient import TestClient

from career_agent.api.app import app


client = TestClient(app)

SAMPLE_JD = """# AI Agent 开发实习生

岗位要求：
- Python, LangGraph, RAG
- 熟悉 FastAPI 和工程化交付
"""


def test_health_schema():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"]
    assert data["service_name"] == "Internship Copilot API"


def test_jobs_analyze_returns_structured_response():
    response = client.post("/api/jobs/analyze", json={
        "title": "AI Agent 开发实习生",
        "company": "DemoCo",
        "jd_text": SAMPLE_JD,
        "source_url": "https://example.com/jobs/1",
        "platform": "demo",
    })

    assert response.status_code == 200
    data = response.json()
    assert "match_score" in data
    assert "opportunity_score" in data
    assert "recommendation" in data
    assert isinstance(data["matched_skills"], list)
    assert isinstance(data["missing_skills"], list)
    assert isinstance(data["evidence"], list)
    assert isinstance(data["warnings"], list)
    assert isinstance(data["approval_required"], bool)


def test_messages_generate_returns_message():
    response = client.post("/api/messages/generate", json={
        "jd_text": SAMPLE_JD,
        "tone": "concise",
        "user_goal": "打招呼",
    })

    assert response.status_code == 200
    data = response.json()
    assert data["message"]
    assert isinstance(data["evidence_used"], list)
    assert isinstance(data["warnings"], list)
    assert isinstance(data["approval_required"], bool)


def test_applications_create_and_list():
    create_response = client.post("/api/applications", json={
        "job_title": "Backend Intern",
        "company": "DemoCo",
        "source_url": "https://example.com/jobs/backend",
        "status": "planned",
        "notes": "Need resume tailoring",
        "generated_message": "您好，我对该岗位感兴趣。",
    })

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["id"]
    assert created["job_title"] == "Backend Intern"
    assert created["company"] == "DemoCo"
    assert created["status"] == "planned"

    list_response = client.get("/api/applications")
    assert list_response.status_code == 200
    items = list_response.json()
    assert isinstance(items, list)
    assert any(item["id"] == created["id"] for item in items)


def test_knowledge_upload_writes_runtime_index():
    response = client.post("/api/knowledge/upload", json={
        "filename": "profile-note.txt",
        "content": "Python RAG FastAPI internship project",
        "source_type": "text",
    })

    assert response.status_code == 200
    data = response.json()
    assert data["source_name"] == "profile-note.txt"
    assert data["chunk_count"] >= 1
    assert "runtime/knowledge_base" in data["index_path"]
