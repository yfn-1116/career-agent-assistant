"""Streamlit demo for the career-agent-assistant job-match workflow.

Usage::

    pip install streamlit
    PYTHONPATH=src streamlit run demo/streamlit/app.py
"""

import sys
from pathlib import Path

# Ensure src/ is on the import path before importing internal modules.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC = str(_REPO_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import streamlit as st

from career_agent.workflows.job_match_workflow import JobMatchWorkflow

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROFILE_DIR = str(_REPO_ROOT / "data" / "samples" / "profile")
JOBS_DIR = _REPO_ROOT / "data" / "samples" / "jobs"

JD_FILES = {
    "AI Agent 开发实习生": "agent_intern_jd.md",
    "RAG 工程师实习生": "rag_engineer_intern_jd.md",
    "AI 应用开发实习生": "ai_application_intern_jd.md",
    "后端开发实习生（AI 方向）": "backend_ai_intern_jd.md",
}

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="智能投递辅助 Agent Demo",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 智能投递辅助 Agent Demo")
st.caption(
    "基于 RAG + 多 Agent 的实习求职匹配原型 | "
    "当前使用本地规则和内存检索，不调用外部大模型"
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

st.sidebar.header("⚙️ 参数设置")

top_k = st.sidebar.slider("检索证据数量 (top_k)", min_value=1, max_value=10, value=5)

jd_source = st.sidebar.radio("JD 来源", ["选择示例 JD", "手动粘贴 JD 文本"])

jd_text = ""

if jd_source == "选择示例 JD":
    selected_label = st.sidebar.selectbox("示例 JD", list(JD_FILES.keys()))
    jd_path = JOBS_DIR / JD_FILES[selected_label]
    if jd_path.is_file():
        jd_text = jd_path.read_text(encoding="utf-8")
        st.sidebar.caption(f"已加载：`{JD_FILES[selected_label]}`")
    else:
        st.sidebar.error(f"JD 文件未找到：{jd_path}")
else:
    jd_text = st.sidebar.text_area(
        "粘贴 JD 文本",
        height=250,
        placeholder="在此粘贴岗位 JD 的完整文本...",
    )

# ---------------------------------------------------------------------------
# Run workflow
# ---------------------------------------------------------------------------

run_clicked = st.sidebar.button("🚀 运行匹配分析", type="primary", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.caption(
    "⚠️ 当前版本使用本地规则和内存检索。"
    "不调用外部大模型，不进行自动投递，不爬取岗位网站。"
)

# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------

if not run_clicked:
    st.info("👈 在左侧选择 JD 来源，然后点击「运行匹配分析」开始。")
    st.markdown("### 支持的功能")
    st.markdown("- 选择 4 个示例 JD 或手动粘贴自定义 JD")
    st.markdown("- 基于 RAG 检索用户资料知识库中的相关经历")
    st.markdown("- 输出匹配分析、简历 bullet、沟通话术")
    st.markdown("- 所有输出基于真实用户资料，不编造经历")
    st.stop()

if not jd_text.strip():
    st.error("JD 文本为空，请选择示例 JD 或粘贴文本。")
    st.stop()

# --- Execute ----------------------------------------------------------------

with st.spinner("正在初始化知识库并运行匹配分析..."):
    wf = JobMatchWorkflow(profile_dir=PROFILE_DIR)
    state = wf.run(jd_text, top_k=top_k)

if state.status == "failed":
    st.error(f"运行失败：{state.error_message}")
    st.stop()

# --- Results ----------------------------------------------------------------

st.success(f"✅ 分析完成 | 岗位方向：{state.parsed_jd.job_direction if state.parsed_jd else 'N/A'} | 检索证据：{len(state.retrieved_evidence)} 条")

# -- JD Parse --
st.markdown("## 📋 JD 解析结果")
if state.parsed_jd:
    pj = state.parsed_jd
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**岗位标题**：{pj.job_title or '（未识别）'}")
        st.markdown(f"**岗位方向**：{pj.job_direction}")
        st.markdown(f"**硬技能**：{', '.join(pj.hard_skills) if pj.hard_skills else '（无）'}")
    with col2:
        st.markdown(f"**加分技能**：{', '.join(pj.bonus_skills) if pj.bonus_skills else '（无）'}")
        st.markdown(f"**软技能**：{', '.join(pj.soft_skills) if pj.soft_skills else '（无）'}")
        st.markdown(f"**关键词**：{', '.join(pj.keywords[:10]) if pj.keywords else '（无）'}...")

# -- Evidence --
st.markdown("## 🔍 RAG 检索证据")
st.caption(f"共检索到 {len(state.retrieved_evidence)} 条证据")
for i, ev in enumerate(state.retrieved_evidence, 1):
    with st.expander(f"证据 {i}：{ev.title or ev.evidence_id} (score: {ev.score:.2f})"):
        st.markdown(f"**来源**：`{ev.source_path}`")
        st.markdown(f"**匹配关键词**：{', '.join(ev.matched_keywords)}")
        st.text(ev.content[:300])

# -- Analysis --
if state.match_analysis:
    ma = state.match_analysis
    st.markdown("## 📊 匹配分析")

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("### ✅ Strengths")
        for s in ma.strengths:
            st.markdown(f"- {s}")
        st.markdown("### 📌 Recommended Projects")
        for r in ma.recommended_projects:
            st.markdown(f"- {r}")

    with col4:
        st.markdown("### ⚠️ Weaknesses")
        for w in ma.weaknesses:
            st.markdown(f"- {w}")
        st.markdown("### 💡 Suggestions")
        for s in ma.suggestions:
            st.markdown(f"- {s}")

    st.markdown(f"**Matched Keywords**：{', '.join(ma.matched_keywords)}")

# -- Output --
if state.generated_output:
    go = state.generated_output
    st.markdown("## ✍️ 生成输出")

    st.markdown("### 📝 简历 Bullet")
    for b in go.resume_bullets:
        st.markdown(b)

    st.markdown("### 💬 沟通话术")
    st.info(go.communication_message)

    st.markdown("### 📄 总结")
    st.markdown(go.summary)

    st.markdown("### 🔗 Evidence Refs")
    st.caption(", ".join(go.evidence_refs) if go.evidence_refs else "（无）")

# -- Footer --
st.markdown("---")
st.caption(
    "⚠️ 当前版本使用本地规则和内存关键词检索，不调用外部大模型，不进行自动投递，不爬取岗位网站。"
    "后续可接入 DeepSeek / OpenAI API 升级为 LLM 驱动版本。"
)
