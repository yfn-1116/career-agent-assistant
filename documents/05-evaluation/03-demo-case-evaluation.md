# Demo Case 评估

## 评估目标

检查 demo 是否能在本地和学校服务器复现，并稳定展示核心链路。

## 输入样例

- 固定用户资料 Markdown。
- 固定 GitHub 仓库摘要 Markdown。
- 固定示例 JD Markdown。

## 评估指标

- CLI demo 是否能完整运行。
- 是否生成 Markdown 输出。
- 输出是否包含 JD 解析、检索证据、匹配分析和最终建议。
- 学校服务器是否能拉取 GitHub 仓库并复现。
- 模型不可用时是否有兜底展示方案。

## 人工检查方式

按照 runbook 从零执行 demo，记录每一步命令、输出文件和异常情况。

## 后续自动化方向

- 增加 smoke test。
- 增加 demo 输出快照。
- 增加服务器环境自检。

## 后续维护规则

每次 demo 流程变化都需要更新本文档和 `documents/06-demo/`。
