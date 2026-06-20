# 服务器展示当天操作清单

> 用途：展示前逐项检查，确保演示顺利。建议提前 30 分钟执行。

## 准备阶段

- [ ] `cd career-agent-assistant`
- [ ] `git pull` 拉取最新代码
- [ ] `python3 --version` 确认 Python ≥ 3.10
- [ ] `source .venv/bin/activate` 激活虚拟环境（如有）
- [ ] `pip install pytest` 确认 pytest 已安装

## 测试阶段

- [ ] `PYTHONPATH=src pytest tests/rag tests/agents tests/workflows tests/demo -v`
- [ ] 确认约 165 个测试全部通过
- [ ] 如果有测试失败，查看错误信息并排查

## CLI Demo 验证

- [ ] `PYTHONPATH=src python demo/cli/run_job_match_demo.py`
- [ ] 确认终端显示 `任务状态：completed`
- [ ] `cat outputs/demo/job_match_result.md` 确认输出内容完整

## Streamlit Demo 验证（可选）

- [ ] `pip install streamlit`（如未安装）
- [ ] `PYTHONPATH=src streamlit run demo/streamlit/app.py --server.address 0.0.0.0 --server.port 8501`
- [ ] 浏览器打开 `http://localhost:8501`
- [ ] 选择「AI Agent 开发实习生」JD → 点击运行 → 确认结果展示正常

## 展示时

- [ ] 准备好终端窗口（或 Streamlit 浏览器页面）
- [ ] 准备好 `outputs/demo/job_match_result.md` 作为备用
- [ ] 确认已了解各模块的讲解要点（见 `documents/06-demo/01-demo-script.md`）

## 备用方案

如果 Streamlit 启动失败或网络不通：

1. 回退到 CLI demo
2. 直接打开预先生成的 `outputs/demo/job_match_result.md`
3. 用 Markdown 文件展示核心链路即可

## 展示后

- [ ] `Ctrl+C` 停止 Streamlit（如使用）
- [ ] 不要提交 `outputs/demo/*.md` 运行产物
- [ ] 如有修改，按需 `git add` / `git commit` / `git push`
