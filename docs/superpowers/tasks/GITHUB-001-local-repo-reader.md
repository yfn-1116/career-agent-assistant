# GITHUB-001 本地 GitHub Repo Reader

## 任务编号

GITHUB-001

## 建议执行者

Claude Code + DeepSeek

## 任务目标

实现本地 GitHub 仓库 Markdown 读取器，支撑后续 GitHubRepoAgent。

## 允许修改文件

- src/career_agent/github/
- tests/github/
- data/samples/github_repos/
- documents/97-journal.md
- documents/99-project-planning.md

## 禁止修改文件

- src/career_agent/rag/
- src/career_agent/agents/
- src/career_agent/workflows/

## 测试命令

```bash
PYTHONPATH=src pytest tests/github -v
PYTHONPATH=src pytest tests/rag tests/agents tests/workflows tests/demo tests/models tests/evaluation tests/github -v
```

## 验收标准

- README 和 docs Markdown 可被读取
- 输出为 ProfileDocument 列表
- 不访问网络
- 现有测试全部通过

## 提交信息建议

```text
feat: add local github repo reader
```
