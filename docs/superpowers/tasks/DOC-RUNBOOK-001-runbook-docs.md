# DOC-RUNBOOK-001 Runbook 文档补强

## 任务编号

DOC-RUNBOOK-001

## 建议执行者

Claude Code + DeepSeek

## 任务目标

补充本地开发、GitHub 同步、学校服务器部署和故障排查文档。

## 允许修改文件

- `documents/98-runbook/`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/`
- `tests/`
- `data/`
- `outputs/`
- `.env.example`
- 部署脚本

## 输入

- 当前仓库结构。
- GitHub 同步方式。
- 学校服务器展示目标。

## 输出

- 可执行 runbook 草案。
- 常见故障排查清单。

## 实现要求

- 不写脚本。
- 不提交密钥、服务器密码或私有路径。
- 命令需要可复制执行。

## 验收标准

- 本地、GitHub、服务器和 troubleshooting 四类文档都有步骤和验证方式。

## 测试命令

```bash
git status --short
find documents/98-runbook -name '*.md' -type f -empty -print
```

## 提交信息建议

```text
docs: expand local and server runbooks
```
