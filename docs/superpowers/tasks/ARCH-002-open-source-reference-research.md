# ARCH-002 开源项目调研与参考架构沉淀

## 任务编号

ARCH-002

## 建议执行者

Codex

## 任务目标

调研成熟开源项目在 RAG、多 Agent 编排、项目结构、文档管理、任务编排和 demo 展示方面的设计，并沉淀为本项目后续开发参考。

## 允许修改文件

- `documents/97-journal.md`
- `documents/99-project-planning.md`
- `documents/99-knowledge-base/README.md`
- `documents/99-knowledge-base/05-open-source-reference-projects.md`
- `documents/03-technical-decisions/README.md`
- `documents/03-technical-decisions/06-reference-architecture-selection.md`
- `documents/02-design/README.md`
- `documents/02-design/07-reference-inspired-architecture.md`
- `docs/superpowers/tasks/README.md`
- `docs/superpowers/tasks/ARCH-002-open-source-reference-research.md`
- `docs/superpowers/tasks/DOC-REFERENCE-001-open-source-reference-docs.md`
- `docs/superpowers/tasks/ARCH-003-codebase-structure-decision.md`

## 禁止修改文件

- `src/`
- `tests/`
- `data/`
- `outputs/`
- `.env.example`
- `.gitignore`
- `AGENTS.md`
- `README.md`
- frontend/backend/server/app/scripts 目录
- 依赖配置文件

## 输入

- ARCH-002 用户任务说明。
- Phase 0 和 ARCH-001 文档。
- 公开开源项目 README、docs、examples。

## 输出

- 开源项目参考调研文档。
- 参考架构选择技术决策。
- 参考架构启发下的本项目代码结构草案。
- 后续任务卡。

## 实现要求

- 只写中文 Markdown。
- 不实现业务代码。
- 不复制大段开源项目内容。
- 网络访问受限时必须说明。

## 验收标准

- 至少调研 6 个开源项目。
- 至少新增 3 个核心文档。
- 至少新增 ARCH-002、DOC-REFERENCE-001、ARCH-003 三张任务卡。
- 未修改 `src/`、`tests/`、`data/`、`outputs/`。
- 未新增 frontend/backend/server/app/scripts。

## 测试命令

```bash
git status --short
find documents docs/superpowers/tasks -name '*.md' -type f -empty -print
find . -path './.git' -prune -o -type d \( -name frontend -o -name backend -o -name server -o -name app -o -name scripts \) -print
```

## 提交信息建议

```text
docs: research open source references and refine architecture direction
```
