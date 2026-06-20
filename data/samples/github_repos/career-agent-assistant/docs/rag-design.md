# RAG 设计

## Pipeline 分层

1. Loader：MarkdownProfileLoader，读取本地 Markdown
2. Chunker：TextChunker，800 字 + 100 overlap
3. VectorStore：MemoryVectorStore，关键词 Token 重叠打分
4. Retriever：SimpleRetriever，封装检索策略
5. Pipeline：组合上述四层

## 后续升级

- Embedding 语义检索替换关键词匹配
- Chroma / FAISS 替换内存存储
- 混合检索（向量 + 关键词）
