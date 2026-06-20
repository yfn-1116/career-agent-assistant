# WORKFLOW-001 Agent Workflow 集成

## 任务编号

WORKFLOW-001

## 建议执行者

Codex

## 任务目标

集成 JDParserAgent、RAGRetrieveAgent、MatchAnalysisAgent、BuildAgent，形成第一阶段可运行 workflow。

## 允许修改文件

- `src/workflows/agent_workflow.py`
- `tests/workflows/test_agent_workflow.py`
- `documents/02-design/03-multi-agent-orchestration.md`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- RAG 底层实现，除非发现接口缺陷并有明确授权。
- Streamlit 页面。
- 部署脚本。
- `data/`
- `outputs/`

## 输入

- `AgentTaskState`
- 四个核心 Agent
- RAG pipeline

## 输出

- 可被 CLI demo 调用的 workflow 入口。

## 实现要求

- 保持固定流程。
- 每个 Agent 只读写规定状态字段。
- 错误写入 `error_message`。
- 不在 workflow 中写具体业务生成逻辑。

## 验收标准

- 固定样例能跑完整链路。
- 状态字段按顺序更新。
- 任一节点失败时有清晰错误。

## 测试命令

```bash
pytest tests/workflows/test_agent_workflow.py -v
git status --short
```

## 提交信息建议

```text
feat: integrate first phase agent workflow
```
