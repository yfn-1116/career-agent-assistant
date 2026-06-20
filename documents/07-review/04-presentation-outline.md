# 答辩 / 展示大纲

> 建议时长：10-12 分钟 | 适用场景：期末实训答辩、实习面试展示

## 一、问题引入（1 分钟）

**讲什么**：

- 找实习时对着多份 JD，想不起自己的哪些经历能对上
- 手动匹配效率低，容易遗漏有价值的项目经历
- 需要一个工具：把经历文档化 → 自动匹配 JD

**展示**：口头说明，不需要屏幕。

## 二、技术路线（1.5 分钟）

**讲什么**：

- **RAG**（检索增强生成）：把个人经历存为可检索知识库
- **Multi-Agent**：4 个 Agent 各司其职，职责清晰
- 第一阶段不调大模型，用规则和模板保证可复现

**展示**：可以画一个简单流程图（白板或幻灯片）。

```text
Markdown 资料 → RAG Pipeline → Agent Pipeline → 输出
                  ↑ 检索           ↓ 解析→分析→生成
```

## 三、Demo 演示（4 分钟）

### 方案 A：CLI Demo（稳妥）

```bash
# 1. 展示样例资料
cat data/samples/profile/resume.md | head -20

# 2. 展示样例 JD
cat data/samples/jobs/agent_intern_jd.md | head -15

# 3. 运行
PYTHONPATH=src python demo/cli/run_job_match_demo.py

# 4. 展示输出
cat outputs/demo/job_match_result.md
```

逐段讲解：JD 解析 → 检索证据 → 匹配分析 → 生成输出

### 方案 B：Streamlit Demo（可视化）

启动 `PYTHONPATH=src streamlit run demo/streamlit/app.py`，浏览器展示交互流程。

## 四、工程实践（1.5 分钟）

**讲什么**：

- **文档先行**：设计文档 → 技术决策 → 任务卡 → 代码实现
- **165 个自动化测试**：RAG 61 + Agent 68 + Workflow 11 + Demo 25
- **多 AI 协作**：Codex + Claude Code + DeepSeek 分工
- **每步都有 journal 记录**，可追溯

**展示**：`documents/` 目录结构，`git log --oneline`。

## 五、技术亮点（1.5 分钟）

**讲什么**：

1. 完整的 RAG pipeline 分层设计（5 层可替换）
2. Agent 边界清晰（每个 Agent 只读写自己的字段）
3. 证据溯源（输出 bullet 可追溯到原始段落）
4. 零外部依赖（不联网也能跑）
5. 两种展示方式（CLI + Streamlit）

## 六、不足与后续（1 分钟）

**坦诚说不足**：

- 当前检索是关键词匹配，不是语义检索
- 分析和生成是规则模板，不是 LLM
- 缺 pyproject.toml 和 CI

**后续计划**：

- 接入 DeepSeek API → 提升分析和生成质量
- 接入 Embedding + Chroma → 语义检索
- 可选：迁移到 LangGraph

## 七、备用方案

如果现场环境出问题：

1. Streamlit 启动失败 → 切换到 CLI demo
2. 网络不通 → CLI demo 不需要网络
3. Python 版本问题 → 提前准备截图
4. 端口不通 → SSH 端口转发或本机演示
