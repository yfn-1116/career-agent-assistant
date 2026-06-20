# ARCH-001 核心架构边界与模块契约

## 任务编号

ARCH-001

## 建议执行者

Codex

## 任务目标

补强项目总览、需求边界、核心设计、技术决策、挑战评估和后续任务卡，明确第一阶段 RAG + 多 Agent 原型系统边界。

## 允许修改文件

- `README.md`
- `documents/00-project-overview.md`
- `documents/01-requirements/`
- `documents/02-design/`
- `documents/03-technical-decisions/`
- `documents/04-challenges/`
- `documents/05-evaluation/`
- `documents/06-demo/`
- `documents/97-journal.md`
- `documents/99-project-planning.md`
- `docs/superpowers/README.md`
- `docs/superpowers/tasks/`

## 禁止修改文件

- `src/`
- `tests/`
- `data/`
- `outputs/`
- `.env.example`
- `.gitignore`
- `AGENTS.md`
- frontend/backend/server/app/scripts 目录
- 依赖配置文件

## 输入

- 用户提供的 ARCH-001 任务说明。
- Phase 0 初始化文档。

## 输出

- 补强后的中文架构文档。
- 后续 RAG、Agent、Workflow、Sample、Demo、Deploy 任务卡。
- 更新后的 journal 和 project planning。

## 实现要求

- 只写中文 Markdown。
- 不实现业务代码。
- 不新增依赖。
- 不改变现有目录体系。

## 验收标准

- 明确第一阶段是 RAG + 多 Agent 原型系统。
- 明确 CLI + Markdown 优先，Streamlit 轻量展示，暂不做完整前后端。
- 明确第一阶段 RAG 只处理本地 Markdown 和 GitHub 仓库摘要。
- 明确四个核心 Agent。
- 任务卡包含允许文件、禁止文件和验收标准。

## 测试命令

```bash
git status --short
find documents docs/superpowers/tasks -name '*.md' -type f -empty -print
find . -path './.git' -prune -o -type d \( -name frontend -o -name backend -o -name server -o -name app -o -name scripts \) -print
```

## 提交信息建议

```text
docs: define core architecture boundaries and implementation task cards
```
