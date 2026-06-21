"""Human Approval Gate — all send actions require user confirmation."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid

ACTIONS_REQUIRING_APPROVAL = [
    "send_greeting", "send_hr_reply", "send_resume",
    "mark_message_sent", "mark_resume_sent", "browser_click_send",
]


@dataclass
class ApprovalRequest:
    approval_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    action_type: str = ""
    target: str = ""  # company, job_title, or recipient
    preview_text: str = ""
    risk_warnings: list[str] = field(default_factory=list)
    required: bool = True
    status: str = "pending"  # pending / approved / rejected
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in self.__dataclass_fields__}


class ApprovalGate:
    """Check if an action requires human approval."""

    def check(self, action_type: str, preview_text: str = "", target: str = "") -> ApprovalRequest:
        required = action_type in ACTIONS_REQUIRING_APPROVAL
        warnings = []
        if required:
            warnings.append(f"动作 '{action_type}' 需要人工确认后才能执行")
        if not preview_text:
            warnings.append("预览文本为空，请确认内容")

        return ApprovalRequest(
            action_type=action_type,
            target=target,
            preview_text=preview_text,
            risk_warnings=warnings,
            required=required,
        )

    def approve(self, req: ApprovalRequest) -> ApprovalRequest:
        req.status = "approved"
        return req

    def reject(self, req: ApprovalRequest) -> ApprovalRequest:
        req.status = "rejected"
        return req
