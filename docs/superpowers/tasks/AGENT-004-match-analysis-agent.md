# AGENT-004 MatchAnalysisAgent 实现

## 任务编号

AGENT-004

## 建议执行者

Claude Code + DeepSeek

## 任务目标

实现 `MatchAnalysisAgent`，只负责岗位要求与 evidence 的匹配分析。

## 允许修改文件

- `src/career_agent/agents/match_analysis_agent.py`
- `tests/agents/test_match_analysis_agent.py`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/career_agent/rag/`
- `src/career_agent/workflows/`
- `src/career_agent/agents/build_agent.py`
- `demo/`
- `data/`
- `outputs/`

## 输入

- `parsed_jd`
- `retrieved_evidence`

## 输出

- `match_analysis`

## 实现要求

- 不生成最终简历文本。
- 不读取原始 Markdown。
- 不调用外部检索。
- 每个匹配点必须能追溯到 evidence。

## 测试命令

```bash
pytest tests/agents/test_match_analysis_agent.py -v
git status --short
```

## 验收标准

- 输出包含强匹配、弱匹配、缺口和建议。
- 证据不足时明确提示。
- 不编造经历。

## 建议 commit message

```text
feat: add match analysis agent
```
