# DOC-REFERENCE-001 开源项目参考文档补全

## 任务编号

DOC-REFERENCE-001

## 建议执行者

Claude Code + DeepSeek

## 任务目标

基于 ARCH-002 的调研结果，继续补充开源项目参考细节、对比表和后续可借鉴模式。

## 允许修改文件

- `documents/99-knowledge-base/05-open-source-reference-projects.md`
- `documents/97-journal.md`
- `documents/99-project-planning.md`

## 禁止修改文件

- `src/`
- `tests/`
- `data/`
- `outputs/`
- `documents/02-design/`
- `documents/03-technical-decisions/`
- `AGENTS.md`
- `README.md`

## 输入

- `documents/99-knowledge-base/05-open-source-reference-projects.md`
- 公开项目 README 和官方文档。

## 输出

- 更完整的开源项目对比表。
- 更细的可借鉴点和不适合照搬点。
- 补充参考来源链接。

## 实现要求

- 只写中文 Markdown。
- 不修改架构决策。
- 不新增业务代码。
- 不把开源项目内容大段复制进仓库。

## 验收标准

- 每个项目至少有定位、可借鉴点、不适合照搬点和对本项目启发。
- 新增内容能支撑 ARCH-003 决策。
- 不修改禁改目录。

## 测试命令

```bash
git status --short
find documents/99-knowledge-base -name '*.md' -type f -empty -print
```

## 提交信息建议

```text
docs: expand open source reference research
```
