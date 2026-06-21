# 学校服务器部署与展示

## 1. 部署目标

- 项目在本地电脑开发，通过 GitHub 同步
- 学校服务器通过 `git clone` / `git pull` 获取项目
- 服务器用于展示 CLI demo（默认）或 Streamlit demo（可选）
- **不部署生产服务**，不配置数据库或消息队列

## 2. 环境要求

| 依赖 | 版本要求 | 说明 |
|---|---|---|
| Python | 3.10+ | 过低版本可能语法不兼容 |
| Git | 任意 | 用于 clone 和 pull |
| pip | 任意 | 安装项目与可选 demo 依赖 |
| pytest | 最新 | 用于运行测试 |
| streamlit | 1.30+（可选） | 通过 `python -m pip install -e ".[demo]"` 安装 |

**不依赖**：GPU、外部大模型 API、数据库、Redis、Docker。

## 3. 首次部署步骤

```bash
# 1. 克隆仓库
git clone https://github.com/yfn-1116/career-agent-assistant.git
cd career-agent-assistant

# 2. 创建虚拟环境（推荐）
python3 -m venv .venv
source .venv/bin/activate

# 3. 安装项目依赖
python -m pip install -e .

# 4. 运行全部测试确认环境正常
pytest tests -q
# 预期约 165 个测试全部通过
```

## 4. 运行 CLI demo（默认展示方式）

```bash
python demo/cli/run_job_match_demo.py
```

终端输出：

```text
任务状态：completed
岗位方向：agent
检索证据：5 条
输出文件：outputs/demo/job_match_result.md
Done.
```

查看输出：

```bash
cat outputs/demo/job_match_result.md
```

## 5. 运行 Streamlit demo（可选可视化展示）

### 安装

```bash
python -m pip install -e ".[demo]"
```

### 启动

```bash
streamlit run demo/streamlit/app.py --server.address 0.0.0.0 --server.port 8501
```

启动后终端会显示访问地址（如 `http://<服务器IP>:8501`）。

### 端口说明

- 默认端口 8501
- 如果服务器端口未开放，**外部无法访问**
- 可以先在本机或内网访问：`http://localhost:8501`
- 若学校服务器有防火墙限制，联系管理员开放端口，或使用 SSH 端口转发：

  ```bash
  # 在本地电脑执行，将服务器 8501 转发到本地 8501
  ssh -L 8501:localhost:8501 user@server-ip
  # 然后本地浏览器访问 http://localhost:8501
  ```

- **不要把 token、密钥写入仓库**

## 6. 后续更新

```bash
cd career-agent-assistant
git pull
source .venv/bin/activate  # 如果使用虚拟环境
python -m pip install -e .
pytest tests -q

# 确认测试通过后运行 demo
python demo/cli/run_job_match_demo.py
```

## 7. 展示给老师或同学

### 展示要点

1. 这是一个**实习求职智能投递辅助 Agent 原型**
2. 输入：用户 Markdown 个人能力资料 + 岗位 JD
3. 输出：JD 解析 → RAG 检索 → 匹配分析 → 简历 bullet + 沟通话术
4. 当前使用**规则和模板**，不调用外部大模型，**保证可复现**
5. 后续可接入 DeepSeek API 升级为 LLM 驱动

### 建议展示流程

**方案 A：CLI demo（稳定）**

1. `cat data/samples/profile/resume.md` — 展示样例用户资料
2. `cat data/samples/jobs/agent_intern_jd.md` — 展示样例 JD
3. `python demo/cli/run_job_match_demo.py` — 运行
4. `cat outputs/demo/job_match_result.md` — 逐段讲解输出

**方案 B：Streamlit demo（可视化）**

1. 启动 Streamlit：同上命令
2. 浏览器打开页面
3. 选择示例 JD → 点击运行 → 逐区域展示结果
4. 如果 Streamlit 启动失败，回退到方案 A

## 8. 展示前检查清单

参见 `05-server-demo-checklist.md`。
