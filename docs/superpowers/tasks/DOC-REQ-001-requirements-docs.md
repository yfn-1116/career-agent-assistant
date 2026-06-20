# DOC-REQ-001 需求文档补强

## 任务编号

DOC-REQ-001

## 建议执行者

Claude Code + DeepSeek

## 任务目标

补充用户场景、MVP 范围、非目标和验收标准，使需求文档能指导后续 RAG、Agent 和 demo 任务。

## 允许修改文件

- `documents/01-requirements/`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/`
- `tests/`
- `data/`
- `outputs/`
- `documents/02-design/`
- 依赖配置文件

## 输入

- 用户提供的项目背景。
- `documents/00-project-overview.md`

## 输出

- 完整需求场景。
- MVP 范围和非目标。
- 可验证验收标准。

## 实现要求

- 只写中文 Markdown。
- 不写实现方案和业务代码。
- 明确第一阶段不是完整求职平台。

## 验收标准

- 至少覆盖岗位判断、项目经历改写、沟通话术、避免编造和学校服务器展示场景。
- 明确自动投递、爬取岗位网站、完整前后端、多用户系统等非目标。

## 测试命令

```bash
git status --short
find documents/01-requirements -name '*.md' -type f -empty -print
```

## 提交信息建议

```text
docs: expand first phase requirements
```
