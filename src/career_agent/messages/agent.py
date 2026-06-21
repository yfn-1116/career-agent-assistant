"""Message Agent — generates platform-specific communication scripts."""

from __future__ import annotations
import dataclasses
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid


@dataclass
class MessageDraft:
    message_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    platform: str = "boss"
    message_type: str = "greeting"
    text: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    source_paths: list[str] = field(default_factory=list)
    risk_warnings: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in dataclasses.fields(self)}


class MessageAgent:
    """Generate HR communication scripts grounded in evidence."""

    def generate(
        self,
        message_type: str,
        job_title: str = "",
        company: str = "",
        matched_skills: list[str] | None = None,
        strengths: list[str] | None = None,
        evidence_paths: list[str] | None = None,
        tone: str = "concise",
        hr_question: str = "",
    ) -> MessageDraft:
        skills = matched_skills or []
        ev_paths = evidence_paths or []

        if message_type == "boss_greeting":
            text = self._boss_greeting(job_title, company, skills, tone)
        elif message_type == "email_intro":
            text = self._email_intro(job_title, company, skills, tone)
        elif message_type == "hr_reply":
            text = self._hr_reply(hr_question, skills, strengths or [])
        elif message_type == "follow_up":
            text = self._follow_up(job_title, company)
        else:
            text = self._boss_greeting(job_title, company, skills, tone)

        warnings = []
        if not skills:
            warnings.append("无匹配技能，建议谨慎联系或先补充经历")
        if not ev_paths:
            warnings.append("无 evidence source，话术可能无法支撑")

        return MessageDraft(
            platform="boss" if "boss" in message_type else "email",
            message_type=message_type,
            text=text,
            evidence_ids=[],
            source_paths=ev_paths,
            risk_warnings=warnings,
        )

    @staticmethod
    def _boss_greeting(job_title: str, company: str, skills: list[str], tone: str) -> str:
        skill_str = "、".join(skills[:3]) if skills else "Python 和 AI 应用开发"
        company_str = f"{company}的" if company else ""
        return (
            f"您好，我是人工智能专业本科生，最近在做一个基于 LangGraph + RAG 的"
            f"智能投递辅助 Agent 项目。"
            f"看到{company_str}{job_title or '该岗位'}提到 {skill_str}，"
            f"感觉比较匹配，想了解一下具体实习任务和要求。"
        )

    @staticmethod
    def _email_intro(job_title: str, company: str, skills: list[str], tone: str) -> str:
        return (
            f"尊敬的{company or '招聘负责人'}您好，\n\n"
            f"我对{job_title or '贵司实习岗位'}非常感兴趣。"
            f"我的项目经历覆盖 {', '.join(skills[:5]) if skills else 'Python 和 AI 应用开发'}，"
            f"附上简历供参考。期待有机会进一步沟通！"
        )

    @staticmethod
    def _hr_reply(question: str, skills: list[str], strengths: list[str]) -> str:
        if "项目" in question or "经验" in question:
            proj = strengths[0] if strengths else "有一个基于 LangGraph + RAG 的 Agent 项目"
            return f"有的。{proj}，具体来说包含了 JD 解析、资料库检索、检索评分和简历定制生成。如果您方便，我可以发一份详细的项目说明。"
        if "时间" in question or "到岗" in question:
            return "我目前课程已结束，随时可以到岗，每周可以保证 5 天实习。"
        if "实习" in question and "多久" in question:
            return "可以实习 3-6 个月，具体可以协商。"
        return f"好的。关于您提到的这一点，我可以进一步说明。{strengths[0] if strengths else '我具备相关经验'}。"

    @staticmethod
    def _follow_up(job_title: str, company: str) -> str:
        return f"您好，之前和您沟通过{company or ''}{job_title or '该岗位'}，想再了解一下进展。如果有需要补充的材料我可以提供。谢谢！"
