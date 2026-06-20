# GitHub 仓库资料读取 Agent 设计

## 1. 背景

求职 Agent 需要了解用户的项目经历。GitHub 仓库是项目经历最直接的来源。但第一阶段不直接访问远程 GitHub API（网络不可控、token 管理复杂、测试不稳定），先用本地模拟仓库验证读取→RAG 检索链路。

## 2. 第一阶段目标

实现 `LocalGitHubRepoReader`：读取本地模拟 GitHub 仓库中的 README 和 docs Markdown，转化为 `ProfileDocument`，进入 RAG pipeline 被检索。

## 3. 输入

- 本地模拟仓库目录（如 `data/samples/github_repos/`）
- 每个 repo 下的 `README.md`
- 每个 repo 下 `docs/` 中的所有 `*.md`

## 4. 输出

- `ProfileDocument` 列表
- `item_type = "github_repo"`
- metadata 包含 `repo_name`, `relative_path`, `document_role`

## 5. 与 RAG 的关系

```
LocalGitHubRepoReader
  → ProfileDocument
  → TextChunker → DocumentChunk
  → MemoryVectorStore
  → RAGPipeline.retrieve()
```

## 6. 边界

- 不访问网络
- 不调用 GitHub API
- 不执行 git 命令
- 不读取源码文件（.py/.js/.ts 等）
- 不读取私有仓库
- 不做代码理解

## 7. 后续扩展

- GitHub API / MCP 远程读取
- 源码目录结构摘要
- 关键代码文件片段提取
- 与 JD 触发条件联动
