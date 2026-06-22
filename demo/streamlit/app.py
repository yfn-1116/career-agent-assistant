"""Smart Apply Agent — Streamlit UI for the Internship Copilot demo."""

from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "src"))

import streamlit as st

from career_agent.service.agent_run import AgentRunRequest, AgentRunService
from career_agent.service.application_service import ApplicationService
from career_agent.service.knowledge_base import KnowledgeBaseService


PROFILE_DIR = str(_REPO_ROOT / "data" / "samples" / "profile")
OUTPUT_DIR = str(_REPO_ROOT / "outputs" / "demo")


@st.cache_resource
def _services() -> tuple[KnowledgeBaseService, ApplicationService, AgentRunService]:
    return (
        KnowledgeBaseService(),
        ApplicationService(),
        AgentRunService(profile_dir=PROFILE_DIR),
    )


def _llm(prompt: str, system: str = "你是专业的求职顾问助手") -> str | None:
    """Optional Qwen LLM wrapper for conversational polish."""
    try:
        from career_agent.infrastructure.llm.qwen_provider import QwenProvider

        llm = QwenProvider()
        if llm.is_available:
            return llm.generate(prompt, system_prompt=system)
    except Exception:
        return None
    return None


def _refresh_runtime_state(kb_service: KnowledgeBaseService, app_service: ApplicationService) -> None:
    _, chunk_count = kb_service.load_store()
    st.session_state.kb_chunks = chunk_count
    st.session_state.github_repos = kb_service.load_github_repos()
    st.session_state.applications = [
        record.to_dict() for record in app_service.repository.list_all()
    ]


def _answer_general_question(
    user_input: str,
    kb_service: KnowledgeBaseService,
) -> str:
    evidence = kb_service.search(user_input, top_k=5) if st.session_state.kb_chunks else []
    sources = kb_service.list_sources()
    snippets = "\n".join(
        f"[{item.source_path}] {item.content[:200]}" for item in evidence
    )
    context = f"""你是用户的求职顾问，像朋友一样聊天。简洁、真诚。

知识库文件列表: {sources or '暂无'}
GitHub: {', '.join(st.session_state.github_repos) if st.session_state.github_repos else '暂无'}
已索引内容: {st.session_state.kb_chunks} 条
用户画像: {st.session_state.profile_summary or ''}

检索结果:
{snippets}

用户问: {user_input}

规则:
- 如果用户问是否看到简历或项目资料，根据知识库文件列表如实回答。
- 基于检索内容回答，尽量引用具体文件名。
- 不要声称已经自动投递或自动联系 HR。"""
    return _llm(context, "你是求职顾问，能看到用户上传的资料索引。简洁、真诚。") or (
        "当前 LLM 不可用。已读取本地知识库索引，建议粘贴岗位 JD 触发完整匹配分析。"
    )


def _is_job_input(text: str) -> bool:
    job_tokens = ["岗位要求", "岗位职责", "任职要求", "职位描述", "JD", "招聘", "薪资", "实习"]
    return len(text) > 200 or any(token in text for token in job_tokens)


st.set_page_config(page_title="Smart Apply Agent", page_icon="🤖", layout="wide")
kb_service, app_service, agent_service = _services()

for key, value in {
    "messages": [],
    "profile_summary": "",
    "applications": [],
    "github_repos": [],
    "kb_chunks": 0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = value

_refresh_runtime_state(kb_service, app_service)

with st.sidebar:
    st.header("📁 知识库")
    st.metric("已索引", st.session_state.kb_chunks)

    uploaded = st.file_uploader(
        "上传简历/项目 (PDF/DOCX/MD/TXT)",
        type=["pdf", "docx", "md", "txt"],
        accept_multiple_files=True,
    )
    if uploaded and st.button("📥 导入到知识库"):
        for file in uploaded:
            st.info(f"📄 正在解析 {file.name}...")
            try:
                result = kb_service.ingest_upload(file.name, file.read())
                st.success(f"✅ {file.name} → {result.chunk_count} chunks")
            except Exception as exc:
                st.error(f"❌ {file.name}: 解析失败 - {exc}")
        st.rerun()

    st.divider()
    st.header("🔗 GitHub")
    gh_user = st.text_input("GitHub 用户名", placeholder="yfn-1116")
    if st.button("📥 读取所有公开仓库") and gh_user.strip():
        try:
            count = kb_service.ingest_github_user(gh_user.strip())
            st.success(f"✅ {count} 个仓库已导入知识库")
        except Exception as exc:
            st.error(f"获取仓库失败，请稍后重试: {exc}")
        st.rerun()

    repo = st.text_input("单个仓库", placeholder="用户名/仓库名")
    if st.button("🔗 读取这个仓库") and repo.strip():
        try:
            result = kb_service.ingest_github_repo(repo.strip())
            st.success(f"✅ {repo.strip()} → {result.chunk_count} chunks")
        except Exception as exc:
            st.error(f"❌ {repo.strip()}: {exc}")
        st.rerun()

    if st.session_state.github_repos:
        st.caption("已读仓库:")
        for repo_name in st.session_state.github_repos:
            st.caption(f"  • {repo_name}")

    st.divider()
    if st.button("🔍 分析我的 Profile"):
        if st.session_state.kb_chunks > 0:
            summary = _llm(
                f"用户已上传 {st.session_state.kb_chunks} 条资料。请分析用户的技能、项目、优势、适合的岗位方向，100字以内。",
                "你是求职顾问，简洁分析用户画像。",
            )
            st.session_state.profile_summary = summary or "LLM 不可用，已保留本地知识库索引。"
        else:
            st.warning("请先上传资料")
    if st.session_state.profile_summary:
        st.info(st.session_state.profile_summary)

st.title("Smart Apply Agent")
st.caption("Ask Agent：上传资料和 GitHub 摘要，粘贴 JD，生成匹配分析、话术和简历建议。不会自动投递或自动发送消息。")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Ask Agent about a job, resume, or pasted JD...")

if user_input and user_input.strip():
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("分析中..."):
            if _is_job_input(user_input):
                result = agent_service.run(
                    AgentRunRequest(
                        user_message=user_input,
                        raw_jd=user_input,
                        mode="analyze_job",
                    ),
                    output_dir=OUTPUT_DIR,
                )

                prompt = f"""你是一个实习求职投递管家。基于以下信息给用户一个自然、有用的回答。

用户画像: {st.session_state.profile_summary}
知识库: {st.session_state.kb_chunks} 条资料
GitHub: {', '.join(st.session_state.github_repos)}
RAG 检索: {result.final_answer[:2000]}
用户输入: {user_input}

请输出匹配判断、优势、不足、沟通建议和下一步行动。不要声称已经自动投递或自动发送。"""
                answer = _llm(prompt, "你是求职投递管家，简洁直接，不编造经历。") or result.final_answer

                record = app_service.save_from_agent_result(
                    result,
                    job_title=user_input.split("\n")[0][:50],
                    company="",
                    jd_text=user_input,
                )
                st.success(f"📌 已保存投递记录 #{record.application_id}")
            else:
                answer = _answer_general_question(user_input, kb_service)

            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

st.divider()
st.subheader("📋 投递记录")
_refresh_runtime_state(kb_service, app_service)
if not st.session_state.applications:
    st.caption("暂无记录。分析岗位后自动保存。")
else:
    for application in reversed(st.session_state.applications[-5:]):
        title = application.get("job_title", "未知岗位")[:40]
        score = float(application.get("match_score", 0.0))
        status = application.get("status", "analyzed")
        with st.expander(f"{title} | 匹配 {score:.0%} | {status}"):
            st.markdown(f"**话术**: {application.get('communication_script', '')[:200]}")
            st.caption(f"ID: {application.get('application_id', '')} | {application.get('created_at', '')}")
