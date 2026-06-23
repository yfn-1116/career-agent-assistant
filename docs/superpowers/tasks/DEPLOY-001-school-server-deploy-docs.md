# DEPLOY-001 学校服务器部署文档

## 任务编号

DEPLOY-001

## 建议执行者

Claude Code + DeepSeek

## 任务目标

补充学校服务器部署展示文档，确保 GitHub 拉取后可以在老师已启动的 Docker/Jupyter 容器内复现 FastAPI 和 Streamlit demo。

## 允许修改文件

- `documents/98-runbook/03-school-server-deploy.md`
- `documents/98-runbook/04-troubleshooting.md`
- `documents/98-runbook/05-server-demo-checklist.md`
- `documents/98-runbook/README.md`
- `docs/runbooks/browser_assistant_usage.md`
- `docs/runbooks/docker.md`
- `README.md`
- `documents/06-demo/03-presentation-flow.md`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/`
- `tests/`
- `data/`
- `outputs/`
- 仓库内可执行部署脚本
- 服务器密钥或密码

## 输入

- GitHub 仓库地址。
- 第一阶段 demo 运行方式。
- 学校服务器环境信息：当前服务器是老师已启动的 Docker/Jupyter 容器，登录目录 `/data/pytorch`，项目目录 `/data/pytorch/career-agent-assistant`。
- 实际端口映射：外部 `8023` -> 容器内 `8080` -> FastAPI；外部 `8024` -> 容器内 `8082` -> Streamlit；外部 `8206` -> 容器内 `8206` -> Jupyter。

## 输出

- 部署步骤。
- 环境检查。
- 验证方式。
- 常见问题排查。
- 服务器本地 `start_demo.sh` 和 `update_and_start.sh` 脚本片段。

## 实现要求

- 只写文档；脚本以 runbook 片段形式提供，不在仓库内新增可执行部署脚本。
- 不提交真实服务器凭据。
- 不创建 server 目录。
- 明确学校服务器不使用 Docker Compose。
- 明确学校服务器不要使用默认 `8000` / `8501`，FastAPI 使用容器内 `8080`，Streamlit 使用容器内 `8082`。

## 验收标准

- 文档包含拉取代码、安装依赖、启动 FastAPI、启动 Streamlit、检查输出五个步骤。
- 包含 Docker Compose 不适用、Streamlit command not found、端口不可访问、Git 冲突的排查建议。
- 文档给出外部访问地址：`http://218.197.18.192:8023/docs`、`http://218.197.18.192:8023/api/health`、`http://218.197.18.192:8024`。

## 测试命令

```bash
git status --short
find documents/98-runbook -name '*.md' -type f -empty -print
```

## 提交信息建议

```text
docs: add school server deploy runbook
```
