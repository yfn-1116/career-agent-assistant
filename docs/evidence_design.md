# Evidence 证据约束设计

核心创新：别人的 RAG 只看"有没有检索到证据"，本系统多看一步——"证据的质量等级"。

## 一、状态推断（ProfileLoader）

**文件：** `profile/loader.py:73-95`

用户上传资料后，系统自动推断每段经历的可信度等级：

```python
impl_score   = count_matches(content, [r"完成|部署|上线|实现|构建|开发", ...])
design_score = count_matches(content, [r"设计|架构|方案|预留|接口", ...])
planned_score = count_matches(content, [r"计划|后续|TODO|FIXME", ...])

if impl_score > 0:    return "implemented"   # 有证据证明实现了
if design_score > 0:  return "designed"      # 有设计方案，不确定是否实现
if planned_score > 0: return "planned"        # 只有规划，还没做
return "uncertain"                           # 无法判断
```

## 二、声称验证（EvidenceGate）

**文件：** `evidence/gate.py:46-84`

BuildAgent 生成简历描述前，EvidenceGate 先检查措辞是否合法：

| evidence status | 允许的动词 | 不允许的动词 | 效果 |
|---|---|---|---|
| implemented | 实现/构建/完成/开发 | — | 可直接写入简历 |
| designed | 设计/规划/架构 | 实现/构建/完成 | 自动降级措辞 |
| planned | — | 所有声称 | 阻止写入 |
| 无 evidence | — | 所有声称 | 阻止写入 |

## 三、生成约束（BuildAgent）

**文件：** `agents/build_agent.py:240-278`

BuildAgent 把所有生成的 bullet 分成三类输出：

- **can_write_claims** ← implemented → 🟢 可直接写入简历
- **needs_confirmation_claims** ← designed → 🟡 需用户确认后使用
- **learning_plan_claims** ← planned/uncertain → 🔴 仅作为学习方向

### 答辩话术

> "别人的 RAG 只看'有没有检索到证据'。我的系统多看一步——'证据的质量等级'。implemented 的经历可以直接写进简历；designed 的经历必须降级措辞，比如'实现了 MCP 协议'自动改成'设计了 MCP 方案'；planned 的阶段直接阻止写入。这样保证生成的简历每句话都有真实经历支撑，不编造。"
