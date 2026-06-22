"""Browser-extension service orchestration."""

from __future__ import annotations

import re

from career_agent.api.schemas import BrowserAgentResult, BrowserPageSnapshot
from career_agent.job_sources.parser import JobPostingParser
from career_agent.hiring_intent.analyzer import HiringIntentAnalyzer
from career_agent.resume.pdf_exporter import export_pdf
from career_agent.service.agent_run import AgentRunService


class BrowserAssistantService:
    """Classify browser snapshots and call backend services for responses."""

    def __init__(self, agent_service: AgentRunService | None = None) -> None:
        self.agent_service = agent_service or AgentRunService()

    def analyze_current_page(self, snapshot: BrowserPageSnapshot) -> BrowserAgentResult:
        page_type = self.classify_page(snapshot)
        if page_type == "job_detail":
            return self._handle_job_detail(snapshot)
        if page_type == "job_list":
            return self._handle_job_list(snapshot)
        if page_type == "chat":
            return self._handle_chat(snapshot)
        return BrowserAgentResult(
            page_type="unknown",
            warnings=["Unable to classify page type — paste the JD text or try a job detail page"],
            next_action="manual_paste",
        )

    @staticmethod
    def classify_page(snapshot: BrowserPageSnapshot) -> str:
        text = snapshot.text.lower()
        title = snapshot.title.lower()
        url = snapshot.url.lower()

        job_signals = ["岗位要求", "岗位职责", "任职要求", "职位描述", "工作内容"]
        if any(signal in text for signal in job_signals) and len(text) < 3000:
            return "job_detail"

        chat_patterns = [r"\bhr\b", r"\b你好\b", r"\b您好\b", "看到你的简历", "聊天", "沟通", "消息"]
        chat_count = sum(1 for pattern in chat_patterns if re.search(pattern, text[:800]) or pattern in title)
        if chat_count >= 2 and len(text) < 2000:
            return "chat"

        list_signals = ["搜索", "search", "岗位列表", "推荐", "result", "找到"]
        if any(signal in title or signal in url for signal in list_signals) and text.count("岗位") >= 2:
            return "job_list"
        if (text.count("实习") + text.count("招聘")) >= 5:
            return "job_list"

        job_detail_signals = ["岗位要求", "岗位职责", "任职要求", "职位描述", "工作内容", "薪资", "地点"]
        if any(signal in text for signal in job_detail_signals):
            return "job_detail"
        if any(signal in text for signal in ["python", "java", "实习", "招聘", "公司"]) and len(text) > 100:
            return "job_detail"
        return "unknown"

    def _handle_job_detail(self, snapshot: BrowserPageSnapshot) -> BrowserAgentResult:
        parser = JobPostingParser()
        posting = parser.parse(snapshot.text, platform=snapshot.platform)
        intent = HiringIntentAnalyzer().analyze(
            jd_text=snapshot.text,
            hard_skills=posting.hard_skills,
            job_title=posting.job_title,
        )
        result = self.agent_service.analyze_job(snapshot.text, user_message=snapshot.text)
        app_record = self.agent_service.save_application(
            result,
            job_title=posting.job_title or "unknown",
            company=posting.company,
            jd_text=snapshot.text,
        )
        msg_result = self.agent_service.generate_message(
            job_title=posting.job_title,
            company=posting.company,
            matched_skills=posting.hard_skills[:3],
            evidence_paths=result.evidence_sources,
        )
        pdf = export_pdf(
            f"outputs/resumes/{result.trace_id[:8]}.pdf",
            profile_info={"name": "Candidate"},
            match_result=result.match_summary,
            generated_bullets=result.generated_bullets,
        )
        return BrowserAgentResult(
            page_type="job_detail",
            job_posting=posting.to_dict(),
            match_score=result.match_score,
            hiring_intent_score=intent.hiring_intent_score,
            opportunity_score=max(
                0,
                min(1, 0.5 * result.match_score + 0.35 * intent.hiring_intent_score - 0.2 * intent.risk_score),
            ),
            recommended_action=result.recommended_action or intent.recommended_action,
            message_draft=msg_result.message_draft,
            verification_questions=intent.verification_questions,
            resume_paths=[pdf],
            application_record_id=app_record.application_id,
            next_action="copy_message_and_send",
            warnings=result.warnings,
        )

    def _handle_job_list(self, snapshot: BrowserPageSnapshot) -> BrowserAgentResult:
        result = self.agent_service.discover_jobs(snapshot.text)
        return BrowserAgentResult(
            page_type="job_list",
            ranked_jobs=list(result.metadata.get("ranked_jobs", [])),
            recommended_action="review_top_candidates",
            next_action="select_job_for_detail_analysis",
            warnings=result.warnings,
        )

    def _handle_chat(self, snapshot: BrowserPageSnapshot) -> BrowserAgentResult:
        result = self.agent_service.chat_about_job(snapshot.text)
        return BrowserAgentResult(
            page_type="chat",
            reply_suggestion=result.message_draft,
            next_action="copy_reply_and_send",
            warnings=["请确认回复内容后再发送", "不自动发送消息", *result.warnings],
        )
