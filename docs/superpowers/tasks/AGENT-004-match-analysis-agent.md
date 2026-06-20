# AGENT-004 MatchAnalysisAgent 实现

## 任务编号

AGENT-004

## 建议执行者

Claude Code + DeepSeek

## 任务目标

只实现岗位要求与用户资料证据之间的匹配分析。

## 允许修改文件

- `src/agents/match_analysis.py`
- `tests/agents/test_match_analysis.py`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/rag/`
- `src/workflows/`
- demo 文件
- BuildAgent 文件

## 输入

- `parsed_jd`
- `retrieved_evidence`

## 输出

- `match_analysis`

## 实现要求

- 不生成最终简历文本。
- 不读取原始 Markdown。
- 不调用外部检索。

## 验收标准

- 输出包含强匹配、弱匹配、缺口和建议。
- 每个匹配点能指向 evidence。
- 证据不足时明确提示。

## 测试命令

```bash
pytest tests/agents/test_match_analysis.py -v
git status --short
```

## 提交信息建议

```text
feat: add match analysis agent
```
