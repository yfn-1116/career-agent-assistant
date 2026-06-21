"""FastAPI Browser Assistant API — local agent service for Chrome extension."""

from __future__ import annotations
import uuid
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from career_agent.api.schemas import BrowserAgentResult, BrowserPageSnapshot
from career_agent.service.agent_run import AgentRunRequest, AgentRunService

app = FastAPI(title="Smart Apply Browser API", version="1.3")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

SVC = AgentRunService(profile_dir=str(Path(__file__).resolve().parents[3] / "data" / "samples" / "profile"))


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.3", "agent": "Smart Apply Browser Assistant"}


@app.post("/api/browser/analyze-current-page")
def analyze_current_page(snapshot: BrowserPageSnapshot):
    """Analyze current browser page — job detail, job list, or chat."""
    page_type, errors, warnings = _classify_page(snapshot), [], []

    if page_type == "job_detail":
        return _handle_job_detail(snapshot)
    elif page_type == "job_list":
        return _handle_job_list(snapshot)
    elif page_type == "chat":
        return _handle_chat(snapshot)
    else:
        warnings.append("Unable to classify page type — paste the JD text or try a job detail page")
        return BrowserAgentResult(page_type="unknown", warnings=warnings, next_action="manual_paste").to_dict()


def _classify_page(snapshot: BrowserPageSnapshot) -> str:
    text = snapshot.text.lower()
    title = snapshot.title.lower()
    url = snapshot.url.lower()

    # Job detail FIRST — explicit signals take priority
    job_signals = ["岗位要求", "岗位职责", "任职要求", "职位描述", "工作内容"]
    if any(s in text for s in job_signals) and len(text) < 3000:
        return "job_detail"

    # Chat indicators
    import re as _re
    chat_patterns = [r"\bhr\b", r"\b你好\b", r"\b您好\b", "看到你的简历", "聊天", "沟通", "消息"]
    chat_count = sum(1 for p in chat_patterns if _re.search(p, text[:800]) or p in title)
    if chat_count >= 2 and len(text) < 2000:
        return "chat"

    # Job list indicators
    list_signals = ["搜索", "search", "岗位列表", "推荐", "result", "找到"]
    if any(s in title or s in url for s in list_signals) and text.count("岗位") >= 2:
        return "job_list"
    if (text.count("实习") + text.count("招聘")) >= 5:
        return "job_list"

    # Job detail indicators
    job_signals = ["岗位要求", "岗位职责", "任职要求", "职位描述", "工作内容", "薪资", "地点"]
    if any(s in text for s in job_signals):
        return "job_detail"
    if any(s in text for s in ["Python", "Java", "实习", "招聘", "公司"]) and len(text) > 100:
        return "job_detail"

    return "unknown"


def _handle_job_detail(snapshot: BrowserPageSnapshot) -> dict:
    from career_agent.job_sources.parser import JobPostingParser
    from career_agent.hiring_intent.analyzer import HiringIntentAnalyzer
    from career_agent.messages.agent import MessageAgent
    from career_agent.resume.pdf_exporter import export_pdf

    parser = JobPostingParser()
    posting = parser.parse(snapshot.text, platform=snapshot.platform)
    ha = HiringIntentAnalyzer()
    intent = ha.analyze(jd_text=snapshot.text, hard_skills=posting.hard_skills, job_title=posting.job_title)

    # Run main agent
    req = AgentRunRequest(user_message=snapshot.text, raw_jd=snapshot.text, mode="analyze_job")
    result = SVC.run(req)

    # Generate message
    msg = MessageAgent().generate("boss_greeting", job_title=posting.job_title, matched_skills=posting.hard_skills[:3])

    # PDF resume
    pdf = export_pdf(f"outputs/resumes/{result.trace_id[:8]}.pdf",
                     profile_info={"name": "Candidate"}, match_result=result.match_summary,
                     generated_bullets=result.generated_bullets)

    return BrowserAgentResult(
        page_type="job_detail",
        job_posting=posting.to_dict(),
        match_score=result.match_score,
        hiring_intent_score=intent.hiring_intent_score,
        opportunity_score=max(0, min(1, 0.5*result.match_score + 0.35*intent.hiring_intent_score - 0.2*intent.risk_score)),
        recommended_action=result.recommended_action or intent.recommended_action,
        message_draft=msg.to_dict(),
        verification_questions=intent.verification_questions,
        resume_paths=[pdf],
        next_action="copy_message_and_send",
    ).to_dict()


def _handle_job_list(snapshot: BrowserPageSnapshot) -> dict:
    from career_agent.job_sources.parser import JobPostingParser
    from career_agent.discovery.ranker import JobRanker
    from career_agent.profile.loader import ProfileLoader
    from career_agent.rag.loaders.markdown_loader import MarkdownProfileLoader

    parser = JobPostingParser()
    postings = parser.parse_batch(snapshot.text)
    loader = ProfileLoader()
    md_loader = MarkdownProfileLoader()
    docs = md_loader.load_directory(str(Path(__file__).resolve().parents[3] / "data" / "samples" / "profile"))
    items = loader.load_documents(docs)

    ranker = JobRanker()
    ranked = ranker.rank(postings, items)

    top = []
    for rj in ranked[:5]:
        jp = rj.job_posting
        top.append({
            "job_title": jp.job_title, "company": jp.company,
            "match_score": rj.match_score, "recommended_action": rj.recommended_action,
            "matched_skills": rj.matched_skills, "missing_skills": rj.missing_skills,
            "reason_summary": rj.reason_summary, "message_preview": rj.generated_message_preview,
        })

    return BrowserAgentResult(
        page_type="job_list", ranked_jobs=top,
        recommended_action="review_top_candidates",
        next_action="select_job_for_detail_analysis",
    ).to_dict()


def _handle_chat(snapshot: BrowserPageSnapshot) -> dict:
    from career_agent.conversation.reply import HRReplyAssistant

    assistant = HRReplyAssistant()
    reply = assistant.suggest(snapshot.text)

    return BrowserAgentResult(
        page_type="chat",
        reply_suggestion=reply.to_dict(),
        next_action="copy_reply_and_send",
        warnings=["请确认回复内容后再发送", "不自动发送消息"],
    ).to_dict()
