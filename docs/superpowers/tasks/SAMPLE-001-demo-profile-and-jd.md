# SAMPLE-001 示例用户资料与岗位 JD

## 任务编号

SAMPLE-001

## 建议执行者

Claude Code + DeepSeek

## 任务目标

编写脱敏示例用户资料、项目经历、GitHub 仓库摘要和示例岗位 JD，用于 RAG 与 demo 验证。

## 允许修改文件

- `data/samples/`
- `documents/06-demo/02-demo-data.md`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/`
- `tests/`
- `outputs/`
- 依赖配置文件
- 真实隐私资料

## 输入

- 第一阶段用户场景。
- RAG 资料格式设计。

## 输出

- 示例 profile Markdown。
- 示例 project Markdown。
- 示例 GitHub repo summary Markdown。
- 示例 JD Markdown。

## 实现要求

- 只写样例数据。
- 不写代码。
- 不包含真实手机号、邮箱、学号、API Key。

## 验收标准

- 样例数据能覆盖 Agent 实习岗位。
- 每份资料能支持至少一个检索证据。
- JD 能触发 RAG、Agent 和 demo 链路。

## 测试命令

```bash
git status --short
find data/samples -type f -empty -print
```

## 提交信息建议

```text
docs: add sample profile and jd data
```
