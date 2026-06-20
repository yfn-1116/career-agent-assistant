# GitHub 仓库读取策略决策

## 1. 为什么不一开始读远程 GitHub

- 测试不可控：网络不稳定、API rate limit、仓库可能被删除
- token 管理复杂：需要 GitHub token，容易泄漏
- 第一阶段优先级：先验证 README→RAG 链路，远程是锦上添花

## 2. 为什么不分析完整源码

- 代码理解是另一个复杂问题，不是第一优先级
- README 和 docs 已经包含了项目的核心信息
- 避免过度设计

## 3. 为什么先用本地样例

- 测试稳定：本地文件，可重复
- 无外部依赖：不需要网络
- 适合展示：样例内容可控

## 4. 测试稳定策略

- 全部使用本地 tempfile / 固定样例目录
- 不依赖网络、不依赖 git、不依赖外部 API

## 5. 后续升级路径

1. GitHub API（urllib + token）
2. MCP GitHub reader
3. `git clone` 到本地后读取
4. 工具调用模式（Agent 自主决定读取哪些文件）
