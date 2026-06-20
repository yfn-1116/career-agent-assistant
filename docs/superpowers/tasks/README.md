# Agent 任务卡目录

## 用途

本目录存放可交给执行 Agent 的任务卡。任务卡是执行边界，不是灵感列表。

## 任务卡必备字段

每个任务卡必须包含：

- 任务编号
- 建议执行者
- 任务目标
- 允许修改文件
- 禁止修改文件
- 输入
- 输出
- 实现要求
- 验收标准
- 测试命令
- 提交信息建议

## 当前状态

当前已建立 ARCH、DOC、RAG、AGENT、WORKFLOW、SAMPLE、DEMO、DEPLOY 任务卡，覆盖第一阶段从文档补强、参考架构调研到 demo 展示的主要链路。

## 当前新增重点

- `ARCH-002-open-source-reference-research.md`：开源项目调研与参考架构沉淀。
- `DOC-REFERENCE-001-open-source-reference-docs.md`：后续补充开源参考细节。
- `ARCH-003-codebase-structure-decision.md`：最终确定第一阶段代码目录结构。

## 后续维护规则

- 没有任务卡不得启动执行任务。
- 不允许一个任务同时修改 RAG、Agent、Demo、部署多个大模块。
- 核心接口和 workflow 集成任务优先交给 Codex。
