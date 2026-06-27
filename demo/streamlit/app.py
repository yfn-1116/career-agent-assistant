"""Smart Apply Agent — Chat-first Streamlit UI for the Internship Copilot demo."""

from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "src"))

import streamlit as st

from career_agent.agents.memory import ConversationMemory
from career_agent.agents.orchestrator import OrchestratorAgent
from career_agent.service.agent_run import AgentRunRequest, AgentRunService
from career_agent.service.application_service import ApplicationService
from career_agent.service.knowledge_base import KnowledgeBaseService

from styles import inject_custom_css
from ui_components import (
    load_sample_jd_text,
    render_candidate_profile,
    render_chat_messages,
    render_empty_state,
    render_guide_cards,
    render_sidebar_demo_controls,
    render_sidebar_logo,
    render_sidebar_nav_section,
)


PROFILE_DIR = str(_REPO_ROOT / "data" / "samples" / "profile")
OUTPUT_DIR = str(_REPO_ROOT / "outputs" / "demo")

# -- Intent keywords --
_JD_TOKENS = [
    "岗位要求", "岗位职责", "任职要求", "职位描述", "JD", "招聘", "薪资", "实习",
    "岗位", "工作内容", "技能要求",
]
_MSG_TOKENS = ["话术", "沟通", "打招呼", "回复", "HR", "联系", "消息"]
_RESUME_TOKENS = ["简历", "bullet", "项目描述", "写进简历", "怎么写", "项目经历",
                  "帮我改简历", "修改简历", "改写", "简历建议"]
_PROFILE_TOKENS = [
    "知道我", "我的资料", "profile", "evidence", "source", "sources",
    "知识库", "上传了", "什么信息", "了解我", "我的能力", "我的项目",
    "我有什么", "我的技能", "个人画像",
]
_MATCH_TOKENS = ["适合我吗", "匹配", "适不适合", "能不能投", "帮我看看", "分析一下",
                 "帮我分析", "投递建议", "帮我评估"]
_GITHUB_URL = "github.com"


@st.cache_resource(ttl=600)  # re-init every 10min to pick up config changes
def _services() -> tuple[KnowledgeBaseService, ApplicationService, AgentRunService, OrchestratorAgent]:
    kb = KnowledgeBaseService()
    app = ApplicationService()
    agent = AgentRunService(profile_dir=PROFILE_DIR)
    memory = ConversationMemory()

    # Create LLM provider for autonomous mode
    llm = None
    try:
        from career_agent.infrastructure.llm import create_llm_provider
        from career_agent.core.settings import Settings as _Settings
        llm = create_llm_provider(provider=_Settings().llm.provider)
    except Exception:
        pass

    # Create ToolRegistry for autonomous mode
    from career_agent.tools.registry import create_standard_registry
    tools = create_standard_registry()

    orch = OrchestratorAgent(
        memory=memory, kb_service=kb, agent_service=agent,
        tool_registry=tools, llm_provider=llm,
    )
    return kb, app, agent, orch


def _llm(prompt: str, system: str = "你是专业的求职顾问助手") -> str | None:
    try:
        from career_agent.infrastructure.llm.qwen_provider import QwenProvider
        llm = QwenProvider()
        if llm.is_available:
            return llm.generate(prompt, system_prompt=system)
    except Exception:
        return None
    return None


def _route_intent(text: str) -> str:
    t = text.lower()
    # JD + GitHub combo → analyze_job (not github_ingest)
    has_github = _GITHUB_URL in t
    has_jd = len(text) > 200 and any(kw in text for kw in _JD_TOKENS)
    if has_jd and any(kw in text for kw in _JD_TOKENS):
        return "analyze_job"
    if has_github and not has_jd:
        return "github_ingest"
    if any(kw in text for kw in _RESUME_TOKENS):
        return "tailor_resume"
    if any(kw in text for kw in _MSG_TOKENS):
        return "generate_message"
    if any(kw in t for kw in _PROFILE_TOKENS):
        return "show_profile"
    if any(kw in text for kw in _MATCH_TOKENS):
        return "analyze_job"
    if len(text) > 200 and any(kw in text for kw in _JD_TOKENS):
        return "analyze_job"
    if any(kw in text for kw in _JD_TOKENS):
        return "analyze_job"
    return "chat"


def _run_analysis(user_msg: str, agent_service: AgentRunService) -> dict:
    result = agent_service.run(
        AgentRunRequest(user_message=user_msg, raw_jd=user_msg, mode="analyze_job"),
        output_dir=OUTPUT_DIR,
    )
    match_pct = f"{result.match_score:.0%}" if result.match_score else "N/A"
    return {
        "role": "assistant",
        "content": f"**匹配度**：{match_pct}",
        "type": "analysis",
        "data": {"result": result},
    }


def _run_message(user_msg: str, agent_service: AgentRunService) -> dict:
    result = agent_service.generate_message(job_title="目标岗位")
    return {
        "role": "assistant", "content": "",
        "type": "message",
        "data": {
            "message": result.communication_script,
            "evidence_sources": result.evidence_sources,
            "warnings": result.warnings,
        },
    }


def _run_profile(kb_service: KnowledgeBaseService) -> dict:
    profile_text = kb_service.get_profile_text()
    if profile_text:
        system = "你是求职顾问。根据以下用户资料，用80字以内总结用户背景、技能、适合岗位方向。只基于资料，不编造。"
        ps = _llm(profile_text, system)
    else:
        ps = None
    return {
        "role": "assistant",
        "content": ps or "已索引你的知识库。粘贴岗位 JD 即可进行匹配分析。",
        "type": "profile",
        "data": {"summary": ps, "sources": kb_service.get_source_details()},
    }


def _run_github_ingest(user_msg: str, kb_service: KnowledgeBaseService) -> dict:
    import re
    match = re.search(r"github\.com/([^/\s]+/[^/\s]+)", user_msg)
    if match:
        repo = match.group(1).rstrip("/")
        try:
            r = kb_service.ingest_github_repo(repo)
            return {"role": "assistant", "content": f"已拉取 **{repo}**：索引了 {r.chunk_count} 条片段。", "type": "github_ingest", "data": {"repo_count": 1, "repos": [repo]}}
        except Exception:
            return {"role": "assistant", "content": f"无法拉取 {repo}，请确认仓库是公开的。", "type": "text"}
    user_match = re.search(r"github\.com/([^/\s]+)/?$", user_msg)
    if user_match:
        username = user_match.group(1).rstrip("/")
        try:
            count = kb_service.ingest_github_user(username)
            return {"role": "assistant", "content": f"已拉取 **{username}** 的公开仓库：{count} 个已索引。", "type": "github_ingest", "data": {"repo_count": count}}
        except Exception:
            return {"role": "assistant", "content": f"无法拉取 {username} 的仓库。", "type": "text"}
    return {"role": "assistant", "content": "请提供完整的 GitHub 链接。", "type": "text"}


def _run_chat(user_msg: str, kb_service: KnowledgeBaseService) -> dict:
    evidence = kb_service.search(user_msg, top_k=5) if st.session_state.get("kb_chunks", 0) else []
    sources = kb_service.list_sources()
    snippets = "\n".join(f"[{item.source_path}] {item.content[:200]}" for item in evidence)
    repos = st.session_state.get("github_repos", [])
    context = f"""你是用户的求职顾问。要客观、诚实，不要过度迎合。

知识库文件: {sources or '暂无'}
GitHub: {', '.join(repos) if repos else '暂无'}
已索引: {st.session_state.get('kb_chunks', 0)} 条

检索结果:
{snippets}

用户问: {user_msg}

规则:
- 基于检索内容回答，引用文件名。
- 如果证据不足，诚实告知。
- 不要声称已自动投递或联系HR。
- 如果用户问"适不适合"，给出客观分析，不要一味说适合。"""
    answer = _llm(context, "你是客观的求职顾问。基于资料回答，不迎合，不编造。")
    return {
        "role": "assistant",
        "content": answer or "已检索知识库。建议粘贴岗位 JD 或具体描述需求。",
        "type": "text",
    }


# ============================================================================
# Page config
# ============================================================================

st.set_page_config(page_title="实习投递智能助手", page_icon="🤖", layout="wide")
inject_custom_css()
kb_service, app_service, agent_service, orchestrator = _services()

_defaults = {
    "messages": [], "profile_summary": "", "applications": [],
    "github_repos": [], "kb_chunks": 0, "kb_sources": 0, "kb_repos": 0,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# refresh KB state
kb_summary = kb_service.get_summary()
st.session_state.kb_chunks = kb_summary["chunk_count"]
st.session_state.kb_sources = kb_summary["source_count"]
st.session_state.kb_repos = kb_summary["repo_count"]
st.session_state.github_repos = kb_service.load_github_repos()

# ============================================================================
# Sidebar — minimal: profile + KB
# ============================================================================

with st.sidebar:
    render_sidebar_logo()

    # -- New chat --
    if st.button("＋ 新建对话", use_container_width=True):
        st.session_state.messages = []
        orchestrator.memory.clear_short_term()
        st.rerun()

    st.divider()

    # -- Candidate Profile --
    render_candidate_profile(kb_service)

    st.divider()

    # -- Knowledge Base --
    render_sidebar_nav_section("知识库")

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
                imported.append(f"✓ {file.name}（{r.chunk_count} 条）")
            except Exception:
                imported.append(f"✗ {file.name}")
        if imported:
            st.session_state.messages.append({
                "role": "assistant", "content": "文件导入完成：\n\n" + "\n".join(imported), "type": "text",
            })
        st.rerun()

    gh_user = st.text_input("GitHub 用户名", placeholder="yfn-1116", label_visibility="collapsed")
    if st.button("拉取 GitHub", use_container_width=True) and gh_user.strip():
        try:
            count = kb_service.ingest_github_user(gh_user.strip())
            st.session_state.messages.append({
                "role": "assistant", "content": f"已拉取 **{gh_user}** 的公开仓库：{count} 个已索引。", "type": "text",
            })
        except Exception:
            st.error("拉取失败。")
        st.rerun()

    st.divider()

    # -- Demo controls --
    load_sample, clear_chat = render_sidebar_demo_controls()

    if load_sample:
        text = load_sample_jd_text()
        if text:
            st.session_state.messages.append({"role": "user", "content": text, "type": "text"})
            with st.spinner("分析中…"):
                resp = orchestrator.handle(text)
                msg = {"role": "assistant", "content": resp.message, "type": "analysis",
                       "data": {"result": resp.data.get("result"), "ppam": {
                           "intent": resp.intent,
                           "perception": resp.perception_summary,
                           "plan": resp.plan_summary,
                           "action": resp.action_summary,
                       }}}
                st.session_state.messages.append(msg)
                try:
                    app_service.save_from_agent_result(
                        msg["data"]["result"], job_title=text.split("\n")[0][:50], company="", jd_text=text,
                    )
                except Exception:
                    pass
        else:
            st.warning("示例 JD 未找到。")
        st.rerun()

    if clear_chat:
        st.session_state.messages = []
        orchestrator.memory.clear_short_term()
        st.rerun()

    # -- PPAM Trace --
    st.divider()
    with st.expander("🔍 PPAM 认知追踪"):
        mem_summary = orchestrator.memory.summary()
        st.caption(f"Memory: {mem_summary}")
        last_ppam = st.session_state.get("last_ppam", {})
        if last_ppam:
            st.caption(f"**意图**: {last_ppam.get('intent', '?')}")
            st.caption(f"**感知**: {last_ppam.get('perception', '?')}")
            st.caption(f"**规划**: {last_ppam.get('plan', '?')}")
            st.caption(f"**行动**: {last_ppam.get('action', '?')}")
        else:
            st.caption("尚未执行 PPAM 流程")

# ============================================================================
# Main Area — chat
# ============================================================================

if not st.session_state.messages:
    render_empty_state()
    render_guide_cards()

render_chat_messages(st.session_state.messages)

# ============================================================================
# Chat Input — native st.chat_input (best IME + Enter support)
# ============================================================================

user_input = st.chat_input(
    "粘贴岗位 JD、输入 GitHub 链接，或直接提问……"
)

if user_input and user_input.strip():
    text = user_input.strip()
    st.session_state.messages.append({"role": "user", "content": text, "type": "text"})

    with st.spinner("分析中…"):
        # Use OrchestratorAgent for full PPAM pipeline
        resp = orchestrator.handle(text)

        ppam_trace = {
            "intent": resp.intent,
            "perception": resp.perception_summary,
            "plan": resp.plan_summary,
            "action": resp.action_summary,
        }
        st.session_state["last_ppam"] = ppam_trace

        msg = {
            "role": "assistant",
            "content": resp.message,
            "type": "analysis" if resp.intent == "analyze_job" else "text",
            "data": {"result": resp.data.get("result"), "ppam": ppam_trace},
        }

        # Save application record if analysis was run
        if resp.intent == "analyze_job" and resp.data.get("result"):
            try:
                app_service.save_from_agent_result(
                    resp.data["result"],
                    job_title=text.split("\n")[0][:50],
                    company="",
                    jd_text=text,
                )
            except Exception:
                pass

        st.session_state.messages.append(msg)
        st.rerun()
