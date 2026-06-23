"""Chat-first UI component renderers for the Internship Copilot demo.

Pure UI — no business logic, no RAG / repository / LangGraph calls.
All user-facing labels in Chinese.
"""

from __future__ import annotations

import html as _html
from pathlib import Path
from typing import Any

import streamlit as st

_REPO_ROOT = Path(__file__).resolve().parents[2]

_TEXT = "#111827"
_MUTED = "#6b7280"
_BORDER = "#e5e7eb"
_BG = "#f9fafb"

# -- Chinese label constants --
L_MATCH = "匹配度"
L_RETRIEVAL = "检索质量"
L_ACTION = "投递建议"
L_STATUS = "状态"
L_RESUME = "简历建议"
L_HR_MSG = "HR 沟通话术"
L_EV_USED = "本次使用的证据"
L_CAN_WRITE = "可直接写入简历"
L_NEEDS_CONF = "需要用户确认"
L_LEARN_ONLY = "仅作为学习计划"
L_SOURCES = "资料来源"
L_APPLICATIONS = "投递记录"
L_COPY_HINT = "选中上方文本即可复制"
L_DISCLAIMER = "此内容由 AI 生成，请核实后使用。系统不会自动发送消息或联系任何人。"
L_EV_SUMMARY = "本次生成基于 {n} 条可写入简历的证据"
L_NO_EV = "暂无详细证据映射（使用 LLM provider 可启用）"


# ============================================================================
# Empty state
# ============================================================================

def render_empty_state() -> None:
    st.markdown(
        '<div class="empty-state">'
        "<h1>实习投递智能助手</h1>"
        '<p class="subtitle">基于证据约束的实习投递 Agent</p>'
        "</div>",
        unsafe_allow_html=True,
    )
    st.caption(
        "粘贴岗位 JD、上传个人资料，或直接问我「这个岗位适合我吗？」"
        "我会基于你的知识库给出有证据支撑的建议。"
    )


# ============================================================================
# Chat message rendering
# ============================================================================

def render_chat_messages(messages: list[dict]) -> None:
    for msg in messages:
        role = msg.get("role", "user")
        mtype = msg.get("type", "text")
        with st.chat_message(role):
            content = msg.get("content", "")
            if content:
                st.markdown(content)
            data = msg.get("data")
            if data is not None:
                _render_message_data(mtype, data)


def _render_message_data(mtype: str, data: dict) -> None:
    if mtype == "analysis":
        _render_analysis_inline(data)
    elif mtype == "message":
        _render_message_inline(data)
    elif mtype == "profile":
        _render_profile_inline(data)
    elif mtype == "kb_overview":
        _render_kb_inline(data)
    elif mtype == "github_ingest":
        _render_github_ingest_inline(data)


# ============================================================================
# Inline renderers
# ============================================================================

def _render_analysis_inline(data: dict) -> None:
    result = data.get("result")
    if result is None:
        return

    # ---- metrics ----
    match_score = _sf(getattr(result, "match_score", None))
    retrieval_score = _sf(getattr(result, "retrieval_total_score", None))
    action_raw = (
        getattr(result, "recommended_action", "")
        or getattr(result, "decision", "")
        or "—"
    )
    evidence_n = len(list(getattr(result, "evidence_sources", []) or []))
    warn_n = len(list(getattr(result, "warnings", []) or []))

    metrics = [
        (L_MATCH, f"{match_score:.0%}" if match_score is not None else "—"),
        (L_RETRIEVAL, f"{retrieval_score:.0%}" if retrieval_score is not None else "—"),
        (L_ACTION, _fmt_action(action_raw)),
        (L_STATUS, f"{evidence_n} 条证据" + (f"，{warn_n} 条警告" if warn_n else "")),
    ]
    cards = "".join(
        f'<div class="inline-metric"><div class="val">{v}</div><div class="lbl">{l}</div></div>'
        for l, v in metrics
    )
    st.markdown(f'<div class="inline-metrics">{cards}</div>', unsafe_allow_html=True)

    # ---- warnings ----
    warnings = list(getattr(result, "warnings", []) or [])
    if warnings:
        _warn_inline(warnings)

    # ---- resume bullets ----
    can_write = list(getattr(result, "can_write_claims", []) or [])
    needs_conf = []
    learning = []
    meta = getattr(result, "metadata", None) or {}
    if meta:
        needs_conf = list(meta.get("needs_confirmation_claims", []))
        learning = list(meta.get("learning_plan_claims", []))
    if not can_write and not needs_conf and not learning:
        bullets = list(getattr(result, "generated_bullets", []) or [])
        if bullets:
            needs_conf = bullets

    if can_write or needs_conf or learning:
        st.markdown(f"**{L_RESUME}**")
        _bullet_group(L_CAN_WRITE, can_write, True)
        _bullet_group(L_NEEDS_CONF, needs_conf, not can_write)
        _bullet_group(L_LEARN_ONLY, learning, False)

    # ---- HR message ----
    msg = getattr(result, "communication_script", "") or ""
    if msg.strip():
        st.markdown(f"**{L_HR_MSG}**")
        st.markdown(
            f'<div class="msg-card">{_html.escape(msg)}</div>',
            unsafe_allow_html=True,
        )
        st.caption(L_COPY_HINT)
        st.markdown(
            f'<div class="msg-disclaimer">{L_DISCLAIMER}</div>',
            unsafe_allow_html=True,
        )

    # ---- evidence (collapsed summary) ----
    constraints = meta.get("output_constraints", {}) or {}
    bullet_map = list(constraints.get("bullet_evidence_map", []) or [])

    if bullet_map:
        implemented = [m for m in bullet_map if m.get("status") == "implemented"]
        designed = [m for m in bullet_map if m.get("status") == "designed"]
        planned = [m for m in bullet_map if m.get("status") not in ("implemented", "designed")]

        n_impl = len(implemented)
        summary_text = L_EV_SUMMARY.format(n=n_impl)
        if warn_n:
            summary_text += f"，{warn_n} 条警告"
        st.caption(summary_text)

        with st.expander(f"🔍 {L_EV_USED}（{len(bullet_map)} 条）"):
            _ev_group(L_CAN_WRITE, implemented, True)
            _ev_group(L_NEEDS_CONF, designed, len(designed) > 0 and not implemented)
            _ev_group(L_LEARN_ONLY, planned, False)
    else:
        sources = list(getattr(result, "evidence_sources", []) or [])
        if sources:
            st.caption(f"证据来源：{', '.join(sources[:5])}")
        else:
            st.caption(L_NO_EV)

    # ---- approval ----
    if getattr(result, "approval_required", False):
        _warn_inline(["需要用户确认后才能使用以上建议。"])


def _render_message_inline(data: dict) -> None:
    msg = data.get("message", "") or data.get("communication_script", "")
    if not msg:
        return
    st.markdown(f"**{L_HR_MSG}**")
    st.markdown(f'<div class="msg-card">{_html.escape(msg)}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="msg-disclaimer">{L_DISCLAIMER}</div>',
        unsafe_allow_html=True,
    )
    sources = data.get("evidence_sources", [])
    if sources:
        st.caption(f"证据来源：{', '.join(sources[:5])}")
    warnings = data.get("warnings", [])
    if warnings:
        _warn_inline(warnings)


def _render_profile_inline(data: dict) -> None:
    summary = data.get("summary", "")
    sources = data.get("sources", [])

    if summary:
        st.info(summary)
    else:
        st.info("已索引你的知识库。粘贴岗位 JD 即可进行匹配分析。")

    if sources:
        with st.expander(f"{L_SOURCES}（{len(sources)} 个）"):
            for s in sources:
                st.caption(
                    f'· {s.get("source_name", "?")} '
                    f'（{s.get("source_type", "?")}，{s.get("chunk_count", 0)} 条片段）'
                )


def _render_kb_inline(data: dict) -> None:
    sources = data.get("sources", [])
    if sources:
        with st.expander(f"{L_SOURCES}（{len(sources)} 个）"):
            for s in sources:
                st.caption(
                    f'· {s.get("source_name", "?")} '
                    f'（{s.get("source_type", "?")}，{s.get("chunk_count", 0)} 条片段）'
                )


def _render_github_ingest_inline(data: dict) -> None:
    count = data.get("repo_count", 0)
    repos = data.get("repos", [])
    st.caption(f"已拉取 {count} 个 GitHub 仓库。")
    if repos:
        with st.expander("仓库列表"):
            for r in repos:
                st.caption(f"· {r}")


# ============================================================================
# Evidence Gate (compact, default-collapsed)
# ============================================================================

def render_evidence_gate(result: Any) -> None:
    meta = getattr(result, "metadata", None) or {}
    constraints = meta.get("output_constraints", {}) or {}
    bullet_map = list(constraints.get("bullet_evidence_map", []) or [])
    if not bullet_map:
        return
    implemented = [m for m in bullet_map if m.get("status") == "implemented"]
    designed = [m for m in bullet_map if m.get("status") == "designed"]
    planned = [m for m in bullet_map if m.get("status") not in ("implemented", "designed")]
    with st.expander(f"🔍 {L_EV_USED}（{len(bullet_map)} 条）"):
        _ev_group(L_CAN_WRITE, implemented, True)
        _ev_group(L_NEEDS_CONF, designed, not implemented)
        _ev_group(L_LEARN_ONLY, planned, False)


# ============================================================================
# Application Records
# ============================================================================

def render_application_records(applications: list[dict[str, Any]], max_items: int = 10) -> None:
    if not applications:
        return
    for app in list(reversed(applications))[-max_items:]:
        title = str(app.get("job_title", "未知"))[:60]
        company = app.get("company", "") or "—"
        score = _sf(app.get("match_score"))
        status = str(app.get("status", "analyzed"))
        created = str(app.get("created_at", ""))[:10]
        label = f"{title} · {company}"
        if score is not None:
            label += f" · {score:.0%}"
        with st.expander(label):
            c1, c2, c3 = st.columns(3)
            c1.caption(f"状态：{status}")
            c2.caption(f"匹配度：{score:.0%}" if score is not None else "匹配度：—")
            c3.caption(f"日期：{created or '—'}")


def render_sidebar_recent_apps(applications: list[dict[str, Any]], n: int = 3) -> None:
    """Render recent N apps in sidebar — very compact."""
    if not applications:
        st.caption("暂无投递记录")
        return
    recent = list(reversed(applications))[-n:]
    for app in reversed(recent):
        title = str(app.get("job_title", "未知"))[:25]
        score = _sf(app.get("match_score"))
        pct = f"{score:.0%}" if score is not None else "—"
        st.caption(f"· {title}（{pct}）")


# ============================================================================
# Sidebar components
# ============================================================================

def render_sidebar_logo() -> None:
    st.markdown(
        '<div style="font-size:1rem;font-weight:700;color:#111827;padding:0.3rem 0 0.5rem 0;">'
        "实习投递智能助手"
        "</div>",
        unsafe_allow_html=True,
    )


def render_sidebar_nav_section(label: str) -> None:
    st.markdown(
        f'<div class="sidebar-nav-section">{label}</div>',
        unsafe_allow_html=True,
    )


def render_sidebar_kb_stats(kb_summary: dict) -> None:
    chunks = kb_summary.get("chunk_count", 0)
    sources = kb_summary.get("source_count", 0)
    repos = kb_summary.get("repo_count", 0)
    st.markdown(
        f'<div class="sidebar-kb-stat">'
        f'<span class="num">{chunks}</span> 个片段 · '
        f'<span class="num">{sources}</span> 个来源 · '
        f'<span class="num">{repos}</span> 个仓库'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_sidebar_pipeline() -> None:
    st.caption("处理流程")
    st.markdown(
        '<div class="pipeline-box">'
        '<span class="step">JD 输入</span>'
        '<span class="arrow">→</span>'
        '<span class="step">RAG 检索</span>'
        '<span class="arrow">→</span>'
        '<span class="step">证据门控</span>'
        '<span class="arrow">→</span>'
        '<span class="step">生成结果</span>'
        "</div>",
        unsafe_allow_html=True,
    )


def render_sidebar_demo_controls() -> tuple[bool, bool]:
    load = st.button("📂 加载示例 JD", use_container_width=True)
    clear = st.button("🧹 清空对话", use_container_width=True)
    return load, clear


def load_sample_jd_text() -> str:
    path = _REPO_ROOT / "data" / "samples" / "jobs" / "agent_intern_jd.md"
    try:
        return path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return ""


# ============================================================================
# Internal helpers
# ============================================================================

def _bullet_group(label: str, items: list[str], expanded: bool) -> None:
    if not items:
        return
    with st.expander(f"{label}（{len(items)} 条）", expanded=expanded):
        for item in items:
            st.markdown(
                f'<div style="font-size:0.85rem;padding:0.15rem 0;">'
                f'{_html.escape(str(item))[:350]}'
                f'</div>',
                unsafe_allow_html=True,
            )


def _ev_group(label: str, items: list[dict], expanded: bool) -> None:
    if not items:
        return
    with st.expander(f"{label}（{len(items)} 条）", expanded=expanded):
        for item in items:
            bullet = _html.escape(str(item.get("bullet", "—")))[:280]
            eid = _html.escape(str(item.get("evidence_id", "—")))
            src = _html.escape(str(item.get("source_path", "—")))
            status = str(item.get("status", "unknown"))
            st.markdown(
                f'<div class="ev-item">'
                f'<div>{bullet}</div>'
                f'<div class="ev-meta">'
                f"<code>{eid}</code> · {src} · {status}"
                f"</div></div>",
                unsafe_allow_html=True,
            )


def _warn_inline(warnings: list[str]) -> None:
    if not warnings:
        return
    items = "".join(f"<div>· {_html.escape(str(w))}</div>" for w in warnings)
    st.markdown(f'<div class="warn-box">{items}</div>', unsafe_allow_html=True)


def _sf(value: Any) -> float | None:
    if value is None:
        return None
    try:
        f = float(value)
        return f if f == f else None
    except (TypeError, ValueError):
        return None


def _fmt_action(a: str) -> str:
    m = {
        "strong_apply": "强烈建议投递",
        "apply_with_resume_adjustment": "建议调整简历后投递",
        "apply_only_if_interested": "感兴趣可投递",
        "skip": "建议跳过",
        "not_priority": "优先度较低",
        "fallback": "资料不足",
        "continue": "可继续",
    }
    return m.get(a, a.replace("_", " ").title())
