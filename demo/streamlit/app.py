"""求职投递管家 — 上传资料 → 分析 → 搜岗位 → 生成话术+简历 → 记录"""

import sys, tempfile, os, json, uuid
from pathlib import Path
from datetime import datetime, timezone
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "src"))

import streamlit as st

st.set_page_config(page_title="求职投递管家", page_icon="🤖", layout="wide")

# ---- Session Init ----
for k, v in {
    "messages": [], "kb_chunks": 0, "github_repos": [],
    "profile_summary": "", "applications": [],
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---- Helpers ----
def _rag_index(content, source_name="upload"):
    """将文本导入 RAG 知识库"""
    import hashlib
    from career_agent.rag.schemas import ProfileDocument
    from career_agent.rag.chunking.text_chunker import TextChunker
    from career_agent.rag.vectorstores.memory_store import MemoryVectorStore
    doc_id = hashlib.sha256(source_name.encode()).hexdigest()[:16]
    doc = ProfileDocument(document_id=doc_id, source_path=source_name, title=source_name, content=content, item_type="profile")
    chunks = TextChunker().chunk_document(doc)
    if "kw_store" not in st.session_state:
        st.session_state["kw_store"] = MemoryVectorStore()
    st.session_state["kw_store"].add_chunks(chunks)
    st.session_state.kb_chunks += len(chunks)
    return len(chunks)

def _llm(prompt, system="你是专业的求职顾问助手"):
    """调用千问 LLM"""
    from career_agent.infrastructure.llm.qwen_provider import QwenProvider
    llm = QwenProvider()
    if llm.is_available:
        return llm.generate(prompt, system_prompt=system)
    return None

def _save_application(job_title, company, jd_text, match_score, message, resume_md):
    """保存投递记录 JSONL"""
    record = {
        "id": uuid.uuid4().hex[:12],
        "company": company, "job_title": job_title, "jd_text": jd_text[:500],
        "match_score": match_score, "message": message, "resume": resume_md[:500],
        "status": "analyzed", "created_at": datetime.now(timezone.utc).isoformat()
    }
    st.session_state.applications.append(record)
    Path("data/applications").mkdir(parents=True, exist_ok=True)
    with open("data/applications/applications.jsonl", "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record["id"]

# ---- Sidebar: Knowledge Base ----
with st.sidebar:
    st.header("📁 知识库")
    st.metric("已索引", st.session_state.kb_chunks)

    # File upload
    uploaded = st.file_uploader("上传简历/项目", type=["pdf","docx","md","txt"], accept_multiple_files=True, key="up")
    if uploaded and st.button("📥 导入文件"):
        for f in uploaded:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(f.name).suffix) as tmp:
                tmp.write(f.read()); tp = tmp.name
            try:
                from career_agent.rag.loaders.file_loader import FileLoader
                doc = FileLoader().load(tp)
                n = _rag_index(doc.content, f.name)
                st.success(f"✅ {f.name} → {n} chunks")
                os.unlink(tp)
            except Exception as e:
                st.error(f"❌ {f.name}: {e}")
        st.rerun()

    # GitHub
    st.divider()
    repo = st.text_input("GitHub 仓库", placeholder="用户名/仓库名")
    if st.button("🔗 读取并导入"):
        if repo.strip():
            import urllib.request
            try:
                url = f"https://raw.githubusercontent.com/{repo.strip()}/main/README.md"
                req = urllib.request.Request(url, headers={"User-Agent": "smart-apply"})
                with urllib.request.urlopen(req, timeout=10) as r:
                    content = r.read().decode("utf-8", errors="replace")
                n = _rag_index(content, f"github:{repo.strip()}")
                st.session_state.github_repos.append(repo.strip())
                st.success(f"✅ {repo} → {n} chunks")
            except Exception as e:
                st.error(f"❌ {e}")
            st.rerun()

    # Profile status
    if st.session_state.github_repos:
        st.caption("已读仓库:")
        for r in st.session_state.github_repos:
            st.caption(f"  • {r}")

    st.divider()
    if st.button("🔍 分析我的Profile"):
        if st.session_state.kb_chunks > 0:
            with st.spinner("LLM 分析中..."):
                summary = _llm(
                    f"用户已上传 {st.session_state.kb_chunks} 条资料。请分析用户的技能、项目、优势、适合的岗位方向，100字以内。",
                    "你是求职顾问，简洁分析用户画像。"
                )
                st.session_state.profile_summary = summary or "LLM 不可用"
        else:
            st.warning("请先上传资料")
    if st.session_state.profile_summary:
        st.info(st.session_state.profile_summary)

# ---- Main Chat ----
st.title("🤖 求职投递管家")
st.caption("上传简历和GitHub → 粘贴JD → 生成话术+简历 → 保存记录")

# Chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input
col1, col2 = st.columns([5, 1])
with col1:
    user_input = st.text_area("📝", placeholder="粘贴岗位 JD，或输入「帮我分析适合什么岗位」「搜一下 Agent 实习」", label_visibility="collapsed", height=80)
with col2:
    st.write(""); st.write("")
    mode = st.selectbox("模式", ["分析+话术+简历", "只看匹配", "批量筛选", "生成话术", "生成简历"], label_visibility="collapsed")
    send = st.button("🚀 发送", use_container_width=True, type="primary")

if send and user_input.strip():
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)
    with st.chat_message("assistant"):
        with st.spinner("检索资料 + 大模型分析..."):

            # Step 1: RAG pipeline
            from career_agent.service.agent_run import AgentRunRequest, AgentRunService
            svc = AgentRunService(profile_dir="data/samples/profile")
            result = svc.run(AgentRunRequest(user_message=user_input, raw_jd=user_input, mode="analyze_job"))

            # Step 2: LLM analysis
            llm_answer = _llm(
                f"""用户Profile: {st.session_state.profile_summary}
知识库: {st.session_state.kb_chunks} 条资料
GitHub: {', '.join(st.session_state.github_repos)}

RAG 分析结果: {result.final_answer[:2000]}

用户输入: {user_input}

请输出:
1. **匹配度评估** (一句话)
2. **你的优势** (3-5 bullet)
3. **需要准备的** (3 bullet)
4. **建议沟通话术** (一段,100字内)
5. **建议搜索关键词** (5个)
6. **下一步行动** (2-3项)""",
                "你是实习求职投递管家。简洁、精准、可执行。不编造经历。"
            ) or result.final_answer

            st.markdown(llm_answer)

            # Step 3: Auto-save if JD detected
            if "岗位" in user_input or "JD" in user_input.upper() or "要求" in user_input:
                app_id = _save_application(
                    job_title=user_input.split("\n")[0][:50],
                    company="", jd_text=user_input,
                    match_score=result.match_score,
                    message=result.communication_script,
                    resume_md="\n".join(result.generated_bullets)
                )
                st.success(f"📌 已保存投递记录 #{app_id}")

            st.session_state.messages.append({"role": "assistant", "content": llm_answer})

# ---- Footer: Application Records ----
st.divider()
st.subheader("📋 投递记录")
if not st.session_state.applications:
    st.caption("暂无记录。分析岗位后自动保存。")
else:
    for app in reversed(st.session_state.applications[-5:]):
        with st.expander(f"{app['job_title'][:40]} | 匹配 {app['match_score']:.0%} | {app['status']}"):
            st.markdown(f"**话术**: {app.get('message','')[:200]}")
            st.markdown(f"**简历**: {app.get('resume','')[:200]}")
            st.caption(f"ID: {app['id']} | {app['created_at']}")
