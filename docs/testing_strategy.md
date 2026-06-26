# 测试策略

## 三层测试金字塔

```
                    ┌─────────────┐
                    │  Scenario   │  ← 业务场景评估（真实 JD 匹配、分数校准）
                    │   Evals     │
                    ├─────────────┤
                    │    E2E      │  ← 端到端链路（JD→输出 完整流程）
                    ├─────────────┤
                    │ Unit Tests  │  ← 单元测试（函数、Schema、Gate 规则）
                    └─────────────┘
```

---

## 第一层：单元测试（Unit Tests）

**位置：** `tests/{agents,rag,domain,matching,evaluation,evidence,...}/`

**覆盖范围：**
- Schema 创建和 roundtrip（`to_dict` / `from_dict`）
- Score validation（拒绝 bool / NaN / inf / 越界值）
- Evidence Gate 规则（4 种 status 的措辞限制）
- Faithfulness Checker 单 bullet 评分
- RAG 管道（chunking / retrieval / reranker / grading）
- 模型 Provider 接口和 Mock
- Tool Registry 注册和调用

**断言策略：** 精确值断言
- `assert result.score == 0.85`
- `with pytest.raises(ValueError, match="...")`
- `assert result.matched_keywords == ["Python", "RAG"]`

**Mock 策略：**
- `MockProvider(fixed_response=...)` — 模拟 LLM
- `tempfile.TemporaryDirectory()` — 沙盒文件 I/O
- `monkeypatch.setattr(...)` — 替换工作流函数

**运行命令：**
```bash
pytest tests/ --ignore=tests/evals --ignore=tests/e2e -q
```

**当前覆盖：** 554 个测试，全部通过，耗时约 2 分钟

---

## 第二层：评估测试（Evaluation Tests / "Evals"）

**位置：** `tests/evals/`

**目的：** 验证 AI 系统在真实业务场景下的行为正确性，不测试底层实现细节。

### 2a. JD 匹配方向测试（`test_realistic_jd_matching.py`）

验证不同 JD 类型能正确匹配到对应的 evidence：

| 测试类 | 验证内容 | 断言方式 |
|---|---|---|
| `TestAgentJDMatching` | Agent JD 匹配到 agent/RAG 技能 | 技能集合重叠 ≥2 |
| `TestCVJDMatching` | CV JD 匹配到 CV/ML 技能，不匹配前端技能 | 集合重叠 + 排除检查 |
| `TestBackendJDMatching` | 后端 JD 匹配到 API/数据库技能 | 集合重叠 ≥2 |
| `TestFrontendJDMatching` | 无前端项目 → score <0.50 | 分数阈值 + action |
| `TestProductJDMatching` | 技术相关性不足，必须指出 gaps | 分数 + missing_skills |
| `TestAllJDsHaveRequiredFields` | 每个 JD 输出包含 strengths/weaknesses/gaps/recommendation | 参数化 |

### 2b. Evidence 约束测试（`test_evidence_grounded_generation.py`）

验证生成内容尊重 evidence status：

| 测试类 | 验证内容 |
|---|---|
| `TestNoEvidenceNoExaggeration` | 无 evidence → Gate 阻止、Faithfulness 评 0 |
| `TestPlannedEvidenceConstraints` | planned → 所有声称被阻止 |
| `TestDesignedEvidenceConstraints` | designed → 阻止实现动词、允许设计动词、downgrade 保留技术术语 |
| `TestImplementedEvidenceAllowsFullClaims` | implemented → 允许实现/构建/开发、夸大措辞有警告 |
| `TestGeneratedContentReferencesEvidence` | Bullet 必须有 evidence_ids 才 grounded |
| `TestNoForeignTechKeywords` | 不在 evidence 中的技术关键词不会出现在 matched_terms |
| `TestFaithfulnessCheckerWithMixedStatus` | 混合 status 整体评分降级、空 bullets 满分、全无证据失败 |

### 2c. 匹配分校准测试（`test_match_score_calibration.py`）

验证匹配分有区分度：

| 测试类 | 验证内容 |
|---|---|
| `TestScoreDiscrimination` | Agent JD 强匹配、Backend 中匹配、Frontend/Product 弱匹配 |
| `TestScoreSpread` | 8 个 JD 分数 range ≥0.25、std ≥0.08、Frontend 在最低 3 名 |
| `TestThresholdCorrectActions` | 低分 JD → not_priority、高分 JD → strong_apply 或 adjust |

**评估测试的断言策略（核心设计原则）：**

| 原则 | 示例 |
|---|---|
| 基于技能集合 | `assert _AGENT_SKILLS & matched → ≥2` |
| 基于分数区间 | `assert 0.65 <= score <= 0.95` |
| 基于 status 常量 | `assert EvidenceGate.validate(claim, STATUS_PLANNED).allowed == False` |
| 不硬编码文件名 | 用 `source_path` 检查来源类型，不检查具体路径 |
| 不硬编码精确分数 | 用范围断言，不用 `== 0.78` |

**运行命令：**
```bash
pytest tests/evals/ -v
```

---

## 第三层：端到端测试（E2E Tests）

**位置：** `tests/e2e/`

**目的：** 验证完整链路不崩溃、不编造。

### `test_jd_to_application_flow.py`

- 使用 `tempfile.TemporaryDirectory` 构建 sandbox profile 知识库
- 使用真实 `RAGPipeline` + `MemoryVectorStore`（零外部依赖）
- 使用真实 Agents（规则模式，无 LLM）
- 参数化全部 8 种 JD 类型
- 验证：evidence_refs 与检索 evidence 对应
- 验证：无 evidence 时输出保守
- 验证：全部 4 种消息类型都能生成
- 验证：BuildAgent 输出 metadata 包含所有约束类别

**运行命令：**
```bash
pytest tests/e2e/ -v
```

---

## 覆盖矩阵

| 维度 | 单元测试 | Evals | E2E |
|---|---|---|---|
| Schema 正确性 | V | | |
| Score 校验 | V | | |
| Evidence Gate 单规则 | V | | |
| Faithfulness 单 bullet | V | | |
| RAG 管道分段 | V | | |
| 技能匹配方向 | | V | |
| 匹配置信度校准 | | V | |
| 状态约束端到端 | | V | |
| 生成措辞约束 | | V | V |
| 完整链路不崩溃 | | | V |
| 无编造保证 | | V | V |
| 消息类型覆盖 | | | V |

---

## 不测试的内容

- **真实 LLM 输出的具体文本** — 单元测试用 `MockProvider`，E2E 只测结构
- **Embedding 模型的实际语义质量** — 用 `HashEmbeddingProvider` 验证接口链路
- **前端 UI 布局** — 用 `test_streamlit_app_static.py` 做组件导入检查
- **网络连接和 API 调用的重试** — 用 `MockProvider` 模拟失败场景

---

## CI 集成

```bash
#!/bin/bash
# 完整测试套件
PYTHONPATH=src:$PWD pytest tests/ -v --timeout=60

# 仅快速反馈（单元 + Evals）
PYTHONPATH=src:$PWD pytest tests/ --ignore=tests/e2e -v --timeout=30
```

全部三层测试在每次 `git push` 时自动运行，任何失败阻止合并。
