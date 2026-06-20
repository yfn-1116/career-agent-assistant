# 模型 Provider 抽象决策

## 1. 背景

第一阶段 MVP 的 Agent 全部使用规则和模板实现，不调用外部大模型。优点：

- 稳定可复现，每次输入输出一致
- 不依赖外部 API，不联网也能运行
- 测试不依赖网络，速度快

缺点：

- JD 解析只能匹配预定义关键词池，覆盖面有限
- 匹配分析的深度不够，无法理解技能的上下文相关性
- 生成输出的语言自然度远低于 LLM
- 无法利用大模型的推理能力做更复杂的多维度判断

## 2. 目标

在不破坏现有规则型链路的前提下，增加可选的 LLM Provider 能力，使 Agent 可以逐步接入真实模型，同时保证：

- 默认规则型仍可完整运行
- 测试使用 MockProvider，不依赖真实 API
- 真实 API 调用为可选增强

## 3. 设计原则

| 原则 | 说明 |
|---|---|
| 默认规则型可运行 | 不传 provider 或未配置 API Key 时，回退规则型 |
| 测试使用 MockProvider | 所有自动化测试不依赖外部网络 |
| 统一接口 | DeepSeek / OpenAI / 本地模型通过同一接口接入 |
| API Key 只从环境变量读取 | 不写入代码、不写入配置文件、不提交 |
| 不在 Agent 中写死模型调用 | 通过依赖注入传入 provider |
| 模型失败时 fallback | 网络异常、额度不足时降级到规则型 |

## 4. Provider 类型

### MockProvider

- 用于测试和默认无 API 环境
- 返回可预测文本
- 记录 last_prompt / last_system_prompt 供测试验证

### DeepSeekProvider

- 使用标准库 HTTP 调用，不引入第三方依赖
- 从环境变量读取 API Key / Base URL / Model
- 无 API Key 时，import 阶段不报错，仅在 generate 调用时给出清晰错误
- 支持 timeout

### 后续扩展

| Provider | 状态 |
|---|---|
| OpenAIProvider | 预留，与 DeepSeekProvider 类似 |
| LocalModelProvider | 预留，接 Ollama / vLLM 等本地模型 |

## 5. 第一阶段接入范围

| Agent | 是否接入 | 原因 |
|---|---|---|
| BuildAgent | **优先接入** | 对输出质量影响最大，prompt 约束最明确 |
| MatchAnalysisAgent | 暂保持规则型 | 规则型已可覆盖主要匹配维度 |
| JDParserAgent | 暂保持规则型 | 关键词匹配在当前规模够用 |
| RAGRetrieveAgent | 暂不接入 | 检索逻辑不涉及 LLM |

## 6. 风险与对策

| 风险 | 对策 |
|---|---|
| API 网络不可用 | try/except → fallback 规则型 |
| 输出幻觉 / 编造经历 | prompt 强约束，必须基于 evidence，明确禁编造 |
| API 调用成本 | 仅 BuildAgent 可选启用，默认规则型 |
| API Key 泄露 | 只读环境变量，不在代码/日志/输出中打印 |
| 响应时间过长 | 设置合理 timeout（默认 30s） |

## 7. Prompt 设计要求

LLM prompt 必须包含：

- 用户 evidence 摘要（title + content snippet）
- 岗位 JD 解析结果
- 匹配分析结果
- 明确约束：
  - **不得编造用户没有的经历**
  - **每条输出必须基于提供的 evidence**
  - **如果 evidence 不足以支撑某个结论，明确指出而非臆测**

## 8. 结论

本轮只做可选增强，不替代 MVP 主链路。核心代码路径保持规则型默认运行，LLM 为可选开关。后续可根据效果逐步扩大 LLM 接入范围。
