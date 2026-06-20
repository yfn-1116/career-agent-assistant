# DEPLOY-001 学校服务器部署文档

## 任务编号

DEPLOY-001

## 建议执行者

Claude Code + DeepSeek

## 任务目标

补充学校服务器部署展示文档，确保 GitHub 拉取后可以复现 CLI 或 Streamlit demo。

## 允许修改文件

- `documents/98-runbook/03-school-server-deploy.md`
- `documents/98-runbook/04-troubleshooting.md`
- `documents/06-demo/03-presentation-flow.md`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/`
- `tests/`
- `data/`
- `outputs/`
- 部署脚本
- 服务器密钥或密码

## 输入

- GitHub 仓库地址。
- 第一阶段 demo 运行方式。
- 学校服务器环境信息。

## 输出

- 部署步骤。
- 环境检查。
- 验证方式。
- 常见问题排查。

## 实现要求

- 只写文档。
- 不提交真实服务器凭据。
- 不创建 server 目录。

## 验收标准

- 文档包含拉取代码、安装依赖、运行 demo、检查输出四个步骤。
- 包含模型不可用和端口不可访问的排查建议。

## 测试命令

```bash
git status --short
find documents/98-runbook -name '*.md' -type f -empty -print
```

## 提交信息建议

```text
docs: add school server deploy runbook
```
