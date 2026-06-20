# Embedding Provider 设计

## 1. EmbeddingProvider 接口

```python
class EmbeddingProvider(ABC):
    def embed_text(self, text: str) -> list[float]: ...
    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...
    @property
    def dimension(self) -> int: ...
```

## 2. HashEmbeddingProvider

基于文本字符 n-gram hash 生成固定维度伪向量。

- 输入相同文本 → 输出相同向量
- 不同文本 → 不同向量
- 文本相似（大量公共子串）→ 向量相近
- 不是真正的语义 embedding，仅用于验证 pipeline

## 3. EmbeddingVectorStore

包装 EmbeddingProvider + 向量存储，提供：

- `add_chunks(chunks)`：对 chunk content 做 embed，存入内存
- `search(query, top_k)`：对 query 做 embed，余弦相似度检索

## 4. 与 MemoryVectorStore 的关系

- MemoryVectorStore **不受影响**，保持关键词检索
- EmbeddingVectorStore 是**新增**的可选实现
- RAGPipeline **不默认切换**到 embedding 检索

## 5. 不修改默认 pipeline

当前 RAGPipeline 仍使用 MemoryVectorStore + 关键词检索。EmbeddingVectorStore 仅作为可选的扩展路径验证。
