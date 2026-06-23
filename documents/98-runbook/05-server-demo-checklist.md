# 服务器展示当天操作清单

> 用途：展示前逐项检查，确保演示顺利。建议提前 30 分钟执行。

## 准备阶段

- [ ] `cd /data/pytorch/career-agent-assistant`
- [ ] `git pull` 拉取最新代码
- [ ] `python3 --version` 确认 Python ≥ 3.10
- [ ] `pip install -e .` 安装当前项目
- [ ] 如 Streamlit 不存在，执行 `pip install streamlit pandas`

## 测试阶段

- [ ] 可选执行 `python -m pytest tests/rag tests/agents tests/workflows tests/demo -q`
- [ ] 如果时间有限，优先做 FastAPI / Streamlit smoke check

## CLI Demo 验证

- [ ] `python demo/cli/run_job_match_demo.py`
- [ ] 确认终端显示 `任务状态：completed`
- [ ] `cat outputs/demo/job_match_result.md` 确认输出内容完整

## FastAPI 验证

- [ ] 确认 FastAPI 启动在容器内 `8080`
- [ ] `curl -i http://127.0.0.1:8080/api/health`
- [ ] 浏览器打开 `http://218.197.18.192:8023/docs`
- [ ] 浏览器打开 `http://218.197.18.192:8023/api/health`

## Streamlit Demo 验证

- [ ] 确认 Streamlit 启动在容器内 `8082`
- [ ] `curl -i http://127.0.0.1:8082`
- [ ] 浏览器打开 `http://218.197.18.192:8024`
- [ ] 选择「AI Agent 开发实习生」JD → 点击运行 → 确认结果展示正常

## 展示时

- [ ] 准备好终端窗口（或 Streamlit 浏览器页面）
- [ ] 准备好 FastAPI Swagger 页面：`http://218.197.18.192:8023/docs`
- [ ] 准备好 Streamlit 页面：`http://218.197.18.192:8024`
- [ ] 准备好 `outputs/demo/job_match_result.md` 作为备用
- [ ] 确认已了解各模块的讲解要点（见 `documents/06-demo/01-demo-script.md`）

## 备用方案

如果 Streamlit 启动失败或网络不通：

1. 查看 `tail -n 100 outputs/streamlit.log`
2. 确认服务监听 `ss -lntp | grep -E ':8080|:8082'`
3. 如果 Streamlit 命令缺失，执行 `pip install streamlit pandas`
4. 回退到 CLI demo 或直接打开预先生成的 `outputs/demo/job_match_result.md`

## 展示后

- [ ] 如需停止服务：`pkill -f "uvicorn career_agent.api.app:app" || true`
- [ ] 如需停止服务：`pkill -f "streamlit run demo/streamlit/app.py" || true`
- [ ] 不要提交 `outputs/demo/*.md` 运行产物
- [ ] 服务器只用于展示，不在服务器上提交代码
