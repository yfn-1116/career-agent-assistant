import json
from pathlib import Path

from career_agent.service.agent_run import AgentRunResult


def test_knowledge_base_service_indexes_text_to_runtime_path(tmp_path):
    from career_agent.service.knowledge_base import KnowledgeBaseService

    service = KnowledgeBaseService(runtime_dir=tmp_path)
    result = service.index_text(
        "Python RAG Agent project with LangGraph workflow",
        source_name="profile.md",
    )

    assert result.chunk_count >= 1
    assert service.chunk_file == tmp_path / "knowledge_base" / "chunks.jsonl"
    assert service.chunk_file.is_file()
    lines = service.chunk_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == result.chunk_count
    assert json.loads(lines[0])["source_path"] == "profile.md"


def test_knowledge_base_service_saves_uploaded_text_file(tmp_path):
    from career_agent.service.knowledge_base import KnowledgeBaseService

    service = KnowledgeBaseService(runtime_dir=tmp_path)
    result = service.ingest_upload(
        filename="resume.txt",
        data=b"Python FastAPI RAG internship project",
    )

    assert result.chunk_count >= 1
    assert result.saved_path == tmp_path / "uploads" / "resume.txt"
    assert result.saved_path.read_text(encoding="utf-8") == "Python FastAPI RAG internship project"


def test_application_service_saves_agent_result(tmp_path):
    from career_agent.service.application_service import ApplicationService

    service = ApplicationService(runtime_dir=tmp_path)
    result = AgentRunResult(
        trace_id="trace-1",
        match_score=0.72,
        communication_script="您好，我对该岗位感兴趣。",
        generated_bullets=["- Built a RAG demo"],
        report_path="outputs/demo/report.md",
        diagnostics_path="outputs/diagnostics/report.json",
        match_summary={
            "matched_skills": ["python"],
            "missing_skills": ["docker"],
        },
    )

    record = service.save_from_agent_result(
        result,
        job_title="AI Agent Intern",
        company="DemoCo",
        jd_text="Python RAG Agent",
    )

    assert record.application_id
    assert record.job_title == "AI Agent Intern"
    assert record.match_score == 0.72
    assert service.repository.count() == 1
    assert service.repository.get(record.application_id).trace_id == "trace-1"
