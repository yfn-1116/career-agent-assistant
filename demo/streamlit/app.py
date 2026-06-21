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
st.caption("基于 RAG + 多 Agent 的实习求职匹配原型")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

st.sidebar.header("⚙️ 参数设置")

top_k = st.sidebar.slider("检索证据数量", min_value=1, max_value=10, value=5)

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

run_clicked = st.sidebar.button("🚀 运行匹配分析", type="primary", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.caption("规则型原型 | 不调用外部大模型 | 不做自动投递")

# ---------------------------------------------------------------------------
# Main content (before run)
# ---------------------------------------------------------------------------

if not run_clicked:
    st.info("👈 在左侧选择 JD，点击「运行匹配分析」开始。")
    st.markdown("### 能做什么")
    st.markdown("- 解析岗位 JD，识别技能要求")
    st.markdown("- 从你的资料库中检索匹配的经历")
    st.markdown("- 评估检索质量（关键词覆盖、来源多样性等）")
    st.markdown("- 输出匹配分析 + 简历 bullet + 沟通话术")
    st.stop()

if not jd_text.strip():
    st.error("JD 文本为空，请选择示例 JD 或粘贴文本。")
    st.stop()

# ---------------------------------------------------------------------------
# Execute workflow
# ---------------------------------------------------------------------------

with st.spinner("正在初始化知识库并运行匹配分析..."):
    wf = JobMatchWorkflow(profile_dir=PROFILE_DIR)
    state = wf.run(jd_text, top_k=top_k)

    # Run retrieval grading
    from career_agent.agents.rag_retrieve_agent import RAGRetrieveAgent
    from career_agent.rag.grading import grade_retrieval

    retrieval_query = ""
    if state.parsed_jd is not None:
        _rag_agent = RAGRetrieveAgent(pipeline=wf.rag_pipeline)
        retrieval_query = _rag_agent.build_query_from_parsed_jd(state.parsed_jd)
    grade_report = grade_retrieval(
        query=retrieval_query,
        parsed_jd=state.parsed_jd,
        evidence=state.retrieved_evidence,
        top_k=top_k,
    )

if state.status == "failed":
    st.error(f"运行失败：{state.error_message}")
    st.stop()

pj = state.parsed_jd
ma = state.match_analysis
go = state.generated_output

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

# --- Top status bar ---
grade_emoji = {"excellent": "🟢", "good": "🟢", "weak": "🟡", "failed": "🔴"}
g = grade_report.grade
st.success(
    f"{grade_emoji.get(g, '')} 检索评级 **{g.upper()}** | "
    f"方向：{pj.job_direction if pj else 'N/A'} | "
    f"总分 {grade_report.metadata.get('total_score', 0):.2f}"
)

# --- Tab layout for main sections ---
tab1, tab2, tab3 = st.tabs(["🔍 RAG 检索诊断", "📊 匹配分析", "✍️ 生成输出"])

# ===== TAB 1: RAG Diagnostics =====
with tab1:
    # JD summary (compact)
    if pj:
        st.markdown("**JD 解析**")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"岗位：**{pj.job_title or '未识别'}** | 方向：{pj.job_direction}")
        with c2:
            st.markdown(
                f"硬技能：{', '.join(pj.hard_skills[:8]) if pj.hard_skills else '无'}"
                f"{'...' if len(pj.hard_skills) > 8 else ''}"
            )
        st.markdown("---")

    # Grade metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("证据数", f"{grade_report.evidence_count}/{grade_report.top_k}")
    with c2:
        st.metric("平均分", f"{grade_report.average_score:.2f}")
    with c3:
        st.metric("关键词覆盖", f"{grade_report.keyword_coverage:.0%}")
    with c4:
        st.metric("来源数", grade_report.source_diversity)

    st.caption(f"检索 Query：`{retrieval_query[:120]}...`")

    # Evidence details
    st.markdown("**检索到的证据**")
    for i, summary in enumerate(grade_report.evidence_summaries, 1):
        with st.expander(
            f"{i}. {summary.get('title', 'N/A')} — score {summary.get('score', 0):.2f}"
        ):
            st.markdown(f"来源：`{summary.get('source_path', 'N/A')}`")
            st.markdown(
                f"匹配关键词：{', '.join(summary.get('matched_keywords', []))}"
            )
            st.text(summary.get('snippet', ''))

    # Grading detail (collapsed by default)
    with st.expander("评分明细（规则型诊断）"):
        for item in grade_report.items:
            icon = "✅" if item.passed else "❌"
            st.markdown(f"- {icon} **{item.name}**: {item.message}")

# ===== TAB 2: Match Analysis =====
with tab2:
    if ma:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### ✅ 匹配优势")
            for s in ma.strengths[:10]:
                st.markdown(f"- {s}")
            if ma.recommended_projects:
                st.markdown("### 📌 推荐项目")
                for r in ma.recommended_projects:
                    st.markdown(f"- {r}")
        with c2:
            st.markdown("### ⚠️ 待补充")
            for w in ma.weaknesses[:10]:
                st.markdown(f"- {w}")
            if ma.suggestions:
                st.markdown("### 💡 建议")
                for s in ma.suggestions:
                    st.markdown(f"- {s}")
    else:
        st.info("无匹配分析结果")

# ===== TAB 3: Generated Output =====
with tab3:
    if go:
        st.markdown("### 📝 简历 Bullet")
        for b in go.resume_bullets[:6]:
            st.markdown(b)

        st.markdown("### 💬 沟通话术")
        st.info(go.communication_message)

        st.markdown("---")
        st.caption(go.summary)
    else:
        st.info("无生成输出")

# --- Footer ---
st.markdown("---")
st.caption("规则型原型 · 不调用外部大模型 · 不做自动投递")
