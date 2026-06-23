# 常见问题排查

## 1. git push 失败

**现象**：`error: failed to push some refs`

**原因**：远端有你的本地没有的提交。

**解决**：

```bash
git pull --rebase
git push
```

如果有冲突，手动解决后再 push。

---

## 2. Token 权限问题

**现象**：`remote: Permission denied` 或 `403`

**解决**：

- 确认 GitHub token 未过期
- 确认 token 有 repo 权限
- 如果用 HTTPS，确认 credential helper 配置正确：

  ```bash
  git config --global credential.helper store
  ```

---

## 3. ModuleNotFoundError: No module named 'career_agent'

**解决**：在命令前加上 `PYTHONPATH=src`：

```bash
PYTHONPATH=src python demo/cli/run_job_match_demo.py
PYTHONPATH=src pytest tests/rag -v
```

---

## 4. pytest 找不到

**现象**：`pytest: command not found`

**解决**：

```bash
pip install pytest
```

如果使用虚拟环境，确认已激活：

```bash
source venv/bin/activate
```

---

## 5. 测试失败

**现象**：某些测试显示 FAILED

**排查步骤**：

1. 确认 PYTHONPATH 已设置：`PYTHONPATH=src pytest ...`
2. 确认在项目根目录执行命令
3. 确认 `data/samples/` 中的样例文件未被修改或删除
4. 查看失败测试的具体错误信息：`pytest -v --tb=long`

---

## 6. demo 输出为空或内容很少

**原因**：可能是向量检索未命中。

**检查**：

- `data/samples/profile/` 下有 5 个 `.md` 文件
- sample 文件未被修改，内容完整
- 尝试降低 `--top-k` 或使用不同的 JD 文件测试

---

## 7. 路径不一致

**现象**：`FileNotFoundError` 或找不到 sample 文件

**解决**：确保命令在项目根目录（`career-agent-assistant/`）下执行。

检查当前目录：

```bash
pwd
ls data/samples/profile/
```

---

## 8. Windows / WSL 路径问题

**WSL 用户**：项目路径建议放在 WSL 文件系统（如 `/home/...`）而非 `/mnt/c/...`，以避免文件权限和换行符问题。

**Windows 用户**：如果使用 PowerShell，`PYTHONPATH=src` 语法不同：

```powershell
$env:PYTHONPATH = "src"
python demo/cli/run_job_match_demo.py
```

或在 CMD 中：

```cmd
set PYTHONPATH=src
python demo/cli/run_job_match_demo.py
```

---

## 9. 学校服务器 Python 版本问题

**现象**：语法错误或模块不兼容

**解决**：

- 检查 Python 版本：`python3 --version`
- 本项目需要 Python 3.10 或以上
- 如果服务器默认 Python 版本过低，检查是否有 `python3.10` 或 `python3.11` 可用
- 或使用 pyenv / conda 安装合适版本

---

## 10. Streamlit command not found

**现象**：`streamlit: command not found`

**解决**：

```bash
pip install streamlit pandas
```

学校服务器建议使用：

```bash
python -m streamlit run demo/streamlit/app.py \
  --server.address 0.0.0.0 \
  --server.port 8082 \
  --server.headless true \
  --browser.gatherUsageStats false
```

---

## 11. 学校服务器 8023 / 8024 无法访问

**现象**：浏览器打不开 FastAPI Swagger 或 Streamlit 页面

**排查**：

1. 确认当前是在 `/data/pytorch/career-agent-assistant`。
2. 确认 FastAPI 监听容器内 `8080`：`curl -i http://127.0.0.1:8080/api/health`。
3. 确认 Streamlit 监听容器内 `8082`：`curl -i http://127.0.0.1:8082`。
4. 查看监听端口：`ss -lntp | grep -E ':8080|:8082|:8206'`。
5. 查看日志：`tail -n 100 outputs/api.log` 和 `tail -n 100 outputs/streamlit.log`。
6. 不要改用默认 `8000` / `8501`。学校服务器外部 `8023` 映射容器内 `8080`，外部 `8024` 映射容器内 `8082`。

外部访问地址：

```text
FastAPI Swagger:  http://218.197.18.192:8023/docs
FastAPI Health:   http://218.197.18.192:8023/api/health
Streamlit Demo:   http://218.197.18.192:8024
```

注意：`curl http://127.0.0.1:8080/` 返回 `404` 是正常的，健康检查路径是 `/api/health`。

---

## 12. 学校服务器误用 Docker Compose

**现象**：

```text
docker: 'compose' is not a docker command.
```

**解决**：

当前学校服务器已经是老师启动好的 Docker/Jupyter 容器，不使用 `docker compose up --build`。直接在容器内运行：

```bash
cd /data/pytorch/career-agent-assistant
pip install -e .
python -m uvicorn career_agent.api.app:app --host 0.0.0.0 --port 8080
python -m streamlit run demo/streamlit/app.py --server.address 0.0.0.0 --server.port 8082 --server.headless true
```

---

## 13. 服务器没有外网

**解决**：

- 在有网络的机器上 `git clone`，用 U 盘拷贝到服务器
- 在有网络的机器上 `pip download pytest streamlit`，拷贝 `.whl` 文件到服务器安装

---

## 14. outputs/demo 产物是否要提交

**不要提交**。`.gitignore` 已配置忽略 `outputs/demo/*.md`。

这些是 demo 运行产物，每次运行可能不同，不应进入版本控制。
