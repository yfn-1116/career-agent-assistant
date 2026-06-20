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
pip install streamlit
```

如果使用虚拟环境，确认已激活：

```bash
source .venv/bin/activate
```

---

## 11. 端口 8501 无法访问

**现象**：浏览器打不开 Streamlit 页面

**排查**：

1. 确认 Streamlit 已启动且无报错
2. 先在本机测试：`http://localhost:8501`
3. 如果本机可访问但外部不可，检查防火墙
4. 使用 SSH 端口转发（见部署文档）

---

## 12. 服务器没有外网

**解决**：

- 在有网络的机器上 `git clone`，用 U 盘拷贝到服务器
- 在有网络的机器上 `pip download pytest streamlit`，拷贝 `.whl` 文件到服务器安装

---

## 13. outputs/demo 产物是否要提交

**不要提交**。`.gitignore` 已配置忽略 `outputs/demo/*.md`。

这些是 demo 运行产物，每次运行可能不同，不应进入版本控制。
