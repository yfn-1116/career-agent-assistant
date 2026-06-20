# RAG-001 RAG 核心数据结构设计

## 任务编号

RAG-001

## 建议执行者

Codex

## 任务目标

设计并实现第一阶段 RAG 核心 schema：`ProfileItem`、`ProfileDocument`、`DocumentChunk`、`RetrievedEvidence`。ARCH-003 只确定后续创建路径，本任务执行时才允许写代码。

## 允许修改文件

- `src/career_agent/__init__.py`
- `src/career_agent/rag/__init__.py`
- `src/career_agent/rag/schemas.py`
- `tests/rag/test_schemas.py`
- `documents/02-design/02-rag-module-design.md`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/career_agent/agents/`
- `src/career_agent/workflows/`
- `src/career_agent/models/`
- `demo/`
- `data/`
- `outputs/`
- `pyproject.toml`
- `requirements.txt`

## 输入

- `documents/02-design/02-rag-module-design.md`
- `documents/02-design/07-reference-inspired-architecture.md`
- ARCH-003 代码目录结构决策。

## 输出

- `ProfileItem`
- `ProfileDocument`
- `DocumentChunk`
- `RetrievedEvidence`
- 对应 schema 单元测试。

## 实现要求

- 字段必须支持 source、quote、metadata、score、reason 等证据追溯能力。
- 不实现 loader、chunker、retriever、pipeline。
- 不引入向量库依赖。
- 不调用模型。

## 测试命令

```bash
pytest tests/rag/test_schemas.py -v
git status --short
```

## 验收标准

- 四个 schema 均有稳定字段和基本校验。
- 测试覆盖必填字段、默认值和 evidence 来源追溯。
- 未修改 Agent、Workflow、Demo。

## 建议 commit message

```text
feat: define rag core schemas
```
