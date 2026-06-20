# Agent 输出评估

## 评估目标

检查 Agent 生成的输出是否完整、是否基于证据、是否可安全用于求职场景。

## 当前检查项

| 检查 | 规则 | 说明 |
|---|---|---|
| workflow_status | status=completed，无 error_message | workflow 是否成功运行 |
| generated_output_non_empty | summary / resume_bullets / communication_message 均非空 | 输出是否完整 |
| evidence_refs | evidence_refs 可关联到 retrieved_evidence | 输出是否有据可查 |

## 重要约束

- BuildAgent 明确要求**不得编造经历**
- 当 evidence 为空时，应输出保守提示而非编造项目
- 后续接入 LLM 时，prompt 必须包含防编造约束

## 人工检查要点

- 输出中的项目名称是否来自用户资料
- 技能描述是否与 evidence 一致
- 沟通话术是否自然、得体

## 后续增强方向

- LLM-as-judge：用 LLM 评估 LLM 输出的真实性
- 人工评分：对 resume_bullets 做 1-5 分可用性评分
