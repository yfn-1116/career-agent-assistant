# Internship Copilot — Product Architecture

## 产品定位

**Evidence-grounded Job Hunting Agent / 基于证据约束的实习求职投递管家 Agent**

不是：
- 简历生成器
- 自动投递机器人
- GPT 包装壳
- 一次性 JD 分析工具

是：
- 长期个人资料库 → 自动检索真实经历
- 岗位发现与筛选 → 判断值得投的岗位
- 招聘意图分析 → 识别真实招聘 vs 泛招/引流
- 证据匹配 → 区分"实现了/设计了/计划中"
- 简历自动定制 → 按岗位生成不同侧重点的简历
- 沟通话术生成 → BOSS/邮件/微信
- 投递状态管理 → analyzed→applied→interview→offer
- HR 回复辅助 → 基于上下文的回复建议
- 面试准备辅导 → 项目讲解稿 + 模拟问题
- Human-in-the-loop → 所有发送动作必须用户确认

## 核心用户旅程

```
1. 资料准备
   上传简历/项目/GitHub/技能 → Profile Knowledge Base

2. 岗位发现
   复制 BOSS 岗位文本 → parse JobPosting

3. 岗位筛选
   candidate_match_score + hiring_intent_score → opportunity_score → 排序推荐

4. 沟通
   生成打招呼话术 + 验证问题 → 用户确认 → 复制/发送

5. 简历
   按岗位生成定制简历 → markdown/docx → 用户下载投递

6. 跟进
   保存 ApplicationRecord → 跟踪状态 → HR 回复 → 生成回复建议

7. 面试
   岗位JD + 简历 → 面试准备清单 + 项目讲解稿 + 模拟问题
```

## 模块架构

```
┌─────────────────────────────────────────────┐
│               Interface Layer                │
│         CLI / Streamlit / (API)              │
├─────────────────────────────────────────────┤
│          AgentRunService (唯一入口)           │
├─────────────────────────────────────────────┤
│  Profile │ JobSrc │ Opportunity │ Matching   │
│  Message │ Resume │ Application │ HR Reply   │
│  Interview│Approval│ Faithfulness │ Evidence  │
├─────────────────────────────────────────────┤
│  LangGraph StateGraph + ControlledPlanner    │
├─────────────────────────────────────────────┤
│  ToolRegistry (15 tools)                     │
├─────────────────────────────────────────────┤
│  RAG │ LLM │ Embedding │ Hybrid │ Reranker   │
│  Diagnostics │ Report │ Settings │ Docker     │
└─────────────────────────────────────────────┘
```

## Human-in-the-loop 原则

- 不自动发送消息
- 不自动投递简历
- 不绕过平台风控
- 不保存账号密码
- 不规避验证码
- 所有外部动作必须用户确认 (ApprovalGate)

## V1-V4 Roadmap

### V1：单岗位可用闭环 ✅ 当前

- 手动粘贴 JD → JobPosting
- candidate_match_score + hiring_intent_score
- can_write / cannot_write claims
- BOSS 打招呼话术
- 定制简历 markdown
- ApplicationRecord
- diagnostics + report
- Human approval gate

### V2：批量岗位筛选

- 多岗位文本解析
- 批量 scoring + ranking
- Top N 推荐 + skip 列表
- 一句话推荐原因

### V3：HR 回复 + 面试辅导

- HR 回复分类 + 建议生成
- 面试准备清单
- 项目讲解稿
- 模拟面试问题
- 自我介绍生成

### V4：浏览器辅助

- Chrome 插件 → 读取当前页面 DOM
- 本地 API 返回分析结果
- 用户确认复制话术
- 不自动登录/发送/爬取
