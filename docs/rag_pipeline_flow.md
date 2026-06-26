# RAG 检索 Pipeline 完整实现

## 一、数据摄入链路

```
用户上传 PDF/DOCX/MD
    │
    ▼
┌──────────────────────────────────────────────────────────────────┐
│ ① FileLoader.load()                    rag/loaders/file_loader.py │
│    .pdf  → pypdf.PdfReader → page.extract_text()                 │
│    .docx → python-docx → para.text                               │
│    .md   → path.read_text()                                      │
│    输出：ProfileDocument { content = 全文纯文本 }                   │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│ ② TextChunker.chunk_document()       rag/chunking/text_chunker.py │
│    clean_text()  → 去空白/统一换行/压缩空行                       │
│    _split_text() → 固定滑动窗口 chunk_size=800, overlap=100       │
│                    step = 800 - 100 = 700                         │
│    _build_chunks() → 包装为 DocumentChunk {chunk_id, content...} │
│    输出：list[DocumentChunk]（每个 800 字符，重叠 100 字符）        │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│ ③ _append_chunks()              service/knowledge_base.py:274    │
│    → runtime/knowledge_base/chunks.jsonl                         │
│    {"chunk_id":"xxx_0","content":"...","source_path":"xxx.pdf"}  │
│    每行一个 chunk JSON，追加写入                                   │
└──────────────────────────────────────────────────────────────────┘
```

## 二、检索 Pipeline（完整 ML 模式）

```
用户提问："Agent 开发实习生 要求 Python RAG LangGraph"
    │
    │  jieba.cut("Agent 开发实习生 要求 Python RAG LangGraph")
    │  → ["Agent", "开发", "实习生", "要求", "Python", "RAG", "LangGraph"]
    │
    ├─────────────────────────────────────────────────────────────┐
    │                                                             │
    ▼                                                             ▼
┌──────────────────────┐                        ┌──────────────────────────┐
│  BM25 关键词检索       │                        │  Qwen Embedding 语义检索   │
│  (rag/retrievers/     │                        │  (rag/embeddings/         │
│   bm25_retriever.py)  │                        │   qwen_embedding.py)      │
│                       │                        │                           │
│  rank_bm25 库          │                        │  DashScope API             │
│  BM25Okapi 算法        │                        │  text-embedding-v3        │
│                       │                        │  1024 维稠密向量           │
│  score = Σ IDF(qi)    │                        │                           │
│    × TF(qi,doc)       │                        │  cosine_similarity(        │
│    × (k1+1)           │                        │    query_vec,              │
│    / (TF + k1×(1-b    │                        │    chunk_vecs)             │
│    + b×doc_len/avg))  │                        │                           │
│                       │                        │  优势：语义理解              │
│  优势：精确关键词匹配    │                        │  "写代码" ≈ "编程" ≈ "开发"│
│  不会漏掉"LangGraph"   │                        │                           │
│                       │                        │                           │
│  输出：top 80 chunks   │                        │  输出：top 80 chunks        │
│  (按 BM25 得分排序)    │                        │  (按 cosine 相似度排序)     │
└──────────┬───────────┘                        └────────────┬─────────────┘
           │                                                 │
           └──────────────┬──────────────────────────────────┘
                          │
                          ▼
          ┌───────────────────────────────┐
          │  RRF 融合排序                   │
          │  (rag/retrievers/rrf_fusion.py)│
          │                               │
          │  RRF_score(chunk) =            │
          │    Σ 1/(k + rank_i(chunk))     │
          │                               │
          │  其中 k = 60                   │
          │  rank_i 是 chunk 在第 i 个      │
          │  排序列表中的排名 (1-based)      │
          │                               │
          │  零参数，不需要调权重             │
          │  输出：top 30 chunks            │
          └───────────────┬───────────────┘
                          │
                          ▼
          ┌───────────────────────────────┐
          │  Cross-Encoder Reranker 精排    │
          │  (rag/reranker/               │
          │   cross_encoder_reranker.py)   │
          │                               │
          │  bge-reranker-base             │
          │  279M 参数, 12层 Transformer    │
          │                               │
          │  把 query 和 chunk 拼成一对：      │
          │  [CLS] query [SEP] chunk [SEP] │
          │  整对送进 Transformer 打分      │
          │                               │
          │  Cross-Attention 让 query 的     │
          │  每个 token 都能看到 chunk 的     │
          │  每个 token → 精确判断相关性     │
          │                               │
          │  输出：top 5 chunks             │
          │  (按 Cross-Encoder 得分排序)     │
          └───────────────┬───────────────┘
                          │
                          ▼
          ┌───────────────────────────────┐
          │  FaithfulnessChecker            │
          │  (evaluation/faithfulness.py)  │
          │                               │
          │  验证每个声称有证据支撑            │
          │  • 检测夸大措辞                  │
          │    ("完整实现"/"大规模部署")     │
          │  • 检测无证据声称                 │
          │  • 通过阈值：0.75               │
          │                               │
          │  EvidenceGate                  │
          │  (evidence/gate.py)            │
          │  • implemented → 可直接写入简历  │
          │  • designed    → 需降级措辞     │
          │  • planned     → 拒绝生成      │
          └───────────────┬───────────────┘
                          │
                          ▼
          ┌───────────────────────────────┐
          │  LLM 生成                      │
          │                               │
          │  Qwen-Plus (主)                │
          │  DeepSeek-Chat (备用)          │
          │                               │
          │  基于 top 5 evidence            │
          │  + SYSTEM_PROMPT (证据约束)     │
          │  → 生成简历 bullet + 沟通话术    │
          │                               │
          │  BuildAgent 四阶段分级：         │
          │  • can_write_claims             │
          │  • needs_confirmation_claims    │
          │  • learning_plan_claims         │
          └───────────────────────────────┘
```

## 三、轻量模式（无 API / 无 GPU 降级）

```
用户提问
    │
    ▼
jieba 分词 → BM25 关键词检索 (top N)
    │
    ▼
LightweightReranker 规则打分
  • 技能重叠 (0.35) + 来源质量 (0.25) + 特异性 (0.20)
  • 长度惩罚 (0.10) + 去重惩罚 (0.10)
    │
    ▼
FaithfulnessChecker + EvidenceGate
    │
    ▼
模板生成 / LLM 生成 (如果有 API Key)
```

## 四、降级策略

```
启动时检查：

QWEN_API_KEY 存在？
  ├── YES → BM25 + Qwen Embedding + RRF + CrossEncoder (完整模式)
  │         准确率最高，延迟 ~800ms
  │
  └── NO  → BM25 + LightweightReranker (轻量模式)
           准确率降低，但延迟 <50ms，零网络依赖
```

## 五、技术选型汇总

| 环节 | 技术 | 部署方式 | 作用 |
|---|---|---|---|
| 分词 | jieba 0.42 | 本地 pip | 中文分词，BM25 前置 |
| BM25 | rank_bm25 0.2 | 本地 pip | 关键词粗召回 (top 80) |
| Embedding | Qwen text-embedding-v3 | 阿里云 API | 语义粗召回 (top 80) |
| 融合 | RRF (k=60) | 本地公式 | 零参数融合两路排序 |
| 精排 | bge-reranker-base | 本地 (~1.1GB) | Cross-Encoder 逐对打分 |
| LLM | Qwen-Plus / DeepSeek | 阿里云 / DeepSeek API | 生成分析 + 话术 |
| 真实性 | FaithfulnessChecker | 本地规则 | 不编造保证 |
| 证据约束 | EvidenceGate | 本地规则 | 四阶段分级 |
