# AGENT-002 JDParserAgent 实现

## 任务编号

AGENT-002

## 建议执行者

Claude Code + DeepSeek

## 任务目标

实现 `JDParserAgent`，只负责将岗位 JD 解析为结构化 `parsed_jd`。

## 允许修改文件

- `src/career_agent/agents/jd_parser.py`
- `tests/agents/test_jd_parser.py`
- `data/samples/jobs/`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/career_agent/rag/`
- `src/career_agent/workflows/`
- `src/career_agent/agents/rag_retrieve_agent.py`
- `src/career_agent/agents/match_analysis_agent.py`
- `src/career_agent/agents/build_agent.py`
- `demo/`
- `outputs/`

## 输入

- 岗位 JD 文本。
- `AgentTaskState`。
- 示例 JD。

## 输出

- `parsed_jd`，包括岗位标题、职责、技术栈、能力要求、关键词、检索 query。

## 实现要求

- 不调用 RAG。
- 不生成简历。
- 不做匹配分析。
- 可以先使用规则或 MockProvider 支持测试。

## 测试命令

```bash
pytest tests/agents/test_jd_parser.py -v
git status --short
```

## 验收标准

- 示例 JD 能解析出关键词和技术栈。
- 空 JD 有清晰错误。
- 输出结构稳定。

## 建议 commit message

```text
feat: add jd parser agent
```
