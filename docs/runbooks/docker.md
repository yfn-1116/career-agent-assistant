# Docker 运行指南

## 适用范围

本文档只适用于本地开发机或普通云服务器 Docker 环境。

**不要在当前学校展示服务器上使用 Docker Compose。** 学校服务器已经是老师启动好的 Docker/Jupyter 容器，外部端口也已经映射完成：

- FastAPI：容器内 `8080` -> 外部 `8023`
- Streamlit：容器内 `8082` -> 外部 `8024`
- Jupyter：容器内 `8206` -> 外部 `8206`

学校服务器部署请使用 `documents/98-runbook/03-school-server-deploy.md`，不要执行 `docker compose up --build`。

## 前置条件

- Docker 已安装
- 项目根目录有 `.env` 文件（复制自 `.env.example`）

## 快速启动

```bash
# 1. 复制环境配置（如果还没有 .env）
cp .env.example .env

# 2. 构建并启动
docker compose up --build

# 3. 打开浏览器
# http://localhost:8501
```

## 使用 mock LLM 运行（默认）

`.env.example` 默认 `LLM_PROVIDER=mock`，无需 API key 即可运行 demo。

```bash
cp .env.example .env
docker compose up --build
```

## 使用真实 LLM 运行

编辑 `.env`：

```
LLM_PROVIDER=qwen
LLM_API_KEY=sk-your-key
LLM_MODEL=qwen-plus
EMBEDDING_PROVIDER=qwen
EMBEDDING_MODEL=text-embedding-v3
```

然后：

```bash
docker compose up --build
```

## 挂载说明

| 宿主机路径 | 容器路径 | 用途 |
|-----------|---------|------|
| `./data/` | `/app/data/` | 用户资料、JD 样例 |
| `./outputs/` | `/app/outputs/` | 报告输出 |

## 常用命令

```bash
# 后台运行
docker compose up -d

# 查看日志
docker compose logs -f

# 停止
docker compose down

# 重新构建（代码变更后）
docker compose up --build
```
