# AGENT-002 JDParserAgent 实现

## 任务编号

AGENT-002

## 建议执行者

Claude Code + DeepSeek

## 任务目标

只实现 JD 解析 Agent，将岗位 JD 转为结构化 `parsed_jd`。

## 允许修改文件

- `src/agents/jd_parser.py`
- `tests/agents/test_jd_parser.py`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/rag/`
- `src/workflows/`
- demo 文件
- `data/`
- `outputs/`

## 输入

- 岗位 JD 文本。

## 输出

- 岗位标题、职责、技术栈、关键词、能力要求、检索 query。

## 实现要求

- 不调用 RAG。
- 不生成简历。
- 不做匹配分析。

## 验收标准

- 示例 JD 能解析出关键词和技术栈。
- 空 JD 有清晰错误。
- 输出结构稳定。

## 测试命令

```bash
pytest tests/agents/test_jd_parser.py -v
git status --short
```

## 提交信息建议

```text
feat: add jd parser agent
```
