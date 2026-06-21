"""求职助手 — 真实 RAG + Agent + LLM 对话"""

import sys, tempfile, os
from pathlib import Path
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "src"))

import streamlit as st

st.set_page_config(page_title="求职助手", page_icon="🤖", layout="centered")

# ---- 初始化 session ----
if "messages" not in st.session_state:
    st.session_state.messages = []
if "kb_chunks" not in st.session_state:
    st.session_state.kb_chunks = 0
if "github_repos" not in st.session_state:
    st.session_state.github_repos = []

# ---- 侧边栏 ----
with st.sidebar:
    st.header("📁 知识库")
    st.metric("已索引资料", st.session_state.kb_chunks)

    # 文件上传 — 真实解析入库
    uploaded = st.file_uploader("上传简历/项目 (PDF/DOCX/MD)", type=["pdf","docx","md","txt"], accept_multiple_files=True)
    if uploaded and st.button("导入文件到知识库"):
        from career_agent.rag.loaders.file_loader import FileLoader
        from career_agent.rag.chunking.text_chunker import TextChunker
        from career_agent.rag.vectorstores.memory_store import MemoryVectorStore
        from career_agent.rag.embeddings.embedding_store import EmbeddingVectorStore
        from career_agent.rag.embeddings.qwen_embedding import QwenEmbeddingProvider

        loader = FileLoader()
        chunker = TextChunker()
        all_chunks = []
        for f in uploaded:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(f.name).suffix) as tmp:
                tmp.write(f.read())
                tmp_path = tmp.name
            try:
                doc = loader.load(tmp_path)
                chunks = chunker.chunk_document(doc)
                all_chunks.extend(chunks)
                os.unlink(tmp_path)
                st.success(f"✅ {f.name} → {len(chunks)} chunks")
            except Exception as e:
                st.error(f"❌ {f.name}: {e}")

        if all_chunks:
            kw_store = MemoryVectorStore()
            kw_store.add_chunks(all_chunks)
            st.session_state["kw_store"] = kw_store
            try:
                emb = QwenEmbeddingProvider()
                emb_store = EmbeddingVectorStore(emb)
                emb_store.add_chunks(all_chunks)
                st.session_state["emb_store"] = emb_store
            except Exception:
                pass
            st.session_state.kb_chunks += len(all_chunks)
            st.success(f"✅ 知识库总计: {st.session_state.kb_chunks} chunks")
            st.rerun()

    st.divider()
    st.header("🔗 GitHub")
    repo = st.text_input("仓库名", placeholder="yfn-1116/career-agent-assistant")
    if st.button("读取并导入"):
        if repo.strip():
            result = _fetch_github(repo.strip())
            if result:
                st.success(f"✅ {repo} ({len(result)} 字) → 已索引")
            else:
                st.error(f"❌ 无法读取 {repo}")

    if st.session_state.github_repos:
        st.caption("已读仓库:")
        for r in st.session_state.github_repos:
            st.caption(f"  • {r}")

# ---- 主界面 ----
st.title("🤖 求职助手")
st.caption("粘贴 JD 或问问题，基于你的真实资料回答")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---- 输入 ----
col1, col2 = st.columns([5, 1])
with col1:
    prompt = st.text_area("输入", placeholder="粘贴 JD 或输入问题...", label_visibility="collapsed", height=80, key="chat_input")
with col2:
    st.write(""); st.write("")
    send = st.button("发送", use_container_width=True, type="primary")

if send and prompt.strip():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("检索你的资料 + 大模型分析..."):
            # 1. RAG 检索
            rag_context = ""
            try:
                from career_agent.service.agent_run import AgentRunRequest, AgentRunService
                svc = AgentRunService(profile_dir="data/samples/profile")
                result = svc.run(AgentRunRequest(user_message=prompt, raw_jd=prompt, mode="analyze_job"))
                rag_context = result.final_answer
                if result.match_score > 0:
                    rag_context += f"\n\n匹配度: {result.match_score:.0%}"
            except Exception as e:
                rag_context = f"(RAG 检索出错: {e})"

            # 2. LLM 回答
            try:
                from career_agent.infrastructure.llm.qwen_provider import QwenProvider
                llm = QwenProvider()
                if llm.is_available:
                    ctx = rag_context[:3000]
                    if st.session_state.kb_chunks > 0:
                        ctx += f"\n知识库: {st.session_state.kb_chunks} 条资料已索引"
                    system = "你是专业的实习求职助手。简洁直接，像朋友聊天。基于用户真实资料回答，不编造经历。"
                    answer = llm.generate(f"参考分析:\n{ctx}\n\n用户: {prompt}", system_prompt=system)
                else:
                    answer = rag_context or "LLM 不可用，请设置 QWEN_API_KEY"
            except Exception:
                answer = rag_context or "处理出错"

            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})


def _fetch_github(repo_name):
    """真实读取 GitHub 仓库 README 并导入知识库"""
    import urllib.request, hashlib
    try:
        url = f"https://raw.githubusercontent.com/{repo_name}/main/README.md"
        req = urllib.request.Request(url, headers={"User-Agent": "smart-apply-agent"})
        with urllib.request.urlopen(req, timeout=10) as r:
            content = r.read().decode("utf-8", errors="replace")

        # 导入 RAG
        from career_agent.rag.schemas import ProfileDocument
        from career_agent.rag.chunking.text_chunker import TextChunker
        from career_agent.rag.vectorstores.memory_store import MemoryVectorStore
        doc_id = hashlib.sha256(repo_name.encode()).hexdigest()[:16]
        doc = ProfileDocument(document_id=doc_id, source_path=f"github://{repo_name}", title=repo_name, content=content, item_type="github_repo")
        chunks = TextChunker().chunk_document(doc)
        if "kw_store" not in st.session_state:
            st.session_state["kw_store"] = MemoryVectorStore()
        st.session_state["kw_store"].add_chunks(chunks)
        st.session_state.kb_chunks += len(chunks)
        if repo_name not in st.session_state.github_repos:
            st.session_state.github_repos.append(repo_name)
        return content
    except Exception as e:
        st.error(f"读取失败: {e}")
        return None
