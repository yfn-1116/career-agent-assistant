# GitHub 同步与协作规范

## 1. 查看当前状态

```bash
git status
git log --oneline -5
```

## 2. 提交更改

```bash
git add <文件>
git commit -m "<类型>: <简短描述>"
```

推荐 commit message 格式：

```text
feat: <新功能>
docs: <文档更新>
fix: <修复>
test: <测试>
chore: <杂项>
```

## 3. 推送到远端

```bash
git push
```

## 4. 拉取远端更新

```bash
git pull
```

如果本地有未提交更改，先提交或 stash 再 pull。

## 5. 多 AI 协作注意事项

本项目由 Codex 和 Claude Code + DeepSeek 协作开发。为避免冲突：

1. **每个任务完成后立即提交**，不要积攒多个任务的修改。
2. **提交前先运行测试**：

   ```bash
   PYTHONPATH=src pytest tests/rag tests/agents tests/workflows tests/demo -v
   ```

3. **不要一次 commit 混合多个任务**。每个 commit 对应一个任务卡（如 RAG-002、AGENT-001）。
4. **提交后立即 push**，让协作者看到最新状态。
5. **如果 git push 被拒绝**（远端有更新），先 `git pull --rebase` 再 push。

## 6. 分支管理

当前所有开发在 `main` 分支。后续如需实验性开发，可创建功能分支：

```bash
git checkout -b feature/<功能名>
```

## 7. 文件冲突解决

如果 pull 时出现冲突：

1. 打开冲突文件，找到 `<<<<<<<` / `=======` / `>>>>>>>` 标记
2. 手动合并，保留需要的部分
3. `git add <文件>`
4. `git commit`
5. `git push`
