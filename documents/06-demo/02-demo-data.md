# Demo 数据

## 用途

本文档定义第一阶段 demo 数据的范围和脱敏规则。

## 推荐数据

### 主 demo 数据

- **用户资料**：`data/samples/profile/`（5 个文件）
- **岗位 JD**：`data/samples/jobs/agent_intern_jd.md`（AI Agent 开发实习生）

### 备用 JD

| JD 文件 | 岗位方向 | 适用场景 |
|---|---|---|
| `agent_intern_jd.md` | Agent 开发 | 主 demo |
| `rag_engineer_intern_jd.md` | RAG 工程师 | 展示检索相关匹配 |
| `ai_application_intern_jd.md` | AI 应用开发 | 展示香港岗位匹配 |
| `backend_ai_intern_jd.md` | 后端开发（AI 方向） | 展示后端岗位匹配 |

## 每个 profile 文件在 demo 中的作用

| 文件 | 内容 | demo 中的作用 |
|---|---|---|
| `resume.md` | 个人背景/教育/技术栈/项目概览 | 提供整体画像，检索综合信息 |
| `projects.md` | 4 个项目的技术架构和实现细节 | 检索具体项目经历，支撑简历 bullet |
| `github_repos.md` | 5 个 GitHub 仓库摘要 | 提供项目链接和技术栈证据 |
| `skills.md` | 分类技能详情 | 技能-岗位匹配的关键来源 |
| `internship.md` | 2 段实习/实践经历 | 提供实习经历证据 |

## 数据边界

- 使用样例或脱敏内容。
- 不放真实手机号、邮箱、学号、API Key。
- GitHub 仓库摘要优先描述项目价值、技术栈、用户负责内容和适配岗位方向。
- 用户设定为化学+计算机交叉背景，不过度包装。

## 当前状态

已创建 9 份示例数据（SAMPLE-001），覆盖完整的用户资料和 4 个岗位方向。所有数据为脱敏虚构内容。

详见 `data/samples/profile/` 和 `data/samples/jobs/`。

## 需要谨慎表达的内容

- 样例中使用"示例""虚构"等标记
- 不宣称"精通"某项技术，用"了解""使用过"代替
- 项目成果不夸大数字
- 避免暗示样例数据为真实个人信息

## 后续维护规则

- 样例数据应支持固定 demo case
- 资料不足时应在 demo 中展示"需要补充资料"的行为
- 新增样例需同步更新本文档
