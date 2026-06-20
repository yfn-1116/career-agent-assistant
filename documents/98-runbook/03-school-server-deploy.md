# 学校服务器部署与展示

## 1. 在服务器上克隆项目

```bash
git clone https://github.com/yfn-1116/career-agent-assistant.git
cd career-agent-assistant
```

## 2. 后续更新

```bash
git pull
```

## 3. 环境准备

### 创建虚拟环境（可选但推荐）

```bash
python3 -m venv venv
source venv/bin/activate
```

### 安装测试依赖

```bash
pip install pytest
```

本项目不依赖外部大模型 API，无需额外配置。

## 4. 运行测试确认环境正常

```bash
PYTHONPATH=src pytest tests/rag tests/agents tests/workflows tests/demo -v
```

预期约 150 个测试全部通过。

## 5. 运行 CLI demo

```bash
PYTHONPATH=src python demo/cli/run_job_match_demo.py
```

终端会显示：

```text
任务状态：completed
岗位方向：agent
检索证据：5 条
输出文件：outputs/demo/job_match_result.md
Done.
```

## 6. 查看输出

```bash
cat outputs/demo/job_match_result.md
```

输出文件包含完整的 JD 解析、检索证据、匹配分析和生成结果。

## 7. 展示给老师或同学

**当前阶段展示要点**：

1. 这是一个**实习求职智能投递辅助 Agent 原型**（CLI demo）
2. 输入：用户 Markdown 个人能力资料 + 岗位 JD
3. 输出：JD 解析 → RAG 检索 → 匹配分析 → 简历 bullet + 沟通话术
4. 当前使用**规则和模板**，不调用外部大模型，**保证可复现**
5. 后续将接入 DeepSeek API 升级为 LLM 驱动，并增加 Streamlit 可视化展示

**建议展示流程**：

1. 用 `cat` 展示样例用户资料（`data/samples/profile/resume.md`）
2. 用 `cat` 展示样例 JD（`data/samples/jobs/agent_intern_jd.md`）
3. 运行 `PYTHONPATH=src python demo/cli/run_job_match_demo.py`
4. 打开 `outputs/demo/job_match_result.md` 逐段讲解

## 8. 后续 Streamlit 展示（预留）

后续将开发 Streamlit demo，届时可在服务器上运行：

```bash
streamlit run demo/streamlit/app.py
```

（当前尚未实现，仅供预留参考）
