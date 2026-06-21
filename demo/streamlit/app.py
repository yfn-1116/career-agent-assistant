"""Smart Apply — 简洁对话式求职助手"""

import sys
from pathlib import Path
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "src"))

import streamlit as st

# ---- 页面 ----
st.set_page_config(page_title="求职助手", page_icon="🤖", layout="centered")
st.title("🤖 求职助手")

# ---- 侧边栏：知识库 ----
with st.sidebar:
    st.header("📁 知识库")
    uploaded = st.file_uploader("上传简历/项目 (PDF/DOCX/MD)", type=["pdf","docx","md","txt"], accept_multiple_files=True)
    if uploaded:
        for f in uploaded:
            st.success(f"✅ {f.name}")

    st.divider()
    repo = st.text_input("GitHub 仓库", placeholder="yfn-1116/career-agent-assistant")
    if st.button("读取仓库"):
        if repo:
            try:
                import urllib.request
                url = f"https://raw.githubusercontent.com/{repo}/main/README.md"
                req = urllib.request.Request(url, headers={"User-Agent": "smart-apply"})
                with urllib.request.urlopen(req, timeout=10) as r:
                    content = r.read().decode("utf-8", errors="replace")
                st.session_state["github_content"] = content
                st.success(f"✅ {repo} ({len(content)} 字)")
            except Exception as e:
                st.error(str(e))

    st.divider()
    st.caption("你的 3 个仓库已入库 ✅")

# ---- 初始化对话 ----
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---- 显示对话 ----
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---- 输入框 ----
if prompt := st.chat_input("粘贴 JD 或输入问题..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            # 构建完整上下文
            context = prompt
            if "github_content" in st.session_state:
                context = f"用户 GitHub 仓库内容：\n{st.session_state.github_content[:3000]}\n\n用户问题：{prompt}"

            # 先用 RAG pipeline 检索相关资料
            try:
                from career_agent.service.agent_run import AgentRunRequest, AgentRunService
                svc = AgentRunService(profile_dir="data/samples/profile")
                result = svc.run(AgentRunRequest(user_message=prompt, raw_jd=prompt, mode="analyze_job"))
                rag_context = result.final_answer
            except Exception:
                rag_context = ""

            # 调用大模型
            try:
                from career_agent.infrastructure.llm.qwen_provider import QwenProvider
                llm = QwenProvider()
                if llm.is_available:
                    system = """你是专业的实习求职助手。回答风格：
- 简洁、直接、可执行
- 像朋友聊天，不像写论文
- 基于用户真实经历，不编造
- 如果信息不足，诚实说"""
                    full_prompt = f"参考资料：\n{rag_context[:2000]}\n\n用户问题：{prompt}"
                    answer = llm.generate(full_prompt, system_prompt=system)
                else:
                    answer = rag_context or "抱歉，LLM 不可用。"
            except Exception:
                answer = rag_context or "抱歉，处理出错。"

            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
