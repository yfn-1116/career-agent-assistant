# Demo 脚本

## 用途

本文档记录第一阶段 CLI demo 展示时的讲解脚本和操作顺序。

## 展示脚本（约 10 分钟）

### 1. 项目背景（1 分钟）

> 找实习时，对着 10 份 JD，需要反复翻自己的项目文档回忆哪些经历能对上——效率很低。这个工具把你的经历写成结构化 Markdown 文档，然后用 RAG 检索 + Agent 匹配分析来做 JD 匹配。

### 2. 展示样例用户资料（1 分钟）

```bash
cat data/samples/profile/resume.md
```

讲解要点：
- 这是脱敏虚构的用户资料
- 包含技能、项目、实习、GitHub 仓库等结构化信息
- 所有内容用中文 Markdown 组织

### 3. 展示样例岗位 JD（1 分钟）

```bash
cat data/samples/jobs/agent_intern_jd.md
```

讲解要点：
- AI Agent 开发实习生岗位
- 包含岗位职责、任职要求、加分项

### 4. 运行 CLI demo（30 秒）

```bash
PYTHONPATH=src python demo/cli/run_job_match_demo.py
```

终端输出：

```text
任务状态：completed
岗位方向：agent
检索证据：5 条
输出文件：outputs/demo/job_match_result.md
Done.
```

### 5. 打开输出 Markdown（5 分钟）

```bash
cat outputs/demo/job_match_result.md
```

逐段讲解：

#### JD 解析结果（1 分钟）

> 系统用规则从 JD 文本中提取了岗位标题、方向、硬技能、加分技能、软技能和关键词。当前用规则匹配，后续可接入 LLM 做更精细的解析。

#### RAG 检索证据（1.5 分钟）

> 基于 JD 中的技能关键词，在用户资料知识库中检索最相关的经历片段。每条证据包含来源文件、相关性评分、匹配关键词和原文引用。

#### 匹配分析（1 分钟）

> 对比 JD 要求和检索到的用户证据，生成 strengths（哪些 JD 要求有证据支撑）、weaknesses（哪些 JD 要求知识库中没有对应证据）、推荐突出的项目、改进建议。

#### 生成输出（1 分钟）

> 基于检索证据生成简历 bullet（每条可追溯到来源）、简短的沟通话术（适合联系 HR/mentor）、总结。**关键：不编造用户没有的经历。**

#### 运行说明（30 秒）

> 当前使用本地规则和内存关键词检索，不调用外部大模型，保证每次运行结果一致可复现。

### 6. 总结（1 分钟）

> 第一阶段完成了完整的 RAG + Agent + Workflow + CLI demo 闭环。后续将接入 DeepSeek API 提升匹配质量，并用 Streamlit 做可视化展示。

## 备用 JD

如果主 JD 运行结果不够丰富，可切换到 RAG 工程 JD：

```bash
PYTHONPATH=src python demo/cli/run_job_match_demo.py \
  --job-file data/samples/jobs/rag_engineer_intern_jd.md \
  --output-file outputs/demo/rag_engineer_result.md
```

## 注意事项

1. 确保 `PYTHONPATH=src` 已设置
2. 确保在项目根目录下运行
3. 展示前先运行一次确认输出正常
4. 如果终端不支持中文，可预先准备英文版输出
