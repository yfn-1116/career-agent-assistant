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

已创建 9 份示例数据（SAMPLE-001 按新结构重建）：

### 用户资料 (`data/samples/profile/`)

| 文件 | 内容 | 用途 |
|---|---|---|
| `resume.md` | 个人简历（背景/教育/技术栈/项目/实习/求职方向） | RAG 检索源 |
| `projects.md` | 4 个项目经历详情（Agent/滴定/Smart Journey/CNN） | 精确检索 |
| `github_repos.md` | 5 个 GitHub 仓库摘要 | 项目经历匹配 |
| `skills.md` | 技能详情（Python/AI/Web/CV/硬件/工具链/领域） | 技能-岗位匹配 |
| `internship.md` | 实习与实践经历详情 | 经历-岗位匹配 |

### 岗位 JD (`data/samples/jobs/`)

| 文件 | 内容 | 用途 |
|---|---|---|
| `agent_intern_jd.md` | AI Agent 开发实习生 JD | JD 解析和匹配 |
| `rag_engineer_intern_jd.md` | RAG 工程师实习生 JD | 检索相关岗位匹配 |
| `ai_application_intern_jd.md` | AI 应用开发实习生 JD | 香港岗位匹配 |
| `backend_ai_intern_jd.md` | 后端开发实习生（AI 方向）JD | 后端岗位匹配 |

所有数据均为脱敏虚构内容，不包含真实手机号、邮箱、学号、API Key。

## 后续维护规则

- 样例数据应支持固定 demo case。
- 资料不足时应在 demo 中展示“需要补充资料”的行为。
