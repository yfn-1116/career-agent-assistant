# RAG 完整流程：写入 + 检索

## 一、总览

```
┌──────────────────────┐         ┌──────────────────────┐
│    写入路径 (Write)    │         │    检索路径 (Read)     │
│   Perception → Memory │         │   Memory → Action    │
├──────────────────────┤         ├──────────────────────┤
│                      │         │                      │
│ PDF/DOCX/MD          │         │ 用户提问              │
│   ↓                  │         │   ↓                  │
│ 提取文字             │         │ jieba 分词           │
│   ↓                  │         │   ↓                  │
│ 分块 (800字/块)       │   ┌────→│ BM25 关键词 (top80)   │
│   ↓                  │   │     │   ↓                  │
│ 写入 JSONL ──────────┼───┘     │ Qwen Embedding(top80)│
│                      │         │   ↓                  │
│                      │         │ RRF 融合 (top30)     │
│                      │         │   ↓                  │
│                      │         │ CrossEncoder (top5)  │
│                      │         │   ↓                  │
│                      │         │ Evidence Gate        │
│                      │         │   ↓                  │
│                      │         │ LLM 生成             │
└──────────────────────┘         └──────────────────────┘
         写入后存入                    检索时读出
    chunks.jsonl     ←─────────────→  chunks.jsonl
```

---

## 二、写入路径（Write Path）

### 2.1 PDF 文件

```
用户上传 "陈小明简历.pdf"
    │
    ▼
FileLoader.load("陈小明简历.pdf")
  rag/loaders/file_loader.py:22
    │
    ├── path.suffix → ".pdf"
    │
    ├── _read_pdf(path)
    │     rag/loaders/file_loader.py:68
    │     │
    │     ├── pypdf.PdfReader(path)
    │     ├── for page in reader.pages:
    │     │      text = page.extract_text()
    │     │      提取该页所有文字和数字
    │     └── "\n\n".join(所有页文字)
    │
    └── 返回 ProfileDocument
        {
          document_id: "d4d8c6234dab0f7a",
          source_path: "陈小明简历.pdf",
          content: "陈小明\nXX大学 化学系 本科\nPython 熟练\n...
                    FastAPI 独立开发 3 个后端项目\n...",
        }
    │
    ▼
KnowledgeBaseService.index_text(content, "陈小明简历.pdf")
  service/knowledge_base.py:64
    │
    ├── 包装为 ProfileDocument
    │
    ├── TextChunker.chunk_document(doc)
    │     rag/chunking/text_chunker.py:36
    │     │
    │     ├── clean_text(content)
    │     │     去空白 → 统一换行 → 压缩空行
    │     │
    │     ├── _split_text(cleaned)
    │     │     chunk_size=800, step=700, overlap=100
    │     │     while start < len(text):
    │     │         chunk = text[start : start+800]
    │     │         start += 700
    │     │
    │     └── _build_chunks(doc, segments)
    │           每个 segment → DocumentChunk
    │           chunk_id = "d4d8c6234dab0f7a_0", "_1", "_2"
    │
    └── DocumentChunk 列表，例如 3 个 chunk：
        [
          {chunk_id: "d4d8c_0", content: "陈小明\nXX大学\n...(前800字)"},
          {chunk_id: "d4d8c_1", content: "Python 熟练\nFastAPI\n...(中段800字)"},
          {chunk_id: "d4d8c_2", content: "求职意向\nAI应用开发\n...(后段800字)"},
        ]
    │
    ▼
_append_chunks(chunks)
  service/knowledge_base.py:274
    │
    └── 写入 runtime/knowledge_base/chunks.jsonl
        每行一个 chunk 的 JSON：
        
        {"chunk_id":"d4d8c_0","content":"陈小明\nXX大学...","source_path":"陈小明简历.pdf","chunk_index":0}
        {"chunk_id":"d4d8c_1","content":"Python 熟练\nFastAPI...","source_path":"陈小明简历.pdf","chunk_index":1}
        {"chunk_id":"d4d8c_2","content":"求职意向\nAI应用...","source_path":"陈小明简历.pdf","chunk_index":2}
```

### 2.2 GitHub 仓库

```
用户粘贴 "https://github.com/yfn-1116/career-agent-assistant"
    │
    ▼
LLM 调 MCPGitHubTool
  tools/mcp_github_tool.py:51  run(action="read_repo", repo="yfn-1116/career-agent-assistant")
    │
    ├── 尝试 MCP（优先）
    │     infrastructure/mcp_client.py:61  start()
    │       │
    │       ├── subprocess.Popen("npx", ["-y", "@modelcontextprotocol/server-github"])
    │       │     启动 GitHub MCP 服务器子进程
    │       │
    │       ├── JSON-RPC: tools/call → get_file_contents(owner, repo, "README.md")
    │       │     通过 MCP 协议获取 README 内容
    │       │
    │       └── 返回 README 的 Markdown 原文
    │
    └── 或降级（MCP 不可用时）
          mcp_github_tool.py:110  _raw_fallback()
            │
            └── urllib: GET https://raw.githubusercontent.com/{repo}/main/README.md
                  直接 HTTP 请求原始文件
    │
    ▼
README 内容（Markdown）：
  "# Career Agent Assistant\n\n基于证据约束的智能求职 Agent...\n\n## 技术栈\n- Python\n- LangGraph\n..."
    │
    ▼
和 PDF 一样走分块流程：
  index_text(content, "github:yfn-1116/career-agent-assistant")
    → TextChunker → 分块 → _append_chunks → chunks.jsonl
```

---

## 三、检索路径（Read Path）

```
用户提问："Agent 开发实习生 要求 Python RAG LangGraph"
    │
    ▼
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
① jieba 分词
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    jieba.cut("Agent 开发实习生 要求 Python RAG LangGraph")
    → ["Agent", "开发", "实习生", "要求", "Python", "RAG", "LangGraph"]
    │
    ▼
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
② 双路粗召回 (并行)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    左路：BM25 关键词检索                  右路：Qwen Embedding 语义检索
    ┌───────────────────────┐          ┌──────────────────────────┐
    │ BM25Retriever          │          │ QwenEmbeddingProvider    │
    │ bm25_retriever.py:42   │          │ qwen_embedding.py:38     │
    │                        │          │                          │
    │ 从 JSONL 读回所有       │          │ query → API 调           │
    │ DocumentChunk           │          │ text-embedding-v3       │
    │                        │          │ → 1024维向量            │
    │ jieba 分词每个 chunk    │          │                          │
    │ → rank_bm25.get_scores │          │ 所有 chunk 预 encode     │
    │                        │          │ → cosine_similarity      │
    │ BM25 公式：             │          │                          │
    │ score = Σ IDF(qi)      │          │ 优势：                   │
    │  × TF(qi,doc)          │          │ "写代码" ≈ "编程"        │
    │  × (k1+1) / (...)      │          │                          │
    │                        │          │                          │
    │ 优势：                  │          │                          │
    │ 不会漏掉"LangGraph"    │          │                          │
    │                        │          │                          │
    │ 输出：top 80 chunks     │          │ 输出：top 80 chunks       │
    │ (按 BM25 得分排序)      │          │ (按 cosine 相似度排序)    │
    └───────────┬───────────┘          └────────────┬─────────────┘
                │                                   │
                └──────────────┬────────────────────┘
                               ▼
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
③ RRF 融合 (零参数)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    rrf_fusion.py:15  reciprocal_rank_fusion(list_bm25, list_emb, k=60)
    
    对每个 chunk：
      RRF_score = 1/(60 + rank_in_bm25) + 1/(60 + rank_in_embedding)
    
    不需要归一化两种不同的分数（BM25可能是0~20，cosine是0~1）
    只靠排名来决定，排名越靠前权重越大
    
    输出：top 30 chunks
    │
    ▼
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
④ CrossEncoder 精排
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    cross_encoder_reranker.py:63  rerank(query, top30_chunks, top_n=5)
    
    bge-reranker-base (279M参数, 12层 Transformer)
    
    对每个候选 chunk：
      把 query 和 chunk 拼成一对：
      [CLS] "Agent 开发实习生" [SEP] "陈小明\nPython 熟练\nFastAPI..."
      → 送进 Transformer → 输出一个 relevance score
    
    Cross-Attention: query 的每个 token 能看到 chunk 的每个 token
    比 Embedding 的点乘精确 10-15%
    
    输出：top 5 chunks (按 CrossEncoder 得分降序)
    │
    ▼
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⑤ Evidence Gate + Faithfulness (安全网)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    evidence/gate.py:46  EvidenceGate.validate()
      检查每个 chunk 的 status:
        implemented → ✅ 可以声称"实现了"
        designed    → ⚠️ 必须降级为"设计了"
        planned     → ❌ 不能声称任何东西
        uncertain   → ❌ 拒绝使用
    
    evaluation/faithfulness.py:153  FaithfulnessChecker.check()
      验证生成的 bullet 是否全部有证据支撑
      通过阈值: 0.75
    │
    ▼
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⑥ LLM 生成
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Qwen-Plus / DeepSeek
    
    System Prompt + top 5 evidence + 用户问题
      → 生成：
        • 匹配度：74%
        • 简历 bullet × 5 条（每条标注状态）
        • BOSS 沟通话术
    │
    ▼
    最终输出 → 用户看到
```

---

## 四、一次检索实际数据流 (toy example)

```
知识库：chunks.jsonl 有 3 个 chunk
  c1: "陈小明 Python 熟练 FastAPI 后端开发 数据库"
  c2: "计算机视觉 PyTorch OpenCV CNN 图像处理"
  c3: "AI Agent RAG LangGraph Python 项目"

用户问："Agent Python 开发"
    │
    ▼
jieba 分词 → ["Agent", "Python", "开发"]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
左路 BM25：
  c1 得分: 很高  ("Python" + "开发" 命中)
  c3 得分: 高    ("Agent" + "Python" 命中)
  c2 得分: 0     (没有命中任何词)
  → BM25 排序: [c1, c3, c2]

右路 Embedding：
  c3 得分: 0.92  ("Agent RAG" 语义接近 "Agent 开发")
  c1 得分: 0.78  ("后端开发" 和 "Agent 开发" 部分相似)
  c2 得分: 0.15  ("CV" 完全不相关)
  → Embedding 排序: [c3, c1, c2]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RRF 融合 (k=60)：
  c3: 1/(60+2) + 1/(60+1) = 0.0161 + 0.0164 = 0.0325
  c1: 1/(60+1) + 1/(60+2) = 0.0164 + 0.0161 = 0.0325
  c2: 1/(60+3) + 1/(60+3) = 0.0159 + 0.0159 = 0.0317
  → RRF 排序: [c3, c1, c2]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CrossEncoder 精排 (query + 每个chunk → 打分)：
  c3: 4.82  (高度相关)
  c1: 3.15  (中等相关)
  c2: -2.30 (不相关)
  → 最终 top 2: [c3, c1]

c3（AI Agent RAG LangGraph Python 项目）和
c1（Python 熟练 FastAPI 后端开发）作为证据，
输入 LLM 生成回答。
```
