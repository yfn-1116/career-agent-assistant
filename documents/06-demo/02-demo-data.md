# Demo 数据

## 用途

本文档定义第一阶段 demo 数据的范围和脱敏规则。

## 推荐数据

- 示例用户简介 Markdown。
- 示例项目经历 Markdown。
- 示例 GitHub 仓库摘要 Markdown。
- 示例技能与实习经历 Markdown。
- 示例 Agent 实习岗位 JD Markdown。

## 数据边界

- 使用样例或脱敏内容。
- 不放真实手机号、邮箱、学号、API Key。
- GitHub 仓库摘要优先描述项目价值、技术栈、用户负责内容和适配岗位方向。

## 当前状态

已创建 4 份示例数据（SAMPLE-001 完成）：

| 文件 | 内容 | 用途 |
|---|---|---|
| `data/samples/profile.md` | 个人能力资料（技能/项目/实习/教育） | RAG 检索源 |
| `data/samples/projects.md` | 3 个项目经历详情 | 精确检索细节 |
| `data/samples/github_summary.md` | 5 个 GitHub 仓库摘要 | 项目经历匹配 |
| `data/samples/jd_agent_intern.md` | 3 个 AI 实习岗位 JD | JD 解析和匹配验证 |

所有数据均为脱敏虚构内容，不包含真实手机号、邮箱、学号、API Key。

## 后续维护规则

- 样例数据应支持固定 demo case。
- 资料不足时应在 demo 中展示“需要补充资料”的行为。
