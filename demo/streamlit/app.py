"""Smart Apply Agent — Chat-first Streamlit UI for the Internship Copilot demo."""

from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "src"))

import streamlit as st

from career_agent.service.agent_run import AgentRunRequest, AgentRunService
from career_agent.service.application_service import ApplicationService
from career_agent.service.knowledge_base import KnowledgeBaseService

from styles import inject_custom_css
from ui_components import (
    load_sample_jd_text,
    render_application_records,
    render_chat_messages,
    render_empty_state,
    render_sidebar_demo_controls,
    render_sidebar_kb_stats,
    render_sidebar_logo,
    render_sidebar_nav_section,
    render_sidebar_pipeline,
    render_sidebar_recent_apps,
)


PROFILE_DIR = str(_REPO_ROOT / "data" / "samples" / "profile")
OUTPUT_DIR = str(_REPO_ROOT / "outputs" / "demo")

# -- Intent keywords (Chinese + English) --
_JD_TOKENS = [
    "岗位要求", "岗位职责", "任职要求", "职位描述", "JD", "招聘", "薪资", "实习",
    "岗位", "工作内容", "技能要求",
]
_MSG_TOKENS = ["话术", "沟通", "打招呼", "回复", "HR", "联系", "消息"]
_RESUME_TOKENS = ["简历", "bullet", "项目描述", "写进简历", "怎么写", "项目经历"]
_PROFILE_TOKENS = [
    "知道我", "我的资料", "profile", "evidence", "source", "sources",
    "知识库", "上传了", "什么信息", "了解我", "我的能力", "我的项目",
    "我有什么", "我的技能", "个人画像",
]
_MATCH_TOKENS = ["适合我吗", "匹配", "适不适合", "能不能投", "帮我看看", "分析一下",
                 "帮我分析", "投递建议"]
_GITHUB_URL = "github.com"


@st.cache_resource
def _services() -> tuple[KnowledgeBaseService, ApplicationService, AgentRunService]:
    return (
        KnowledgeBaseService(),
        ApplicationService(),
        AgentRunService(profile_dir=PROFILE_DIR),
    )


def _llm(prompt: str, system: str = "你是专业的求职顾问助手") -> str | None:
    try:
        from career_agent.infrastructure.llm.qwen_provider import QwenProvider
        llm = QwenProvider()
        if llm.is_available:
            return llm.generate(prompt, system_prompt=system)
    except Exception:
        return None
    return None


def _refresh_runtime_state(
    kb_service: KnowledgeBaseService, app_service: ApplicationService
) -> None:
    summary = kb_service.get_summary()
    st.session_state.kb_chunks = summary["chunk_count"]
    st.session_state.kb_sources = summary["source_count"]
    st.session_state.kb_repos = summary["repo_count"]
    st.session_state.github_repos = kb_service.load_github_repos()
    st.session_state.applications = [
        record.to_dict() for record in app_service.repository.list_all()
    ]


def _route_intent(text: str) -> str:
    """Lightweight keyword-based intent routing.
    Returns: analyze_job, generate_message, tailor_resume,
             show_profile, github_ingest, chat.
    """
    t = text.lower()
    # 1. GitHub URL
    if _GITHUB_URL in t:
        return "github_ingest"
    # 2. Job description (long text with JD keywords)
    if len(text) > 200 and any(kw in text for kw in _JD_TOKENS):
        return "analyze_job"
    # 3. HR message request
    if any(kw in text for kw in _MSG_TOKENS):
        return "generate_message"
    # 4. Resume / bullet request
    if any(kw in text for kw in _RESUME_TOKENS):
        return "tailor_resume"
    # 5. Profile / KB query
    if any(kw in t for kw in _PROFILE_TOKENS):
        return "show_profile"
    # 6. Match / analysis query
    if any(kw in text for kw in _MATCH_TOKENS):
        return "analyze_job"
    # 7. Short JD-like text
    if any(kw in text for kw in _JD_TOKENS):
        return "analyze_job"
    # 8. General chat
    return "chat"


def _run_analysis(user_msg: str, agent_service: AgentRunService) -> dict:
    result = agent_service.run(
        AgentRunRequest(user_message=user_msg, raw_jd=user_msg, mode="analyze_job"),
        output_dir=OUTPUT_DIR,
    )
    match_pct = f"{result.match_score:.0%}" if result.match_score else "N/A"
    action_cn = _fmt_action_cn(result.recommended_action or result.decision or "")
    lines = [
        f"**匹配度**：{match_pct}",
        f"**投递建议**：{action_cn}",
    ]
    if result.generated_bullets:
        lines.append(f"已生成 {len(result.generated_bullets)} 条简历建议。")
    if result.communication_script:
        lines.append("已生成 HR 沟通话术，见下方。")
    return {
        "role": "assistant",
        "content": "\n\n".join(lines),
        "type": "analysis",
        "data": {"result": result},
    }


def _run_message(user_msg: str, agent_service: AgentRunService) -> dict:
    result = agent_service.generate_message(job_title="目标岗位")
    return {
        "role": "assistant",
        "content": "以下是生成的 HR 沟通话术：",
        "type": "message",
        "data": {
            "message": result.communication_script,
            "evidence_sources": result.evidence_sources,
            "warnings": result.warnings,
        },
    }


def _run_profile(kb_service: KnowledgeBaseService) -> dict:
    summary = kb_service.get_summary()
    sources = kb_service.get_source_details()
    profile_text = kb_service.get_profile_text()

    if profile_text:
        system = "你是求职顾问。根据以下用户资料，用100字以内总结用户背景、技能、适合的岗位方向。只基于提供的资料，不要编造。"
        profile_summary = _llm(profile_text, system)
    else:
        profile_summary = None

    return {
        "role": "assistant",
        "content": (
            profile_summary
            or "已索引你的知识库。粘贴岗位 JD 即可进行匹配分析。"
        ),
        "type": "profile",
        "data": {"summary": profile_summary, "sources": sources, "stats": summary},
    }


def _run_github_ingest(user_msg: str, kb_service: KnowledgeBaseService) -> dict:
    import re
    match = re.search(r"github\.com/([^/\s]+/[^/\s]+)", user_msg)
    if match:
        repo = match.group(1).rstrip("/")
        try:
            result = kb_service.ingest_github_repo(repo)
            return {
                "role": "assistant",
                "content": f"已拉取 **{repo}**：索引了 {result.chunk_count} 条片段。",
                "type": "github_ingest",
                "data": {"repo_count": 1, "repos": [repo]},
            }
        except Exception:
            return {
                "role": "assistant",
                "content": f"无法拉取 {repo}，请确认仓库是公开的。",
                "type": "text",
            }
    user_match = re.search(r"github\.com/([^/\s]+)/?$", user_msg)
    if user_match:
        username = user_match.group(1).rstrip("/")
        try:
            count = kb_service.ingest_github_user(username)
            repos = kb_service.load_github_repos()
            return {
                "role": "assistant",
                "content": f"已拉取 **{username}** 的公开仓库：{count} 个已索引。",
                "type": "github_ingest",
                "data": {"repo_count": count, "repos": repos[-count:] if count else []},
            }
        except Exception:
            return {
                "role": "assistant",
                "content": f"无法拉取 {username} 的仓库。",
                "type": "text",
            }
    return {
        "role": "assistant",
        "content": "请提供完整的 GitHub 链接（如 https://github.com/owner/repo）。",
        "type": "text",
    }


def _run_chat(user_msg: str, kb_service: KnowledgeBaseService) -> dict:
    evidence = kb_service.search(user_msg, top_k=5) if st.session_state.kb_chunks else []
    sources = kb_service.list_sources()
    snippets = "\n".join(
        f"[{item.source_path}] {item.content[:200]}" for item in evidence
    )
    context = f"""你是用户的求职顾问，像朋友一样聊天。简洁、真诚。

知识库文件: {sources or '暂无'}
GitHub: {', '.join(st.session_state.github_repos) if st.session_state.github_repos else '暂无'}
已索引: {st.session_state.kb_chunks} 条
用户画像: {st.session_state.profile_summary or ''}

检索结果:
{snippets}

用户问: {user_msg}

规则: 基于检索内容回答，引用具体文件名。不要声称已自动投递或自动联系HR。"""
    answer = _llm(context, "你是求职顾问，能看到用户上传的资料索引。简洁、真诚。")
    return {
        "role": "assistant",
        "content": answer or "已检索你的知识库。建议粘贴岗位 JD 或具体描述需求，我可以做更精准的分析。",
        "type": "text",
    }


def _fmt_action_cn(a: str) -> str:
    m = {
        "strong_apply": "强烈建议投递",
        "apply_with_resume_adjustment": "建议调整简历后投递",
        "apply_only_if_interested": "感兴趣可投递",
        "skip": "建议跳过",
        "not_priority": "优先度较低",
        "fallback": "资料不足，建议补充",
        "continue": "可继续",
    }
    return m.get(a, a)


# ============================================================================
# Page config
# ============================================================================

st.set_page_config(page_title="实习投递智能助手", page_icon="🤖", layout="wide")
inject_custom_css()

kb_service, app_service, agent_service = _services()

# -- session state --
_defaults = {
    "messages": [],
    "profile_summary": "",
    "applications": [],
    "github_repos": [],
    "kb_chunks": 0,
    "kb_sources": 0,
    "kb_repos": 0,
}
for key, value in _defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

_refresh_runtime_state(kb_service, app_service)

# ============================================================================
# Sidebar
# ============================================================================

with st.sidebar:
    render_sidebar_logo()

    # -- New Analysis --
    if st.button("＋ 新建分析", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    # -- Knowledge Base --
    render_sidebar_nav_section("知识库")
    kb_summary = kb_service.get_summary()
    render_sidebar_kb_stats(kb_summary)

    uploaded = st.file_uploader(
        "上传简历 / 项目资料",
        type=["pdf", "docx", "md", "txt"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if uploaded and st.button("导入文件", use_container_width=True):
        imported = []
        for file in uploaded:
            try:
                r = kb_service.ingest_upload(file.name, file.read())
                imported.append(f"✓ {file.name}（{r.chunk_count} 条片段）")
            except Exception:
                imported.append(f"✗ {file.name}")
        if imported:
            st.session_state.messages.append({
                "role": "assistant",
                "content": "文件导入完成：\n\n" + "\n".join(imported),
                "type": "text",
            })
        _refresh_runtime_state(kb_service, app_service)
        st.rerun()

    gh_user = st.text_input(
        "GitHub 用户名", placeholder="yfn-1116", label_visibility="collapsed"
    )
    if st.button("拉取 GitHub 仓库", use_container_width=True) and gh_user.strip():
        try:
            count = kb_service.ingest_github_user(gh_user.strip())
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"已拉取 **{gh_user}** 的公开仓库：{count} 个已索引。",
                "type": "text",
            })
            _refresh_runtime_state(kb_service, app_service)
        except Exception:
            st.error("拉取失败，请检查用户名。")
        st.rerun()

    if st.session_state.github_repos:
        with st.expander(f"{len(st.session_state.github_repos)} 个仓库"):
            for rn in st.session_state.github_repos:
                st.caption(f"· {rn}")

    st.divider()

    # -- Demo --
    render_sidebar_nav_section("演示")
    render_sidebar_pipeline()
    load_sample, clear_chat = render_sidebar_demo_controls()

    if load_sample:
        text = load_sample_jd_text()
        if text:
            st.session_state.messages.append({
                "role": "user", "content": text, "type": "text",
            })
            with st.spinner("分析中…"):
                msg = _run_analysis(text, agent_service)
                st.session_state.messages.append(msg)
                try:
                    app_service.save_from_agent_result(
                        msg["data"]["result"],
                        job_title=text.split("\n")[0][:50], company="", jd_text=text,
                    )
                except Exception:
                    pass
            _refresh_runtime_state(kb_service, app_service)
        else:
            st.warning("示例 JD 文件未找到。")
        st.rerun()

    if clear_chat:
        st.session_state.messages = []
        st.rerun()

    # -- Profile --
    st.divider()
    if st.button("分析个人画像", use_container_width=True):
        if st.session_state.kb_chunks > 0:
            msg = _run_profile(kb_service)
            st.session_state.messages.append(msg)
            st.rerun()
        else:
            st.warning("暂无知识库数据。")

    # -- Recent Applications --
    st.divider()
    render_sidebar_nav_section("最近投递")
    render_sidebar_recent_apps(st.session_state.applications, n=3)
    if st.session_state.applications:
        with st.expander(f"查看全部（{len(st.session_state.applications)} 条）"):
            render_application_records(st.session_state.applications, max_items=20)

# ============================================================================
# Main Area — pure chat
# ============================================================================

if not st.session_state.messages:
    render_empty_state()

render_chat_messages(st.session_state.messages)

# ============================================================================
# Chat Input
# ============================================================================

user_input = st.chat_input(
    "粘贴岗位 JD、输入 GitHub 链接，或直接问我「这个岗位适合我吗」……"
)

if user_input and user_input.strip():
    text = user_input.strip()

    st.session_state.messages.append({
        "role": "user", "content": text, "type": "text",
    })

    intent = _route_intent(text)

    with st.spinner("思考中…"):
        if intent == "analyze_job":
            msg = _run_analysis(text, agent_service)
            try:
                app_service.save_from_agent_result(
                    msg["data"]["result"],
                    job_title=text.split("\n")[0][:50], company="", jd_text=text,
                )
            except Exception:
                pass
            _refresh_runtime_state(kb_service, app_service)

        elif intent == "generate_message":
            msg = _run_message(text, agent_service)

        elif intent == "tailor_resume":
            msg = _run_analysis(text, agent_service)

        elif intent == "show_profile":
            msg = _run_profile(kb_service)

        elif intent == "github_ingest":
            msg = _run_github_ingest(text, kb_service)
            _refresh_runtime_state(kb_service, app_service)

        else:
            msg = _run_chat(text, kb_service)

        st.session_state.messages.append(msg)
        st.rerun()
