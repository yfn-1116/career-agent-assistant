"""Smart Apply Agent — Codex-like conversational Streamlit UI.

Usage::

    streamlit run demo/streamlit/app.py
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC = str(_REPO_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import streamlit as st
from career_agent.service.agent_run import AgentRunRequest, AgentRunService

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PROFILE_DIR = str(_REPO_ROOT / "data" / "samples" / "profile")

st.set_page_config(page_title="Smart Apply Agent", page_icon="🤖", layout="wide")

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🤖 Smart Apply Agent")
st.caption("粘贴岗位 JD，Agent 自动解析、检索你的经历、给出匹配分析和简历建议")

# ---------------------------------------------------------------------------
# Input area
# ---------------------------------------------------------------------------
col_input, col_btn = st.columns([5, 1])
with col_input:
    user_input = st.text_area(
        "岗位 JD 或问题",
        placeholder="在此粘贴岗位 JD，或输入问题，例如：\n\n"
        "「这是 AI Agent 开发实习岗位，我匹配吗？」\n"
        "「帮我把这个岗位对应的项目经历改写一下」\n"
        "「帮我写一段联系 HR 的话」",
        height=180,
        label_visibility="collapsed",
    )
with col_btn:
    st.write("")
    st.write("")
    analyze = st.button("🚀 Ask Agent", type="primary", use_container_width=True)
    mode = st.selectbox("模式", ["analyze", "resume", "chat"], label_visibility="collapsed")

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if not analyze:
    st.info("👆 粘贴 JD 或输入问题，点击 Ask Agent 开始")
    st.stop()

if not user_input.strip():
    st.error("请输入 JD 文本或问题")
    st.stop()

with st.spinner("Agent 正在分析..."):
    svc = AgentRunService(profile_dir=PROFILE_DIR)
    request = AgentRunRequest(user_message=user_input, raw_jd=user_input, mode=mode)
    result = svc.run(request)

# ---------------------------------------------------------------------------
# Answer
# ---------------------------------------------------------------------------
if result.status == "failed":
    st.error("运行失败")
    st.stop()

# --- Grade badge ---
grade_color = {"excellent": "green", "good": "green", "weak": "orange", "failed": "red", "unknown": "grey"}
g = result.retrieval_grade
st.markdown(
    f"### 检索质量：:{grade_color.get(g, 'grey')}[{g.upper()}] "
    f"(score={result.retrieval_total_score:.2f}) · "
    f"Retry {result.retry_count} 次 · "
    f"Trace `{result.trace_id[:8]}`"
)

# --- Final answer ---
st.markdown(result.final_answer)

# --- Communication script ---
if result.communication_script:
    with st.expander("💬 HR 沟通话术"):
        st.info(result.communication_script)

# --- Warnings ---
if result.warnings:
    for w in result.warnings:
        st.warning(w)

# ---------------------------------------------------------------------------
# Expandable details (collapsed by default)
# ---------------------------------------------------------------------------
with st.expander("📋 技术详情（RAG 诊断 / Trace / 报告）", expanded=False):
    tab1, tab2, tab3 = st.tabs(["📊 匹配详情", "🔍 Evidence 来源", "📄 报告"])

    with tab1:
        st.json(result.match_summary)
        st.metric("检索轮次", result.retry_count)
        st.metric("最终决策", result.decision)

    with tab2:
        if result.evidence_sources:
            for src in result.evidence_sources:
                st.markdown(f"- `{src}`")
        else:
            st.caption("无 evidence 来源")

    with tab3:
        if result.report_path:
            st.caption(f"报告路径：`{result.report_path}`")
            p = Path(result.report_path)
            if p.is_file():
                with open(p) as f:
                    st.markdown(f.read())
        else:
            st.caption("无报告")

# --- Footer ---
st.markdown("---")
st.caption(f"Trace: `{result.trace_id}` · 规则型原型 · 不做自动投递")
