# DEMO-003 RAG 检索诊断展示

## 任务编号

DEMO-003

## 建议执行者

Claude Code + DeepSeek

## 任务目标

在 CLI Markdown 报告和 Streamlit 页面中展示 RAG 检索效果，包括 query、overall grade、指标表和 top evidence 详情。

## 允许修改文件

- `demo/cli/run_job_match_demo.py`
- `demo/streamlit/app.py`
- `tests/demo/test_cli_demo_smoke.py`
- `tests/demo/test_streamlit_app_static.py`
- `documents/06-demo/01-demo-script.md`
- `documents/06-demo/03-presentation-flow.md`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/career_agent/rag/`
- `src/career_agent/agents/`
- `src/career_agent/workflows/`，除非切换到已完成的 `LangGraphJobMatchWorkflow` 入口。
- `outputs/demo/`，除非运行 demo 生成报告并在任务说明中记录。
- `frontend/`
- `backend/`
- `server/`

## 输入

- `AgentTaskState.retrieval_grade_report`
- `AgentTaskState.retrieval_query`
- `retrieved_evidence`

## 输出

- CLI 报告中的 `## 4. RAG 检索诊断` 或等价章节。
- Streamlit 页面中的 `RAG 检索效果` 区域。
- 对应 smoke/static tests。

## 实现要求

- 展示层只读取 workflow state，不实现评分逻辑。
- CLI 报告必须展示 query、grade、关键 metrics、top evidence。
- Streamlit 必须展示 grade、query、metrics table、evidence expandable sections。
- 文案需要说明评分是规则型诊断，不是人工标注或 LLM judge。

## 测试命令

```bash
pytest tests/demo/test_cli_demo_smoke.py tests/demo/test_streamlit_app_static.py -v
PYTHONPATH=src python demo/cli/run_job_match_demo.py
git status --short
```

## 验收标准

- CLI 输出文件能看到 RAG 检索诊断。
- Streamlit 静态测试能识别 RAG 检索效果 UI。
- 旧 demo 功能不丢失。

## 建议 commit message

```text
feat: show rag retrieval diagnostics in demos
```
