"""HR Reply Assistant — generates context-aware replies to HR messages."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid


@dataclass
class ReplySuggestion:
    reply_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    original_message: str = ""
    suggested_reply: str = ""
    needs_user_input: list[str] = field(default_factory=list)
    risk_warnings: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in self.__dataclass_fields__}


class HRReplyAssistant:
    """Generate replies to common HR questions, grounded in user profile."""

    # Common HR question patterns
    _PATTERNS = {
        "ask_project": ["项目", "经验", "做过什么", "会什么"],
        "ask_availability": ["到岗", "时间", "多久", "几个月", "星期", "每周"],
        "ask_resume": ["简历", "发一份", "附件"],
        "ask_skill": ["会不会", "熟练", "掌握", "了解", "用过"],
        "rejection": ["不合适", "不考虑", "已招到", "满了", "抱歉", "不太合适", "不匹配"],
        "interview": ["面试", "聊聊", "面谈", "电话"],
    }

    def suggest(self, hr_message: str, context: dict[str, Any] | None = None) -> ReplySuggestion:
        ctx = context or {}
        msg_type = self._classify(hr_message)
        strengths = ctx.get("strengths", [])
        matched_skills = ctx.get("matched_skills", [])
        warnings = []
        needs_input = []

        if msg_type == "ask_project":
            reply = self._reply_project(strengths, matched_skills)
        elif msg_type == "ask_availability":
            reply = "我目前课程已结束，随时可以到岗，每周 5 天。具体到岗时间可以协商。"
            needs_input.append("请确认你的实际到岗时间和每周可实习天数")
        elif msg_type == "ask_resume":
            reply = "好的，这是我的简历，包含了我的项目经历和技术栈。如果有需要进一步了解的地方请随时问我。"
        elif msg_type == "ask_skill":
            skills_str = "、".join(matched_skills[:5]) if matched_skills else "相关技术"
            reply = f"我具备 {skills_str} 方面的经验，如果需要可以进一步展示具体项目。"
        elif msg_type == "rejection":
            reply = "好的，感谢您的回复。如果有其他合适的机会也请随时联系我，祝工作顺利！"
        elif msg_type == "interview":
            reply = "好的，没问题。我这边时间比较灵活，您方便什么时间？"
        else:
            reply = "好的。关于这一点我可以进一步说明，有什么需要了解的请随时问我。"
            needs_input.append("HR 问题较模糊，建议手动确认回复内容")

        if not matched_skills and msg_type in ("ask_skill", "ask_project"):
            warnings.append("匹配技能为空，回复可能缺乏支撑")

        return ReplySuggestion(
            original_message=hr_message,
            suggested_reply=reply,
            needs_user_input=needs_input,
            risk_warnings=warnings,
        )

    @staticmethod
    def _reply_project(strengths: list[str], matched_skills: list[str]) -> str:
        proj = strengths[0] if strengths else ""
        skills_str = "、".join(matched_skills[:3]) if matched_skills else "相关技术"
        if proj:
            return f"有的。{proj}。技术栈覆盖 {skills_str}，如果您方便，我可以发一份详细的项目说明。"
        return f"有的。我具备 {skills_str} 方面的项目经验，可以进一步展示。"

    def _classify(self, msg: str) -> str:
        for msg_type, keywords in self._PATTERNS.items():
            for kw in keywords:
                if kw in msg:
                    return msg_type
        return "general"
