# Embedding 检索策略决策

## 1. 当前短板

MemoryVectorStore 使用关键词 Token 重叠打分，不是语义检索。JD 写"容器化部署"而资料写"Docker"时无法匹配。

## 2. 为什么不直接接 Chroma / FAISS

- 引入第三方依赖，增加安装复杂度
- 需要 numpy，增加环境要求
- 第一阶段先验证接口设计，后续替换实现

## 3. 为什么不直接调用真实 embedding API

- 需要网络和 API Key
- 测试不稳定
- 先做本地可验证的接口预留

## 4. 为什么先做 EmbeddingProvider 抽象

- 定义统一接口：text → vector
- Mock/Hash 实现可测试、可本地运行
- 后续 DeepSeek/OpenAI embedding 只需实现同一接口

## 5. 测试策略

- MockProvider：返回固定向量
- HashEmbeddingProvider：基于文本 hash 生成伪向量，语义相似的文本向量相近（对同义词无效，仅验证 pipeline）
- 测试不依赖网络

## 6. 后续升级路径

1. DeepSeek Embedding API（urllib，无需新依赖）
2. OpenAI Embedding API
3. Chroma / FAISS 向量库（可选）
4. Reranker 重排序
