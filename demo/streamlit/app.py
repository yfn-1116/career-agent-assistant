"""Smart Apply Agent — Codex-like conversational Streamlit UI.

Usage::

    streamlit run demo/streamlit/app.py
"""

import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC = str(_REPO_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import streamlit as st
from career_agent.service.agent_run import AgentRunRequest, AgentRunService

PROFILE_DIR = str(_REPO_ROOT / "data" / "samples" / "profile")
JOBS_DIR = _REPO_ROOT / "data" / "samples" / "jobs"

JD_FILES = {
    "AI Agent 开发实习生": "agent_intern_jd.md",
    "RAG 工程师实习生": "rag_engineer_intern_jd.md",
    "AI 应用开发实习生": "ai_application_intern_jd.md",
    "后端开发实习生（AI 方向）": "backend_ai_intern_jd.md",
}

TEMPLATE_NAMES = ["default", "minimal", "full"]

# ---------------------------------------------------------------------------
st.set_page_config(page_title="Smart Apply Agent", page_icon="🤖", layout="wide")
st.title("🤖 Smart Apply Agent")
st.caption("粘贴 JD | 上传简历 | 生成匹配分析 + 简历")

# ---------------------------------------------------------------------------
# Sidebar: file upload + knowledge base
# ---------------------------------------------------------------------------
st.sidebar.header("📁 知识库")
uploaded_files = st.sidebar.file_uploader(
    "上传简历 / 项目文档 (PDF, DOCX, MD, TXT)",
    type=["pdf", "docx", "doc", "md", "txt"],
    accept_multiple_files=True,
    help="上传的文件会被解析并加入 RAG 检索知识库",
)

if uploaded_files:
    from career_agent.rag.loaders.file_loader import FileLoader
    from career_agent.rag.chunking.text_chunker import TextChunker
    from career_agent.rag.vectorstores.memory_store import MemoryVectorStore
    from career_agent.rag.pipeline import RAGPipeline

    loader, chunker = FileLoader(), TextChunker()
    for uf in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uf.name).suffix) as tmp:
            tmp.write(uf.read())
            tmp_path = tmp.name
        try:
            doc = loader.load(tmp_path)
            Path(tmp_path).unlink()
            st.sidebar.success(f"✅ {uf.name} → {doc.item_type}")
        except Exception as e:
            st.sidebar.error(f"❌ {uf.name}: {e}")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ 设置")
top_k = st.sidebar.slider("检索数量", 1, 10, 5)
mode = st.sidebar.selectbox("模式", ["analyze", "resume", "chat"])
jd_source = st.sidebar.radio("JD 来源", ["示例 JD", "手动粘贴"])

# ---------------------------------------------------------------------------
# Main input area
# ---------------------------------------------------------------------------
jd_text = ""

if jd_source == "示例 JD":
    selected_label = st.sidebar.selectbox("选择 JD", list(JD_FILES.keys()))
    jd_path = JOBS_DIR / JD_FILES[selected_label]
    if jd_path.is_file():
        jd_text = jd_path.read_text(encoding="utf-8")

col1, col2 = st.columns([4, 1])
with col1:
    user_input = st.text_area(
        "岗位 JD 或问题",
        value=jd_text if jd_text else "",
        placeholder="粘贴岗位 JD，或输入问题...\n\n「这个岗位我匹配吗？」「帮我生成一份简历」",
        height=160,
        label_visibility="collapsed",
    )
with col2:
    st.write(""); st.write("")
    analyze_btn = st.button("🚀 Ask Agent", type="primary", use_container_width=True)
    template_name = st.selectbox("简历模板", TEMPLATE_NAMES, help="生成完整简历时使用的模板")
    st.caption("")

if not analyze_btn:
    st.info("👆 粘贴 JD 或输入问题，也可在侧边栏上传简历/项目文件 → 点击 Ask Agent")
    st.stop()

if not user_input.strip():
    st.error("请输入 JD 文本或问题")
    st.stop()

# ---------------------------------------------------------------------------
# Run Agent
# ---------------------------------------------------------------------------
with st.spinner("Agent 正在分析..."):
    svc = AgentRunService(profile_dir=PROFILE_DIR)
    request = AgentRunRequest(user_message=user_input, raw_jd=user_input, mode=mode)
    result = svc.run(request)

if result.status == "failed":
    st.error("运行失败")
    st.stop()

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
g = result.retrieval_grade
grade_emoji = {"excellent": "🟢", "good": "🟢", "weak": "🟡", "failed": "🔴"}
st.markdown(
    f"### {grade_emoji.get(g, '')} {g.upper()} · "
    f"score={result.retrieval_total_score:.2f} · "
    f"retry {result.retry_count}次 · "
    f"`{result.trace_id[:8]}`"
)

# Final answer
st.markdown(result.final_answer)

# Communication
if result.communication_script:
    with st.expander("💬 HR 沟通话术"):
        st.info(result.communication_script)

# Warnings
for w in result.warnings:
    st.warning(w)

# ---------------------------------------------------------------------------
# Resume Generation (when mode=resume)
# ---------------------------------------------------------------------------
if mode == "resume":
    st.markdown("---")
    st.markdown("## 📝 生成简历")
    from career_agent.agents.resume_generator import ResumeGenerator

    gen = ResumeGenerator(template=template_name)
    profile_info = {
        "name": st.text_input("姓名", "姓名", key="profile_name"),
        "school": st.text_input("学校", key="profile_school"),
        "major": st.text_input("专业", key="profile_major"),
        "email": st.text_input("邮箱", key="profile_email"),
        "github": st.text_input("GitHub", key="profile_github"),
    }
    if st.button("📄 生成完整简历", type="primary"):
        resume_md = gen.generate(
            parsed_jd=None, generated_output=None, match_analysis=None,
            profile_info=profile_info,
        )
        st.download_button(
            "⬇️ 下载简历 (Markdown)",
            resume_md,
            file_name=f"resume_{result.trace_id[:8]}.md",
            mime="text/markdown",
        )
        st.markdown(resume_md)

# ---------------------------------------------------------------------------
# Expandable details
# ---------------------------------------------------------------------------
with st.expander("📋 技术详情 (RAG诊断 / Evidence / 报告)", expanded=False):
    t1, t2, t3 = st.tabs(["📊 匹配详情", "🔍 Evidence", "📄 报告"])
    with t1:
        st.json(result.match_summary)
    with t2:
        for src in result.evidence_sources:
            st.markdown(f"- `{src}`")
    with t3:
        if result.report_path and Path(result.report_path).is_file():
            st.markdown(Path(result.report_path).read_text(encoding="utf-8"))

st.markdown("---")
st.caption(f"Trace: `{result.trace_id}` · 不做自动投递")
