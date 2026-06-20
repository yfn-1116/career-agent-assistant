# RAG-001 RAG 核心数据结构设计

## 任务编号

RAG-001

## 建议执行者

Codex

## 任务目标

设计 RAG 第一阶段核心 schema：`ProfileItem`、`ProfileDocument`、`DocumentChunk`、`RetrievedEvidence`，并明确字段语义和模块边界。本任务只写设计，不实现代码。

## 允许修改文件

- `documents/02-design/02-rag-module-design.md`
- `documents/05-evaluation/01-rag-evaluation.md`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/`
- `tests/`
- `data/`
- `outputs/`
- Agent workflow 文档以外的实现文件
- 依赖配置文件

## 输入

- `documents/00-project-overview.md`
- `documents/02-design/02-rag-module-design.md`
- `documents/01-requirements/02-mvp-scope.md`

## 输出

- 明确四个 schema 的字段方向、字段含义、第一阶段必填字段和后续扩展字段。
- 明确 loader、chunker、retriever、pipeline 对 schema 的使用边界。

## 实现要求

- 不写 Python 代码。
- 不引入依赖。
- 需要说明字段如何支持证据追溯和幻觉控制。

## 验收标准

- `ProfileItem`、`ProfileDocument`、`DocumentChunk`、`RetrievedEvidence` 均有字段说明。
- 每个 schema 能解释它服务于哪一步 RAG 流程。
- 文档明确第一阶段不做多用户知识库和大规模 GitHub 源码分析。

## 测试命令

```bash
git status --short
find documents docs/superpowers/tasks -name '*.md' -type f -empty -print
```

## 提交信息建议

```text
docs: define rag core schema design
```
