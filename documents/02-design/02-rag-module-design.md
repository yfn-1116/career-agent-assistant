# RAG 模块设计

## 用途

本文档定义第一阶段用户资料知识库的范围、核心 schema、模块边界和后续扩展方向。

## 第一阶段资料范围

只处理以下本地 Markdown 内容：

- 用户简历摘要。
- 项目经历 Markdown。
- GitHub 仓库摘要 Markdown。
- 技能与实习经历 Markdown。
- 示例岗位 JD Markdown。

第一阶段不做自动爬取 BOSS / 实习僧、不做复杂 OCR、不做大规模网页抓取、不做完整 GitHub 源码分析、不做多用户知识库。

## 核心 schema 方向

### ProfileItem

表示一条可检索的用户能力材料。字段方向包括：

- `item_id`：资料项唯一标识。
- `item_type`：项目、实习、技能、课程、证书、GitHub 仓库摘要等类型。
- `title`：资料标题。
- `summary`：资料摘要。
- `content`：正文内容。
- `tags`：技术栈、岗位方向、能力标签。
- `source_path`：本地 Markdown 来源。
- `created_at`、`updated_at`：维护时间。

### ProfileDocument

表示一个 Markdown 文件加载后的结构化文档。字段方向包括：

- `document_id`
- `source_path`
- `title`
- `items`
- `metadata`

### DocumentChunk

表示可进入检索索引的文本块。字段方向包括：

- `chunk_id`
- `document_id`
- `item_id`
- `text`
- `metadata`
- `token_count`

### RetrievedEvidence

表示检索返回的证据。字段方向包括：

- `evidence_id`
- `chunk_id`
- `source_path`
- `quote`
- `score`
- `reason`
- `metadata`

## 模块边界

- `MarkdownProfileLoader`：只负责读取和解析本地 Markdown，不做向量化和生成。
- `TextChunker`：只负责文本清洗和 chunk 切分，不理解岗位 JD。
- `VectorStore interface`：定义写入、查询、删除、持久化等接口，不绑定具体实现。
- `SimpleRetriever`：封装查询逻辑，返回 `RetrievedEvidence`。
- `RAGPipeline`：组合 loader、chunker、vector store 和 retriever，为 Agent 提供检索能力。

## 第一阶段实现策略

先抽象接口，再用内存或轻量本地方案实现最小检索链路。后续可接 Chroma / FAISS，但不应影响 Agent 层调用。

## 当前状态

本轮只定义设计方向，不实现任何 RAG 代码。

## 后续维护规则

- RAG schema 由 `RAG-001` 任务负责。
- loader、chunking、vector store、pipeline 必须分任务实现。
- 不允许局部任务同时修改 RAG 和 Agent workflow。

## ARCH-003 代码结构决策

第一阶段 RAG 模块最终放在 `src/career_agent/rag/` 下：

- `schemas.py`：定义 `ProfileItem`、`ProfileDocument`、`DocumentChunk`、`RetrievedEvidence`。
- `loaders/markdown_loader.py`：只处理本地 Markdown。
- `chunking/text_chunker.py`：文本清洗和 chunk 切分。
- `vectorstores/base.py`：`VectorStore` 接口。
- `vectorstores/memory_store.py`：第一阶段内存检索实现。
- `retrievers/simple_retriever.py`：简单检索器。
- `pipeline.py`：组合 loader、chunker、vectorstore、retriever。

第一阶段不接 Chroma / FAISS，不做 OCR，不做完整 GitHub 源码分析。
