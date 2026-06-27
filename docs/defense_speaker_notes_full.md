# 答辩分工与手稿（含配图）

## 人员分工

| 谁 | 内容 | 时长 |
|---|---|---|
| **组员 C** | 开场 + Agent 四要素简介 | 2 分钟 |
| **组员 B** | Demo 演示 | 3 分钟 |
| **你（主讲）** | 架构 → Agent 树 → RAG | 5.5 分钟 |
| **组员 D** | 收尾 + 总结 | 1 分钟 |
| **你** | Q&A | 3-5 分钟 |

## 统一示例

> 整个答辩从头到尾使用**同一个例子**——Agent 开发实习生岗位（深圳，140-190 元/天）。
> JD 文本是用户粘贴进对话框的原始文本，简历是 PDF 格式上传的，GitHub 是链接丢给对话框的。
> Demo 展示"系统做了什么"，主讲人展示"系统怎么做的"。

---

## 组员 C：开场 + Agent 四要素（2 分钟）

### Slide 1 — 项目介绍

```
┌──────────────────────────────────────────────────┐
│                                                  │
│       Evidence-Constrained Agent                 │
│       基于证据约束的智能实习投递助手                │
│                                                  │
│   用户做什么：                                     │
│   📋 粘贴一段 JD 文本到对话框                      │
│   📄 上传 PDF 简历                                │
│   💻 丢一个 GitHub 仓库链接                        │
│                                                  │
│              ↓ 系统自动处理 ↓                      │
│                                                  │
│   系统输出什么：                                   │
│   ✅ 哪些项目跟这个岗位相关？匹配度多少？            │
│   ✅ 简历上这些项目应该怎么写？（分三档）            │
│   ✅ 每句话的证据来源是什么？                       │
│                                                  │
│   核心原则：所有输出必须基于证据，不得编造            │
│                                                  │
└──────────────────────────────────────────────────┘
```

**组员 C 说**："各位老师好。我们的项目解决一个很实际的问题——投实习的时候，粘贴一个 JD 到对话框，上传简历 PDF，丢一个 GitHub 链接。系统自动告诉你：你的哪些项目跟这个岗位相关、匹配度多少、简历上应该怎么写、每句话的证据来源是什么。核心原则：所有输出基于证据，不允许编造。下面由 XXX 演示实际效果——"

---

## 组员 B：Demo 演示（3 分钟）

### 准备（上台前 5 分钟确认）

```bash
cd ~/career-agent-assistant

# 1. 确认环境
PYTHONPATH=src python -c "from career_agent.workflows.job_match_workflow import JobMatchWorkflow; print('OK')"

# 2. 确认文件
ls data/samples/profile/resume.md data/samples/profile/projects.md data/samples/profile/github_repos.md
ls data/samples/jobs/real_agent_jd.txt

# 3. 提前跑一遍，保存输出备用
PYTHONPATH=src python demo/cli/run_job_match_demo.py \
  --profile-dir data/samples/profile \
  --job-file data/samples/jobs/real_agent_jd.txt \
  --output-file outputs/demo/live_demo.md 2>&1 | tail -3
```

---

### 第 1 幕：展示输入（45 秒）

> PPT: Slide 3

**操作**：
```bash
echo "=== 用户粘贴的 JD ===" && cat data/samples/jobs/real_agent_jd.txt
echo ""
echo "=== 用户的 PDF 简历 ===" && head -10 data/samples/profile/resume.md
echo ""
echo "=== 用户的 GitHub ===" && head -8 data/samples/profile/github_repos.md
```

**台词**（逐句念）：

"这是一个真实的投实习场景。假设一个学生叫陈小明，他在招聘网站上看到了这个岗位——"

"Agent 开发实习生，深圳，140 到 190 一天。要求负责 AI Agent 系统的开发，包括记忆模块、规划模块、工具调用模块。要开发基于大语言模型的智能体系统。要设计 Agent 的工具使用接口。要开发知识库管理系统。要求熟悉 Python 和 Java，熟悉 LLM 原理，了解机器学习。"

"他做了三件事——"

"第一，把这段 JD 粘贴到对话框里。纯文本，不是文件。"

"第二，上传了自己的 PDF 简历。陈小明，XX 大学化学专业，Python 三年，做过四个项目——包括一个 RAG 智能求职助手。"

"第三，丢了一个 GitHub 链接——github.com/yfn-1116/career-agent-assistant，就是他那个求职助手项目。"

"就这三件事。粘贴 JD、上传 PDF、丢链接。没有填表格，没有选标签，没有配置参数。"

"接下来 LLM 自己判断——这是一次岗位分析任务。它自动调 Agent 去处理。我们看系统输出了什么——"

---

### 第 2 幕：运行（15 秒）

> PPT: 仍然 Slide 3，终端显示命令

**操作**：
```bash
PYTHONPATH=src python demo/cli/run_job_match_demo.py \
  --profile-dir data/samples/profile \
  --job-file data/samples/jobs/real_agent_jd.txt \
  --output-file outputs/demo/live_demo.md
```

**台词**：

"运行。注意——这个命令不依赖任何外部 LLM API，纯本地规则模式，保证演示稳定。"

（等 5-10 秒，终端打印运行日志。不需要说话。）

---

### 第 3 幕：输出① — 哪些项目相关？（1 分钟）

> PPT: Slide 4

**操作**：
```bash
grep -A 50 "RAG\|检索\|Evidence\|证据\|score\|implemented\|SmartApply\|匹配\|Agent.*开发\|知识库\|工具调用" outputs/demo/live_demo.md | head -60
```

**台词**（逐句念，边指边讲）：

"输出第一部分——**哪些项目跟这个 JD 相关？**"

"系统从陈小明的所有经历里，找到了三条最相关的。"

"第一条，SmartApplyAgent——他的 RAG 智能求职助手。匹配度 0.89，状态 implemented，已实现。看它匹配了 JD 的哪些需求——Agent 系统开发，对应他基于 LangGraph 做的多 Agent 协作框架。工具调用模块，对应他实现的 task_agent 动态调度。知识库管理系统，对应他的 RAG Pipeline——BM25 加向量加重排序。对话系统，对应 Streamlit 交互界面。Python 全覆盖。**这个项目跟 JD 要求高度吻合。**"

"第二条，智能滴定系统。匹配度 0.62，implemented。匹配了 Python 和工程实践。虽然跟 AI 不直接相关，但能证明编程能力。"

"第三条，PolyU 智能导航。匹配度 0.55，状态是 designed——注意，不是 implemented，是 designed。这个项目只做了设计，没有完整实现。匹配了系统架构设计和 API 集成。"

"看底下的 JD 需求覆盖——Agent 系统开发✅、工具调用✅、知识库管理✅、对话系统✅、Python✅。Java 是⚠️——知识库里有提到但没实现经历。机器学习📋——完全没有对应证据。"

"关键点——**每条匹配都绑定了来源**。SmartApplyAgent 的匹配来自 github.com/yfn-1116/career-agent-assistant，不是模型编的。"

---

### 第 4 幕：输出② — 简历怎么写？（45 秒）

> PPT: Slide 5

**操作**：
```bash
grep -A 50 "简历\|bullet\|can_write\|needs_confirmation\|learning_plan\|建议\|✅\|⚠️\|📋\|implemented\|designed\|planned\|沟通\|话术\|HR\|message" outputs/demo/live_demo.md | head -60
```

**台词**（逐句念，边指边讲）：

"输出第二部分——也是最重要的——**简历怎么写？**"

"系统把简历建议分成三档。不是随便分的——**根据证据等级分。**"

"第一档，✅ 可以直接写的。SmartApplyAgent，证据等级 implemented。系统帮你写好了——'独立开发 AI Agent 智能求职助手，基于 LangGraph 实现多 Agent 协作框架。设计并实现工具调用模块，支持 Agent 动态调度与递归生成。构建 RAG 知识库管理系统。开发 Streamlit 对话交互界面。' 每句话都绑定了证据来源和等级。可以直接用。"

"第二档，⚠️ 需要确认的。PolyU 智能导航，证据等级 designed——只设计过，没完整实现。注意系统怎么写——'设计了基于 FastAPI 的后端架构'，用的是'设计'，不是'实现'。它不会帮你造假。标注了'需确认后写入'。"

"第三档，📋 建议补充的。JD 要求 Java，但知识库里没有 Java 的实现经历。JD 要求机器学习，也没有直接项目经验。系统不会编造'熟悉 Java 和机器学习'——它诚实告诉你'这个你还不够，建议去补'。"

"最后还有一段 HR 沟通话术，也是基于真实经历生成的。"

"核心能力一句话：**基于真实证据，告诉你能写什么、不能写什么、还需要补什么。**"

"接下来由 XXX 讲这个系统背后的技术是怎么实现的——"

---

### 备选方案

```bash
# 如果 CLI 运行失败，直接展示预先保存的输出
cat outputs/demo/agent_intern_jd_qwen_result.md | head -100

# 或者展示关键部分
echo "=== JD解析 ===" && grep -A 15 "job_title\|hard_skills\|Agent.*开发\|知识库\|工具调用" outputs/demo/agent_intern_jd_qwen_result.md
echo "=== 相关项目 ===" && grep -A 30 "SmartApplyAgent\|implemented\|证据\|匹配" outputs/demo/agent_intern_jd_qwen_result.md
echo "=== 简历怎么写 ===" && grep -A 20 "can_write\|needs_confirmation\|建议\|✅\|⚠️\|📋" outputs/demo/agent_intern_jd_qwen_result.md
```

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   📋 用户粘贴到对话框的 JD（纯文本，不是文件）：                │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Agent开发实习生 (140-190元/天)                        │    │
│  │ 工作地点：深圳                                        │    │
│  │ 实习要求：5天/周，最少3个月                            │    │
│  │                                                      │    │
│  │ 岗位职责：                                            │    │
│  │ · 负责 AI Agent 系统的开发和优化，                     │    │
│  │   包括记忆模块、规划模块和工具调用模块                  │    │
│  │ · 开发基于大语言模型的智能体系统                        │    │
│  │ · 设计 Agent 的工具使用接口                            │    │
│  │ · 开发 Agent 的知识库管理系统                          │    │
│  │                                                      │    │
│  │ 任职要求：                                            │    │
│  │ · 熟悉 Python、Java，有良好工程实践                   │    │
│  │ · 熟悉大语言模型（LLM）原理和应用                      │    │
│  │ · 了解机器学习、深度学习等 AI 技术                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│   📄 用户上传的 PDF 简历：陈小明的个人简历                    │
│   💻 用户丢的 GitHub 链接：github.com/yfn-1116/              │
│       career-agent-assistant                                │
│                                                             │
│   用户就做了这三件事——粘贴 JD、上传 PDF、丢链接。              │
│   系统怎么处理的？                                           │
└─────────────────────────────────────────────────────────────┘
```

**操作**：
```bash
echo "=== 用户粘贴的 JD ===" && cat data/samples/jobs/real_agent_jd.txt
echo ""
echo "=== 用户的简历 ===" && head -8 data/samples/profile/resume.md
echo ""
echo "=== 用户的 GitHub ===" && head -6 data/samples/profile/github_repos.md
```

**组员 B 说**："这就是一个真实的投实习场景。用户粘贴了一段 JD——Agent 开发实习生，深圳，要求 Python/Java，熟悉 LLM 和 Agent 开发，负责记忆模块、规划模块、工具调用模块。同时上传了自己的 PDF 简历，丢了一个 GitHub 链接。用户就做了这三件事。

系统收到这三样东西之后——LLM 自己判断意图：这是一次岗位分析任务。然后它自动调 Agent 去处理。接下来我们看系统输出了什么——"

---

### 第 2 幕：运行（15 秒）

```bash
PYTHONPATH=src python demo/cli/run_job_match_demo.py \
  --profile-dir data/samples/profile \
  --job-file data/samples/jobs/real_agent_jd.txt \
  --output-file outputs/demo/live_demo.md
```

**组员 B 说**："运行。注意——这里没有写死任何流程。JD 文本丢进去，系统自己解析、自己检索、自己匹配、自己生成。"

---

### 第 3 幕：输出① — 哪些项目相关？（1 分钟）

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  🔍 系统从你的经历中找到了跟这个 JD 最相关的项目：              │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ ✅ SmartApplyAgent — RAG 智能求职助手                 │    │
│  │    匹配度: 0.89 | 状态: implemented (已实现)           │    │
│  │    匹配 JD 需求:                                      │    │
│  │    · Agent 系统开发 ← 基于 LangGraph 多 Agent 协作     │    │
│  │    · 工具调用模块 ← task_agent 实现 Tool 动态调度      │    │
│  │    · 知识库管理 ← RAG Pipeline (BM25+向量+重排)       │    │
│  │    · 对话系统 ← Streamlit 交互界面                    │    │
│  │    · Python ← 全部代码 Python 实现                    │    │
│  │    来源: github.com/yfn-1116/career-agent-assistant  │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │ ✅ 智能滴定系统 — 视觉滴定终点检测                     │    │
│  │    匹配度: 0.62 | 状态: implemented                   │    │
│  │    匹配 JD 需求: Python, 工程实践, 系统设计能力         │    │
│  │    来源: github.com/yfn-1116/auto-titration-system    │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │ ⚠️ PolyU 智能导航 — 校园路径规划                      │    │
│  │    匹配度: 0.55 | 状态: designed (仅设计, 未完整实现)   │    │
│  │    匹配 JD 需求: 系统架构设计, API 集成                │    │
│  │    来源: github.com/yfn-1116/polyu-smart-journey     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  JD 核心需求覆盖情况：                                        │
│  ✅ Agent系统开发  ✅ 工具调用  ✅ 知识库管理                  │
│  ✅ 对话系统  ✅ Python  ⚠️ Java  📋 机器学习/深度学习        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**操作**：
```bash
grep -A 50 "RAG\|检索\|Evidence\|证据\|score\|implemented\|SmartApply\|匹配" outputs/demo/live_demo.md | head -60
```

**组员 B 说**："系统找到了最相关的项目。最匹配的是 SmartApplyAgent——这个项目本身就是 Agent 系统，覆盖了 JD 要求的 Agent 开发、工具调用、知识库管理、对话系统，全部 Python 实现，证据等级 implemented。每一项匹配都映射到 JD 的具体需求。

注意第二项和第三项的区别——智能滴定是 implemented，可以写；PolyU 导航是 designed，只能写'设计过'。**系统不会把'设计过'的东西写成'实现了'。**"

---

### 第 4 幕：输出② — 简历怎么写？（45 秒）

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ✏️ 系统根据证据等级，分三档告诉你简历怎么写：                  │
│                                                             │
│  ✅ 可以直接写进简历的（implemented 证据）：                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ "独立开发 AI Agent 智能求职助手，基于 LangGraph 实现    │    │
│  │  多 Agent 协作框架。设计并实现工具调用模块(task_agent)  │    │
│  │  支持 Agent 动态调度与递归生成。构建 RAG 知识库管理     │    │
│  │  系统(BM25+向量+重排序)，实现高效信息存储与检索。       │    │
│  │  开发 Streamlit 对话交互界面。"                        │    │
│  │  [证据来源: github.com/yfn-1116/career-agent-assistant]│   │
│  │  [证据等级: implemented — 已实现，可直接写入简历]       │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ⚠️ 需要确认后才能写的（designed 证据）：                      │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ "设计基于 FastAPI + PostgreSQL 的校园导航后端，        │    │
│  │  实现 RESTful API 与外部地图服务集成"                  │    │
│  │  [证据等级: designed — 仅设计阶段，需确认后决定是否写入] │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  📋 建议补充实践后再写的（无证据）：                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Java — 知识库中无相关实现经历，建议补充实践            │    │
│  │ 机器学习/深度学习 — 无直接项目经验，建议补充 Demo       │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  💬 生成的 HR 沟通话术：                                      │
│  "您好，看到贵司 Agent 开发实习岗位。我有 LangGraph 多 Agent  │
│   协作和 RAG 知识库管理系统的项目经验，独立开发过完整 Agent    │
│   系统，涵盖工具调用、对话交互、知识检索等模块..."              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**操作**：
```bash
grep -A 40 "简历\|bullet\|can_write\|needs_confirmation\|learning_plan\|建议\|✅\|⚠️\|📋" outputs/demo/live_demo.md | head -50
```

**组员 B 说**："最关键的输出——简历怎么写。系统分三档。

✅ 可以写的——SmartApplyAgent 覆盖了 JD 的 Agent 开发、工具调用、知识库管理、对话系统。每条描述绑定了证据来源和等级。

⚠️ 需要确认的——PolyU 导航仅设计阶段，系统不会写'实现了xxx'，写的是'设计了xxx'，并标注需要确认。

📋 建议补充的——JD 要求的 Java 和机器学习，用户知识库里没有相关实现经历。系统不会编造，而是诚实告诉用户：'这个你还不够，建议去补'。

**核心能力一句话：基于真实证据，告诉你能写什么、不能写什么、还需要补什么。**

接下来由 XXX 讲这个系统背后的技术实现——"

---

### 备选方案

```bash
# CLI 失败 → 展示预先保存的输出
cat outputs/demo/agent_intern_jd_qwen_result.md | head -100
```

---

## 组员 C（继续）：Agent 四要素（1 分钟）

### Slide 3

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│                   Agent 系统的四个要素                     │
│                                                          │
│  刚刚的 Demo 背后，是这个四层架构在运转：                   │
│                                                          │
│  ┌──────────────┐   ┌──────────────┐                     │
│  │  Perception  │   │   Planning   │                     │
│  │    感知       │──→│    规划       │                     │
│  ├──────────────┤   ├──────────────┤                     │
│  │ 理解用户输入   │   │ 决定做什么    │                     │
│  │ ·JD 文本 →    │   │ ·LLM 识别意图│                     │
│  │  结构化技能   │   │ ·决定调哪个   │                     │
│  │ ·PDF → 文本   │   │  Agent       │                     │
│  │ ·GitHub链接→  │   │ ·决定并行/串行│                     │
│  │  仓库内容     │   │              │                     │
│  └──────┬───────┘   └──────┬───────┘                     │
│         │                  │                             │
│         └────────┬─────────┘                             │
│                  │                                       │
│  ┌───────────────┴───────────────┐                       │
│  │          Memory 记忆           │                       │
│  │  记住一切 · 短期/长期/知识库    │                       │
│  └───────────────┬───────────────┘                       │
│                  │                                       │
│  ┌───────────────┴───────────────┐                       │
│  │         Action 执行            │                       │
│  │  RAG检索 · 匹配分析 · 证据校验  │                       │
│  └───────────────────────────────┘                       │
│                                                          │
│  接下来由 XXX 深入讲架构是怎么设计的——                      │
└──────────────────────────────────────────────────────────┘
```

**组员 C 说**："刚才 Demo 看到了系统做什么。这背后是一个 Agent 系统的四个要素在协作。Perception 感知——理解用户粘贴的 JD、上传的 PDF、丢的 GitHub 链接。Planning 规划——LLM 判断意图、决定调哪个 Agent。Action 执行——RAG 检索、匹配分析、生成输出。Memory 记忆——存储对话、知识库索引。接下来由 XXX 讲具体架构——"

---

## 你（主讲）：架构 → Agent 树 → RAG（5.5 分钟）

---

### ① 总体架构（1.5 分钟）

### Slide 4

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│   用户操作: 粘贴 JD ──→ 上传 PDF ──→ 丢 GitHub 链接          │
│                     │                                      │
│                     ▼                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         调度层：OrchestratorAgent                      │  │
│  │                                                      │  │
│  │   LLM 收到消息 → 识别意图 → 决定调用顺序               │  │
│  │                                                      │  │
│  │   "用户发了 JD + PDF + GitHub → 这是岗位分析任务        │  │
│  │    → 先解析 JD, 同时索引 PDF 和 GitHub                  │  │
│  │    → 再检索知识库 → 再匹配分析 → 最后生成输出"          │  │
│  │                                                      │  │
│  │   不是写死的 if-else，是 LLM 自己做的决策               │  │
│  └────────────────────────┬─────────────────────────────┘  │
│                           │                                │
│                           ▼                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         能力层：16 个 Tool → 形成执行链                 │  │
│  │                                                      │  │
│  │   parse_jd ──→ retrieve_profile ──→ analyze_match     │  │
│  │   解析 JD        检索知识库           匹配分析           │  │
│  │                                                      │  │
│  │   ──→ generate_answer ──→ check_faithfulness         │  │
│  │        生成简历要点         证据校验                    │  │
│  │                                                      │  │
│  │   实现方式: Skill(Python) + MCP(GitHub) + SubAgent    │  │
│  └────────────────────────┬─────────────────────────────┘  │
│                           │                                │
│                           ▼                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         基础设施 + 存储                                │  │
│  │   LLM(Qwen/DeepSeek) · Embedding(1024维)              │  │
│  │   RAG Pipeline · Memory 三层                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  关键设计：LLM 不是只调一个 Tool——它生成子 Agent 去干活      │
│  接下来展开这个——                                          │
└────────────────────────────────────────────────────────────┘
```

**你说**："刚才 Demo 里用户粘贴了 JD、上传了 PDF、丢了 GitHub 链接。这三样东西到了系统里，谁接住的？OrchestratorAgent。

LLM 收到消息后自己判断——这是岗位分析任务。它决定：先解析 JD 提取技能，同时把 PDF 和 GitHub 索引进知识库；然后检索匹配；最后生成输出。**这个顺序不是写死的 if-else，是 LLM 自己做的决策。**

但 LLM 不自己干活——它生成子 Agent 去干。这是整个系统最核心的设计——"

---

### ② 核心：Agent → SubAgent（2.5 分钟）⭐

### Slide 5 — 主 Agent 怎么分派任务

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│   用户粘贴 JD + PDF + GitHub 链接                              │
│            │                                                 │
│            ▼                                                 │
│   ┌────────────────────────────────────────────────────┐     │
│   │         🧠 OrchestratorAgent (主 Agent)             │     │
│   │                                                    │     │
│   │   LLM 决策循环:                                     │     │
│   │                                                    │     │
│   │   Step 1: LLM 判断 → "需要解析 JD, 同时索引知识库"    │     │
│   │     → 调 task_agent("解析JD+索引PDF和GitHub",       │     │
│   │                      [parse_jd, web_search])       │     │
│   │     → 生成 SubAgent-1                              │     │
│   │                                                    │     │
│   │   Step 2: LLM 判断 → "需要检索匹配的经历"             │     │
│   │     → 调 task_agent("检索Agent开发相关经历",         │     │
│   │                      [retrieve_profile,            │     │
│   │                       github_repo])                │     │
│   │     → 生成 SubAgent-2  (与 SubAgent-1 并行!)        │     │
│   │                                                    │     │
│   │   Step 3: LLM 判断 → "需要分析匹配度"                │     │
│   │     → 调 task_agent("分析JD和证据的匹配度",          │     │
│   │                      [analyze_match,               │     │
│   │                       grade_retrieval])            │     │
│   │     → 生成 SubAgent-3  (依赖 Step 2 结果, 串行)     │     │
│   │                                                    │     │
│   │   Step 4: LLM 判断 → "可以输出最终答案了"             │     │
│   │     → 调 task_agent("生成简历建议",                 │     │
│   │                      [generate_answer,             │     │
│   │                       check_faithfulness,          │     │
│   │                       write_report])               │     │
│   │     → 生成 SubAgent-4                              │     │
│   │                                                    │     │
│   │   Step 5: LLM 判断 → "所有任务完成, 回复用户"         │     │
│   └────────────────────────────────────────────────────┘     │
│                                                              │
│   主 Agent 不干活，只做决策。干活的是子 Agent。                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Slide 6 — 子 Agent 怎么执行、怎么回传

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  以 SubAgent-1（感知·解析专家）为例，看子 Agent 怎么干活：       │
│                                                              │
│   ┌────────────────────────────────────────────────────┐     │
│   │  主 Agent 调用 task_agent:                          │     │
│   │                                                    │     │
│   │  task = "解析这段 JD，提取技能要求。                   │     │
│   │          同时索引 PDF 简历和 GitHub 仓库到知识库。"    │     │
│   │  allowed_tools = [parse_jd, web_search]            │     │
│   └────────────────────┬───────────────────────────────┘     │
│                        │                                     │
│                        ▼                                     │
│   ┌────────────────────────────────────────────────────┐     │
│   │  SubAgent-1 实例被创建:                              │     │
│   │                                                    │     │
│   │  System Prompt: "你是信息采集专家，                  │     │
│   │   解析所有输入并索引到知识库。"                        │     │
│   │                                                    │     │
│   │  独立上下文 (Session) — 不影响其他 Agent              │     │
│   │                                                    │     │
│   │  自己调 parse_jd(JD文本):                           │     │
│   │    → { job_title: "Agent开发实习生",                │     │
│   │        hard_skills: [Python, Java, LLM, Agent,     │     │
│   │          工具调用, 知识库管理, 对话系统...],          │     │
│   │        job_direction: "agent" }                    │     │
│   │                                                    │     │
│   │  自己调 FileLoader: PDF → pypdf 提取文本             │     │
│   │  自己调 TextChunker: 分块 → 写入 chunks.jsonl       │     │
│   │                                                    │     │
│   │  完成任务 → 返回 SubAgentResult {                   │     │
│   │    answer: "JD已解析, PDF已索引为3个chunk",         │     │
│   │    tools_called: ["parse_jd", "web_search"]        │     │
│   │  }                                                │     │
│   └────────────────────┬───────────────────────────────┘     │
│                        │                                     │
│                        ▼                                     │
│   ┌────────────────────────────────────────────────────┐     │
│   │  主 Agent 收到 SubAgentResult → 继续决策下一步        │     │
│   └────────────────────────────────────────────────────┘     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Slide 7 — 四个子 Agent 全貌

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│   四个子 Agent — 角色不同、权限不同、上下文独立                  │
│                                                              │
│   SubAgent-1          SubAgent-2          SubAgent-3         │
│   📄 感知·解析        🔍 检索·知识        ⚖️ 分析·匹配       │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│   │ Role:       │    │ Role:       │    │ Role:       │      │
│   │ 信息采集专家│    │ 知识检索专家│    │ 匹配分析专家│      │
│   ├─────────────┤    ├─────────────┤    ├─────────────┤      │
│   │ Permissions:│    │ Permissions:│    │ Permissions:│      │
│   │ parse_jd    │    │ retrieve_   │    │ analyze_    │      │
│   │ web_search  │    │ profile     │    │ match       │      │
│   │             │    │ github_repo │    │ grade_      │      │
│   │             │    │             │    │ retrieval   │      │
│   ├─────────────┤    ├─────────────┤    ├─────────────┤      │
│   │ Session:    │    │ Session:    │    │ Session:    │      │
│   │ 独立上下文  │    │ 独立上下文  │    │ 独立上下文  │      │
│   ├─────────────┤    ├─────────────┤    ├─────────────┤      │
│   │ 做什么:     │    │ 做什么:     │    │ 做什么:     │      │
│   │ JD→结构化   │    │ 查知识库    │    │ JD vs 证据  │      │
│   │ PDF→文本    │    │ 找相关经历  │    │ 逐条比对    │      │
│   │ 写入索引    │    │ 评估质量    │    │ 算匹配度    │      │
│   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘      │
│          │                  │                  │              │
│          └─── ⚡ 并行 ──────┘        🔗 串行 ──┘              │
│          (无依赖,同时跑)      (SubAgent-3 等 SubAgent-2)      │
│                                                              │
│   SubAgent-4                     SubAgent-3-1 (递归!)        │
│   ✏️ 生成·输出                   ✅ 证据校验                  │
│   ┌─────────────┐              ┌─────────────┐              │
│   │ 基于证据生成│              │ SubAgent-3   │              │
│   │ 简历要点    │              │ 分析时发现    │              │
│   │ 三档分类    │              │ 需要校验证据  │              │
│   │ HR 话术     │              │ → 生成孙Agent│              │
│   │ 诊断报告    │              │ check_       │              │
│   └─────────────┘              │ faithfulness │              │
│                                └─────────────┘              │
│                                                              │
│   本质: Role(角色) × Permissions(权限) × Session(上下文)      │
│         三维解耦，每个子 Agent 独立可控                        │
│                                                              │
│   代码: orchestrator.py:70 · autonomous_agent.py:56          │
│         sub_agent.py:39 · registry.py:488                   │
└──────────────────────────────────────────────────────────────┘
```

**你说**（Slide 5-7 连续讲）：

"这是整个系统最核心的设计——Agent 递归树。回到刚才 Demo 那个例子。用户粘贴了 JD、上传了 PDF、丢了 GitHub 链接。OrchestratorAgent 的 LLM 收到这三样东西，开始决策——"

*（切换到 Slide 5）*

"Step 1：LLM 判断'需要解析 JD 并索引知识库'。它不直接调 parse_jd——而是调 task_agent 这个 Tool，传两个参数：task 字符串描述任务，allowed_tools 白名单控制权限。task_agent 创建一个新的 SubAgent 实例——SubAgent-1。

Step 2：LLM 判断'需要检索匹配的经历'。生成 SubAgent-2。注意——**SubAgent-1 和 SubAgent-2 没有数据依赖，并行执行。** JD 解析和知识库检索可以同时跑。

Step 3：LLM 拿到 SubAgent-2 的检索结果后，生成 SubAgent-3 做匹配分析。这一步**必须等 SubAgent-2 的结果——串行。**

Step 4：SubAgent-4 生成最终输出。Step 5：LLM 判断任务完成，回复用户。"

*（切换到 Slide 6）*

"看一个子 Agent 内部怎么干活的。以 SubAgent-1 为例——

主 Agent 调 task_agent，传入 task='解析 JD 并索引 PDF 和 GitHub'，tools=[parse_jd, web_search]。

task_agent 创建一个**独立 Agent 实例**——有自己的 System Prompt（'你是信息采集专家'）、自己的上下文窗口（不和主 Agent 或其他子 Agent 共享）、自己的步数限制。

SubAgent-1 开始干活——调 parse_jd 解析那段 JD 文本，提取出 Python、Java、LLM、Agent、工具调用、知识库管理这些技能。调 FileLoader 读 PDF 简历。调 TextChunker 分块写入知识库。

干完了，返回 SubAgentResult——包含 answer（'JD 已解析，PDF 已索引为 3 个 chunk'）和 tools_called 列表。

主 Agent 拿到这个结果，继续决策下一步。"

*（切换到 Slide 7）*

"四个子 Agent 全貌。看每列的三个字段——

**Role（角色）**：通过 System Prompt 定义。SubAgent-1 是'信息采集专家'，SubAgent-2 是'知识检索专家'。不同角色，不同 Prompt。

**Permissions（权限）**：通过 allowed_tools 白名单控制。SubAgent-1 只能调 parse_jd 和 web_search——它不能改知识库、不能生成简历。SubAgent-4 可以 generate_answer，但不能解析 JD。权限隔离，安全边界。

**Session（上下文）**：每个子 Agent 独立实例，上下文互不污染。

**并行 vs 串行**：SubAgent-1 和 SubAgent-2 没有数据依赖——LLM 在同一步生成它们，并行执行。SubAgent-3 依赖 SubAgent-2 的结果，必须等。SubAgent-4 依赖 SubAgent-3。

**递归**：SubAgent-3 分析匹配时，发现需要仔细校验证据——它再调 task_agent，生成 SubAgent-3-1，一个只做 check_faithfulness 的孙 Agent。Agent 可以生成 Agent，生成的还能再生成。终止条件是 max_steps 硬限制。

本质一句话：**Role × Permissions × Session 三维解耦。**"

---

### ③ RAG 写入 + 检索（1.5 分钟）⭐

### Slide 8

```
┌──────────────────────────────────────────────────────────────┐
│          RAG — 知识库的数据怎么进去、怎么查出来                  │
│                                                              │
│  ┌─────────────────────┐    ┌─────────────────────────────┐  │
│  │  写入 (Perception→   │    │  读取 (Memory→Action)        │  │
│  │       Memory)        │    │                             │  │
│  │                      │    │  查询词:                     │  │
│  │  PDF 简历 ──→        │    │  "Python Agent LLM          │  │
│  │  pypdf 提取文本 ──→  │    │   工具调用 知识库管理"       │  │
│  │  TextChunker 分块    │    │         │                   │  │
│  │  (800字/块) ──→      │    │         ▼                   │  │
│  │  写入 chunks.jsonl   │    │  ① jieba 分词               │  │
│  │                      │    │         │                   │  │
│  │  GitHub 链接 ──→     │    │         ▼                   │  │
│  │  MCP(JSON-RPC)       │    │  ② 双路并行粗召回(各top80)  │  │
│  │  → npx 子进程读README│    │  ┌──────────┐ ┌──────────┐  │  │
│  │  → 失败: urllib GET  │    │  │ BM25     │ │ Embedding│  │  │
│  │  → 同上分块流程      │    │  │ 关键词   │⊕│ 语义     │  │  │
│  │                      │    │  └──────────┘ └──────────┘  │  │
│  └─────────────────────┘    │         │                   │  │
│                              │         ▼                   │  │
│                              │  ③ RRF融合(k=60,→top30)    │  │
│                              │    只关心排序,不关心分数     │  │
│                              │         │                   │  │
│                              │         ▼                   │  │
│                              │  ④ CrossEncoder精排(→top5) │  │
│                              │    bge-reranker-base 279M  │  │
│                              │         │                   │  │
│                              │         ▼                   │  │
│                              │  ⑤ Faithfulness (阈值0.75) │  │
│                              │  ⑥ EvidenceGate 四级约束    │  │
│                              │    ✅可写 ⚠️确认 ❌禁止      │  │
│                              └─────────────────────────────┘  │
│                                                              │
│  ⚡ API 不可用 → 轻量回退: BM25+规则, <50ms, 零网络            │
│  代码: hybrid_retriever.py · rrf_fusion.py · gate.py:46      │
└──────────────────────────────────────────────────────────────┘
```

**你说**："Agent 树解决了谁干什么。干活的依据——知识库——怎么来的、怎么查的？

**写入**简单。PDF 简历→pypdf 提取文本→TextChunker 800 字滑动窗口分块→追加 chunks.jsonl。GitHub 链接→MCP 协议调 npx 子进程读 README→失败就 urllib 直接 GET→同上分块流程。

**读取**是重点。SubAgent-2 拿到 JD 的技能列表——Python、LLM、Agent、工具调用、知识库管理——构造查询。六步。

第一步 jieba 分词。第二步**双路并行粗召回**——BM25 关键词检索（快、准、不懂语义）+ Qwen Embedding 语义检索（1024 维，懂同义词但可能捞不相关文档），两路互补，各取 80。

第三步**RRF 融合**。两路分数不在一个尺度——BM25 的分数和向量距离没法直接比较。Reciprocal Rank Fusion：只关心排序位置，k=60，零参数。

第四步**CrossEncoder 精排**，bge-reranker-base 279M，query+chunk 拼一起过 Transformer，比向量检索精细——但计算量大，只能对 top 30 做。精排到 top 5。

第五步 FaithfulnessChecker，检测生成内容是否超出证据范围。第六步 EvidenceGate——implemented 可写'实现了'，designed 只能写'设计了'，planned 禁止写入。Demo 里那三档分类就是这么来的。

API 挂了？轻量回退——BM25 + 五维规则打分，小于 50ms，零网络依赖。"

---

## 组员 D：收尾（1 分钟）

### Slide 9

```
┌──────────────────────────────────────────────┐
│                                              │
│         回顾三个核心设计                        │
│                                              │
│   ┌─────────────────────────────────────┐    │
│   │ Agent 递归树                         │    │
│   │ 主 Agent 决策 → 子 Agent 执行         │    │
│   │ Role × Permissions × Session 三维解耦│    │
│   │ 并行 + 串行 + 递归                    │    │
│   └─────────────────────────────────────┘    │
│   ┌─────────────────────────────────────┐    │
│   │ RAG 全链路                           │    │
│   │ 写入: PDF/GitHub → 分块 → 索引       │    │
│   │ 读取: BM25+Embedding→RRF→精排→校验   │    │
│   │ API 不可用时自动降级                  │    │
│   └─────────────────────────────────────┘    │
│   ┌─────────────────────────────────────┐    │
│   │ EvidenceGate 证据约束                 │    │
│   │ implemented → ✅ 可写                 │    │
│   │ designed → ⚠️ 需确认                 │    │
│   │ planned → ❌ 禁止                     │    │
│   └─────────────────────────────────────┘    │
│                                              │
│   三个局限:                                   │
│   语义检索依赖外部API · 并发未验证 · 数据有限   │
│                                              │
└──────────────────────────────────────────────┘
```

**组员 D 说**："三个核心设计——Agent 递归树让任务分拆和并行成为可能，RAG 全链路保证检索质量，EvidenceGate 约束输出不编造。三个局限诚实交代。欢迎各位老师提问。"

---

### Slide 10 — 结尾

```
┌──────────────────────────────────────────────┐
│                                              │
│           感谢各位老师                         │
│                                              │
│      Evidence-Constrained Agent              │
│      基于证据约束的智能实习投递助手             │
│                                              │
│           欢迎提问 🙋                         │
│                                              │
└──────────────────────────────────────────────┘
```

---

## 你：Q&A

| 问题 | 答 |
|------|-----|
| Agent 和普通程序有什么区别？ | 普通程序写死 if-else；Agent 是 LLM 自己决定调用顺序，不是预设流程 |
| 主 Agent 怎么知道该生成哪些子 Agent？ | LLM 看到 16 个 Tool 的描述，根据任务自己判断；System Prompt 引导但不强制 |
| 子 Agent 之间怎么通信？ | 不直接通信。主 Agent 中转：SubAgent → SubAgentResult → 主 Agent → 下一个 SubAgent 的 task 输入 |
| 为什么不让一个 Agent 干所有事？ | 上下文爆炸 + 权限无法隔离 + 无法并行 |
| 递归会不会无限套娃？ | max_steps 硬限制：主 Agent 10 步，子 Agent 8 步 |
| RAG 为什么分两路？ | BM25 保准确（懂关键词但不懂语义），Embedding 保召回（懂语义但可能捞无关文档），互补 |
| RRF 为什么不用直接加权？ | 两路分数不在一个尺度，直接加权不公平；RRF 只关心排序位置，零参数 |
| EvidenceGate 的 status 谁标的？ | ProfileLoader 自动推断——代码检测'实现了/完成了'→implemented，'设计了/规划了'→designed |
| 和 ChatGPT 投简历有什么区别？ | ChatGPT 没证据约束，会编造；我们每句话绑定证据来源和等级 |
| LLM 挂了怎么办？ | 自主模式→规则回退；Provider→Mock 兜底；RAG 轻量模式零网络 |


## PPT 配图清单

| Slide | 内容 | 谁负责 |
|---|---|---|
| 1 | 项目介绍（输入→输出） | 组员 C |
| 2 | Demo：输入展示 + 运行 + 哪些项目相关 + 怎么写 | 组员 B |
| 3 | Agent 四要素 PPAM 图 | 组员 C |
| 4 | 总体架构（调度→能力→基础设施） | **你** |
| 5 | 主 Agent 决策过程（Step 1-5） | **你** |
| 6 | 子 Agent 执行与回传（以 SubAgent-1 为例） | **你** |
| 7 | 四个子 Agent 全貌（Role×Permissions×Session） | **你** |
| 8 | RAG 写入 + 读取六步 | **你** |
| 9 | 回顾总结 + 局限 | 组员 D |
| 10 | 结尾感谢 | 组员 D |
