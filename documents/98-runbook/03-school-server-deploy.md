# 学校服务器部署与展示

## 1. 部署目标

学校服务器用于展示 `career-agent-assistant` 原型，不作为生产环境使用。

实际部署方式是：**在老师已经启动好的 Docker/Jupyter 容器内直接运行 FastAPI 和 Streamlit**。不要在该环境里优先使用 Docker Compose，也不要再套一层 Docker 容器。

核心流程：

```text
本地修改代码
-> git add / commit / push
-> 学校服务器 git pull
-> pip install -e .
-> 重启 FastAPI 和 Streamlit
-> 打开 8023 / 8024 展示
```

服务器只用于展示，原则上不在服务器上修改代码。

## 2. 实际服务器环境

| 项 | 值 |
|---|---|
| 当前登录目录 | `/data/pytorch` |
| 项目目录 | `/data/pytorch/career-agent-assistant` |
| 容器 hostname | `team1-192` |
| 当前用户 | `user` |
| Jupyter 外部地址 | `http://218.197.18.192:8206/tree` |

当前环境不是普通云服务器，而是老师预先分配并启动好的容器。外部端口已经由老师映射到容器内部端口。

## 3. 端口映射

| 服务 | 容器内端口 | 外部端口 | 外部访问地址 |
|---|---:|---:|---|
| Jupyter | 8206 | 8206 | `http://218.197.18.192:8206/tree` |
| FastAPI | 8080 | 8023 | `http://218.197.18.192:8023/docs` |
| FastAPI Health | 8080 | 8023 | `http://218.197.18.192:8023/api/health` |
| Streamlit | 8082 | 8024 | `http://218.197.18.192:8024` |

因此学校服务器部署时不要使用默认端口 `8000` / `8501`。服务必须监听：

```text
FastAPI:   0.0.0.0:8080
Streamlit: 0.0.0.0:8082
```

## 4. 不使用 Docker Compose

在当前服务器环境中执行：

```bash
docker compose version
```

会报：

```text
docker: 'compose' is not a docker command.
```

所以学校服务器部署不要使用：

```bash
docker compose up --build
```

原因：

- 当前已经在老师分配好的容器里；
- 外部端口已经由老师映射好；
- 再在容器里套 Docker 容器会增加复杂度；
- 容器内再映射端口容易导致外部无法访问。

Docker Compose 文档只适用于本地或普通云服务器，不适用于当前学校展示服务器。

## 5. 首次拉取项目

```bash
cd /data/pytorch
git clone https://github.com/yfn-1116/career-agent-assistant.git
cd career-agent-assistant
```

安装项目依赖：

```bash
cd /data/pytorch/career-agent-assistant
pip install -e .
```

项目主要通过 `pyproject.toml` 管理依赖，没有 `requirements.txt`。此前已验证 `pip install -e .` 可以成功安装核心依赖，包括 FastAPI、uvicorn、LangGraph 等。

如果 Streamlit 不存在，额外安装：

```bash
pip install streamlit pandas
```

建议使用 `python -m streamlit` 启动，不直接依赖 `streamlit` 命令是否在 PATH 中。

## 6. 后续更新

```bash
cd /data/pytorch/career-agent-assistant
git pull
pip install -e .
```

如果本地代码已 push 到 GitHub，服务器只需要 `git pull`、重新安装 editable package，然后重启 FastAPI 和 Streamlit。

## 7. 启动 FastAPI 后端

FastAPI 必须跑在容器内部 `8080`，因为外部 `8023` 映射到容器内部 `8080`。

```bash
cd /data/pytorch/career-agent-assistant

mkdir -p runtime outputs

nohup python -m uvicorn career_agent.api.app:app \
  --host 0.0.0.0 \
  --port 8080 \
  > outputs/api.log 2>&1 &
```

检查：

```bash
curl -i http://127.0.0.1:8080/api/health
curl -i http://127.0.0.1:8080/docs
```

健康检查正常返回：

```json
{"status":"ok","version":"1.3","service_name":"Internship Copilot API"}
```

外部访问：

```text
http://218.197.18.192:8023/docs
http://218.197.18.192:8023/api/health
```

注意：`curl http://127.0.0.1:8080/` 返回 `404` 是正常的，因为项目没有定义根路径 `/`，真正的健康检查是 `/api/health`。

## 8. 启动 Streamlit 前端

Streamlit 必须跑在容器内部 `8082`，因为外部 `8024` 映射到容器内部 `8082`。

```bash
cd /data/pytorch/career-agent-assistant

mkdir -p runtime outputs

nohup python -m streamlit run demo/streamlit/app.py \
  --server.address 0.0.0.0 \
  --server.port 8082 \
  --server.headless true \
  --browser.gatherUsageStats false \
  > outputs/streamlit.log 2>&1 &
```

检查：

```bash
curl -i http://127.0.0.1:8082
```

外部访问：

```text
http://218.197.18.192:8024
```

如果 Streamlit 启动失败并出现 `Exit 127`，通常表示 `streamlit` 命令不存在。安装后重试：

```bash
pip install streamlit pandas
python -m streamlit run demo/streamlit/app.py \
  --server.address 0.0.0.0 \
  --server.port 8082 \
  --server.headless true \
  --browser.gatherUsageStats false
```

## 9. 一键启动脚本

可在服务器项目目录创建 `start_demo.sh`：

```bash
cd /data/pytorch/career-agent-assistant

cat > start_demo.sh <<'EOF'
#!/usr/bin/env bash
set -e

cd /data/pytorch/career-agent-assistant

mkdir -p runtime outputs

echo "=== Stop old services if any ==="
pkill -f "uvicorn career_agent.api.app:app" || true
pkill -f "streamlit run demo/streamlit/app.py" || true

echo "=== Start FastAPI on container port 8080 ==="
nohup python -m uvicorn career_agent.api.app:app \
  --host 0.0.0.0 \
  --port 8080 \
  > outputs/api.log 2>&1 &

echo "=== Start Streamlit on container port 8082 ==="
nohup python -m streamlit run demo/streamlit/app.py \
  --server.address 0.0.0.0 \
  --server.port 8082 \
  --server.headless true \
  --browser.gatherUsageStats false \
  > outputs/streamlit.log 2>&1 &

sleep 3

echo "=== FastAPI health ==="
curl -s http://127.0.0.1:8080/api/health || true

echo ""
echo "=== Listening ports ==="
ss -lntp | grep -E ':8080|:8082' || true

echo ""
echo "=== Visit links ==="
echo "Jupyter:          http://218.197.18.192:8206/tree"
echo "FastAPI Swagger:  http://218.197.18.192:8023/docs"
echo "FastAPI Health:   http://218.197.18.192:8023/api/health"
echo "Streamlit Demo:   http://218.197.18.192:8024"
EOF

chmod +x start_demo.sh
```

以后启动：

```bash
cd /data/pytorch/career-agent-assistant
./start_demo.sh
```

## 10. 一键更新并启动脚本

如果本地代码修改后已经 push 到 GitHub，服务器只需要 pull 并重启。可在服务器项目目录创建 `update_and_start.sh`：

```bash
cd /data/pytorch/career-agent-assistant

cat > update_and_start.sh <<'EOF'
#!/usr/bin/env bash
set -e

cd /data/pytorch/career-agent-assistant

echo "=== Git status before pull ==="
git status --short

echo "=== Pull latest code ==="
git pull

echo "=== Install editable package ==="
pip install -e .

echo "=== Stop old services if any ==="
pkill -f "uvicorn career_agent.api.app:app" || true
pkill -f "streamlit run demo/streamlit/app.py" || true

mkdir -p runtime outputs

echo "=== Start FastAPI on container port 8080 ==="
nohup python -m uvicorn career_agent.api.app:app \
  --host 0.0.0.0 \
  --port 8080 \
  > outputs/api.log 2>&1 &

echo "=== Start Streamlit on container port 8082 ==="
nohup python -m streamlit run demo/streamlit/app.py \
  --server.address 0.0.0.0 \
  --server.port 8082 \
  --server.headless true \
  --browser.gatherUsageStats false \
  > outputs/streamlit.log 2>&1 &

sleep 3

echo "=== FastAPI health ==="
curl -s http://127.0.0.1:8080/api/health || true

echo ""
echo "=== Listening ports ==="
ss -lntp | grep -E ':8080|:8082' || true

echo ""
echo "=== Visit links ==="
echo "Jupyter:          http://218.197.18.192:8206/tree"
echo "FastAPI Swagger:  http://218.197.18.192:8023/docs"
echo "FastAPI Health:   http://218.197.18.192:8023/api/health"
echo "Streamlit Demo:   http://218.197.18.192:8024"
EOF

chmod +x update_and_start.sh
```

以后更新并启动：

```bash
cd /data/pytorch/career-agent-assistant
./update_and_start.sh
```

## 11. 查看日志与状态

查看后端日志：

```bash
tail -n 100 outputs/api.log
```

查看前端日志：

```bash
tail -n 100 outputs/streamlit.log
```

查看进程：

```bash
ps aux | grep -E 'uvicorn|streamlit'
```

查看端口：

```bash
ss -lntp | grep -E ':8080|:8082|:8206'
```

## 12. 停止服务

```bash
pkill -f "uvicorn career_agent.api.app:app" || true
pkill -f "streamlit run demo/streamlit/app.py" || true
```

## 13. 如果出现 Git 冲突

服务器只用于展示，原则上不在服务器改代码，所以一般不会冲突。

先查看：

```bash
git status
```

如果确认服务器本地修改不要，可以恢复：

```bash
git restore .
git pull
```

如果状态很乱，可以重新拉一份：

```bash
cd /data/pytorch
mv career-agent-assistant career-agent-assistant.bak
git clone https://github.com/yfn-1116/career-agent-assistant.git
cd career-agent-assistant
pip install -e .
```

然后重新启动 `8080` / `8082`。

## 14. 最终部署逻辑总结

```text
不是 docker compose 部署
而是在老师已经启动的容器内直接运行服务

FastAPI:
容器内 8080 -> 外部 8023

Streamlit:
容器内 8082 -> 外部 8024

Jupyter:
容器内 8206 -> 外部 8206
```

部署时只需要：

```text
git pull
pip install -e .
启动 uvicorn 到 8080
启动 streamlit 到 8082
打开 8023 / 8024
```
