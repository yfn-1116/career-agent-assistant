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
_TEXT, _MUTED, _BORDER, _BG = "#111827", "#6b7280", "#e5e7eb", "#f9fafb"

# -- Chinese labels --
L_MATCH = "匹配度"
L_RETRIEVAL = "检索质量"
L_ACTION = "投递建议"
L_STATUS = "状态"
L_RESUME = "简历修改建议"
L_HR_MSG = "HR 沟通话术"
L_EV_USED = "本次使用的证据"
L_CAN_WRITE = "可直接写入简历"
L_NEEDS_CONF = "需要用户确认"
L_LEARN_ONLY = "仅作为学习计划"
L_SOURCES = "资料来源"
L_COPY_HINT = "选中上方文本即可复制"
L_DISCLAIMER = "此内容由 AI 生成，请核实后使用。系统不会自动发送消息或联系任何人。"
L_NO_EV = "当前知识库中缺少充分证据，不能直接写进简历。"

# ============================================================================
# Empty state
# ============================================================================

def render_empty_state() -> None:
    """DeepSeek-style centered empty state."""
    st.markdown(
        '<div class="empty-state">'
        '<div class="logo">🤖</div>'
        "<h1>实习投递智能助手</h1>"
        '<p class="subtitle">基于证据约束的实习投递 Agent</p>'
        "</div>",
        unsafe_allow_html=True,
    )


def render_guide_cards() -> None:
    """No guide cards in DeepSeek style — pass."""
    pass


# ============================================================================
# Chat messages
# ============================================================================

def render_chat_messages(messages: list[dict]) -> None:
    for msg in messages:
        role = msg.get("role", "user")
        mtype = msg.get("type", "text")
        with st.chat_message(role):
            content = msg.get("content", "")
            # For user messages, truncate long JD display
            if role == "user" and len(content) > 300:
                # Show first line as summary + collapsible full text
                first_line = content.split("\n")[0][:100]
                st.caption(f"📄 {first_line}…")
                with st.expander("查看完整输入"):
                    st.markdown(content)
            elif content:
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
    elif mtype == "github_ingest":
        _render_github_ingest_inline(data)


# ============================================================================
# Analysis renderer — objective, with risks
# ============================================================================

def _render_analysis_inline(data: dict) -> None:
    result = data.get("result")
    if result is None:
        return

    match_score = _sf(getattr(result, "match_score", None))
    retrieval_score = _sf(getattr(result, "retrieval_total_score", None))
    evidence_n = len(list(getattr(result, "evidence_sources", []) or []))
    warn_n = len(list(getattr(result, "warnings", []) or []))
    meta = getattr(result, "metadata", None) or {}

    # ---- tiered recommendation ----
    if match_score is not None:
        if match_score >= 0.80:
            tier = "强烈建议投递"
            tier_emoji = "🟢"
            tier_note = "匹配度较高，核心技能与岗位要求吻合。"
        elif match_score >= 0.65:
            tier = "建议调整简历后投递"
            tier_emoji = "🟡"
            tier_note = "整体匹配，但部分技能需要突出展示。建议优化简历后再投递。"
        elif match_score >= 0.50:
            tier = "可以尝试投递"
            tier_emoji = "🟠"
            tier_note = "匹配度一般，可与该岗位保持联系，同时建议补充短板技能。"
        else:
            tier = "暂不建议作为重点岗位"
            tier_emoji = "🔴"
            tier_note = "匹配度偏低，建议先补充相关项目经历或技能后再尝试。"
    else:
        tier, tier_emoji, tier_note = "—", "", ""

    # ---- strengths & risks from evidence ----
    match_summary = getattr(result, "match_summary", {}) or {}
    matched_skills = match_summary.get("matched_skills", [])
    missing_skills = match_summary.get("missing_skills", [])

    lines = [
        f"### {tier_emoji} {tier}",
        f"**匹配度**：{match_score:.0%}" if match_score is not None else "**匹配度**：—",
        f"**检索质量**：{retrieval_score:.0%}" if retrieval_score is not None else "",
        "",
        tier_note,
    ]
    if matched_skills:
        lines.append(f"\n**匹配优势**：{', '.join(matched_skills[:8])}")
    if missing_skills:
        lines.append(f"\n**需要补强的技能**：{', '.join(missing_skills[:8])}")
    if evidence_n < 3:
        lines.append(f"\n⚠️ 仅检索到 {evidence_n} 条证据，分析结果仅供参考。")
    if warn_n:
        lines.append(f"\n⚠️ 存在 {warn_n} 条警告，请注意核实。")

    st.markdown("\n".join(filter(None, lines)))

    # ---- metric cards ----
    metrics = [
        (L_MATCH, f"{match_score:.0%}" if match_score is not None else "—"),
        (L_RETRIEVAL, f"{retrieval_score:.0%}" if retrieval_score is not None else "—"),
        (L_ACTION, tier),
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
        items = "".join(f"<div>· {_html.escape(str(w))}</div>" for w in warnings)
        st.markdown(f'<div class="risk-box">{items}</div>', unsafe_allow_html=True)

    # ---- resume advice cards ----
    constraints = meta.get("output_constraints", {}) or {}
    bullet_map = list(constraints.get("bullet_evidence_map", []) or [])
    can_write = list(getattr(result, "can_write_claims", []) or [])
    needs_conf = list(meta.get("needs_confirmation_claims", []))
    learning = list(meta.get("learning_plan_claims", []))
    if not can_write and not needs_conf and not learning:
        bullets = list(getattr(result, "generated_bullets", []) or [])
        if bullets:
            needs_conf = bullets

    if can_write or needs_conf or learning:
        st.markdown(f"### {L_RESUME}")
        _render_resume_advice_cards(can_write, needs_conf, learning, bullet_map, matched_skills, missing_skills)

    # ---- HR message (tone-adjusted) ----
    msg = getattr(result, "communication_script", "") or ""
    if msg.strip():
        st.markdown(f"### {L_HR_MSG}")
        if match_score is not None and match_score < 0.50:
            st.caption("⚠️ 匹配度较低，以下话术仅供参考，建议先补充能力。")
        st.markdown(f'<div class="msg-card">{_html.escape(msg)}</div>', unsafe_allow_html=True)
        st.caption(L_COPY_HINT)
        st.markdown(f'<div class="msg-disclaimer">{L_DISCLAIMER}</div>', unsafe_allow_html=True)

    # ---- evidence (collapsed) ----
    if bullet_map:
        implemented = [m for m in bullet_map if m.get("status") == "implemented"]
        designed = [m for m in bullet_map if m.get("status") == "designed"]
        planned = [m for m in bullet_map if m.get("status") not in ("implemented", "designed")]
        n_impl = len(implemented)
        summary = f"本次生成基于 {n_impl} 条可写入简历的证据"
        if warn_n:
            summary += f"，{warn_n} 条警告"
        if evidence_n < 3:
            summary += "。" + L_NO_EV

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


def _render_resume_advice_cards(
    can_write: list[str], needs_conf: list[str], learning: list[str],
    bullet_map: list[dict], matched_skills: list[str], missing_skills: list[str],
) -> None:
    """Render resume rewrite advice as detailed cards with JD mapping."""
    all_claims = (
        [("can-write", c) for c in can_write] +
        [("needs-confirm", c) for c in needs_conf] +
        [("learn-only", c) for c in learning]
    )
    if not all_claims:
        st.caption("暂无简历修改建议。")
        return

    status_label = {"can-write": "可直接写入简历", "needs-confirm": "需要确认", "learn-only": "仅作为学习计划"}
    status_cls = {"can-write": "can-write", "needs-confirm": "needs-confirm", "learn-only": "learn-only"}

    for i, (status, claim) in enumerate(all_claims, 1):
        # Find matching evidence from bullet_map
        ev_info = {}
        for bm in bullet_map:
            if bm.get("bullet", "") and _html.escape(str(bm.get("bullet", "")))[:80] in claim[:120]:
                ev_info = bm
                break

        # Pick a relevant JD skill for context
        jd_context = ""
        if matched_skills and i <= len(matched_skills):
            jd_context = f"对应岗位要求中的「{matched_skills[i-1]}」能力"
        elif missing_skills and i <= len(matched_skills) + len(missing_skills):
            idx = i - len(matched_skills) - 1
            if idx >= 0 and idx < len(missing_skills):
                jd_context = f"岗位要求「{missing_skills[idx]}」，当前证据不足"

        clean_claim = _html.escape(str(claim))[:400]
        source = ev_info.get("source_path", "知识库") if ev_info else "知识库"

        # Generate rewrite reason based on status
        if status == "can-write":
            reason = "该经历有充分证据支撑，可直接用于简历。建议突出与岗位要求的对应关系。"
        elif status == "needs-confirm":
            reason = "该内容来自设计阶段或不确定来源，建议核实后再决定是否写入简历。"
        else:
            reason = "当前证据不足以支撑该表述为真实经历，仅可作为学习方向参考。"

        st.markdown(
            f'<div class="advice-card">'
            f'<strong>建议 {i}</strong>'
            f'<div class="jd-req">{_html.escape(jd_context)}</div>'
            f'<div class="rewrite">{clean_claim}</div>'
            f'<div class="reason">改写理由：{reason}</div>'
            f'<div class="source">证据来源：{_html.escape(str(source))}</div>'
            f'<span class="status-tag {status_cls.get(status, "")}">{status_label.get(status, status)}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ============================================================================
# Other inline renderers
# ============================================================================

def _render_message_inline(data: dict) -> None:
    msg = data.get("message", "") or data.get("communication_script", "")
    if not msg:
        return
    st.markdown(f"### {L_HR_MSG}")
    st.markdown(f'<div class="msg-card">{_html.escape(msg)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="msg-disclaimer">{L_DISCLAIMER}</div>', unsafe_allow_html=True)
    sources = data.get("evidence_sources", [])
    if sources:
        st.caption(f"证据来源：{', '.join(sources[:5])}")
    warnings = data.get("warnings", [])
    if warnings:
        items = "".join(f"<div>· {_html.escape(str(w))}</div>" for w in warnings)
        st.markdown(f'<div class="risk-box">{items}</div>', unsafe_allow_html=True)


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
                st.caption(f'· {s.get("source_name", "?")}（{s.get("source_type", "?")}，{s.get("chunk_count", 0)} 条片段）')


def _render_github_ingest_inline(data: dict) -> None:
    count = data.get("repo_count", 0)
    repos = data.get("repos", [])
    st.caption(f"已拉取 {count} 个 GitHub 仓库。")
    if repos:
        with st.expander("仓库列表"):
            for r in repos:
                st.caption(f"· {r}")


# ============================================================================
# Sidebar — candidate profile
# ============================================================================

def render_sidebar_logo() -> None:
    st.markdown(
        '<div style="font-size:1rem;font-weight:700;color:#111827;padding:0.3rem 0 0.3rem 0;">'
        "实习投递智能助手"
        "</div>",
        unsafe_allow_html=True,
    )


def render_sidebar_nav_section(label: str) -> None:
    st.markdown(f'<div class="sidebar-nav-section">{label}</div>', unsafe_allow_html=True)


def render_candidate_profile(kb_service) -> None:
    """Render a compact candidate profile in the sidebar from KB data."""
    render_sidebar_nav_section("候选人画像")

    # Try to build profile from KB
    summary = kb_service.get_summary()
    sources = kb_service.get_source_details()
    profile_text = kb_service.get_profile_text()

    if profile_text:
        # Extract key info deterministically from profile text
        skills = _extract_skills_from_text(profile_text)
        projects = _extract_projects_from_text(profile_text)
        direction = _guess_direction(skills, projects)

        st.markdown(
            f'<div class="sidebar-profile">'
            f'<div><span class="label">求职方向</span><br><span class="val">{direction}</span></div>'
            f'<div style="margin-top:0.4rem;"><span class="label">核心技能</span><br>'
            f'<span class="val">{", ".join(skills[:8]) if skills else "待补充"}</span></div>'
            f'<div style="margin-top:0.4rem;"><span class="label">代表项目</span><br>'
            f'<span class="val">{", ".join(projects[:3]) if projects else "待补充"}</span></div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.caption("暂无数据。上传简历或拉取 GitHub 仓库后自动生成。")

    # KB stats
    chunks = summary.get("chunk_count", 0)
    srcs = summary.get("source_count", 0)
    repos = summary.get("repo_count", 0)
    st.markdown(
        f'<div class="sidebar-kb-stat" style="margin-top:0.5rem;">'
        f'<span class="num">{chunks}</span> 个片段 · '
        f'<span class="num">{srcs}</span> 个来源 · '
        f'<span class="num">{repos}</span> 个仓库'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Expandable sources
    if sources:
        with st.expander(f"{L_SOURCES}（{len(sources)} 个）"):
            for s in sources:
                st.caption(
                    f'· {s.get("source_name", "?")} '
                    f'（{s.get("source_type", "?")}，{s.get("chunk_count", 0)} 条）'
                )


def _extract_skills_from_text(text: str) -> list[str]:
    """Deterministic skill extraction from profile text."""
    import re
    skill_patterns = [
        "Python", "FastAPI", "Streamlit", "LangChain", "LangGraph", "RAG",
        "PyTorch", "TensorFlow", "Docker", "Git", "SQL", "API",
        "Agent", "LLM", "Embedding", "向量数据库", "Chroma", "FAISS",
        "React", "TypeScript", "JavaScript", "C++", "Java", "Go",
        "机器学习", "深度学习", "CV", "NLP",
    ]
    found = []
    text_lower = text.lower()
    for s in skill_patterns:
        if s.lower() in text_lower:
            found.append(s)
    return found[:10] if found else ["Python", "AI 应用开发"]


def _extract_projects_from_text(text: str) -> list[str]:
    """Deterministic project extraction."""
    import re
    projects = []
    for m in re.finditer(r"##\s*(?:项目|Project)\s*\d*[：:]\s*(.+)|#\s*(.+?)(?:\n|$)", text):
        name = (m.group(1) or m.group(2) or "").strip()
        if name and len(name) > 3 and "说明" not in name and "脱敏" not in name:
            projects.append(name[:40])
    return projects[:5] if projects else []


def _guess_direction(skills: list[str], projects: list[str]) -> str:
    """Guess career direction from skills."""
    s = " ".join(skills).lower()
    if "rag" in s or "langchain" in s or "langgraph" in s or "agent" in s:
        return "AI Agent / RAG 开发"
    if "fastapi" in s or "api" in s or "docker" in s:
        return "后端开发"
    if "pytorch" in s or "tensorflow" in s or "机器学习" in s:
        return "机器学习 / AI"
    return "通用技术岗"


# ============================================================================
# Sidebar controls (simplified)
# ============================================================================

def render_sidebar_demo_controls() -> tuple[bool, bool]:
    st.caption("演示")
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
                f'<div class="ev-item"><div>{bullet}</div>'
                f'<div class="ev-meta"><code>{eid}</code> · {src} · {status}</div></div>',
                unsafe_allow_html=True,
            )


def _sf(value: Any) -> float | None:
    if value is None:
        return None
    try:
        f = float(value)
        return f if f == f else None
    except (TypeError, ValueError):
        return None
