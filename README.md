# career-agent-assistant

## 项目定位

`career-agent-assistant` 是一个面向大学生实习求职场景的智能投递辅助 Agent。项目目标是帮助用户围绕岗位 JD、个人资料、项目经历和沟通场景，生成更可控、更可追溯的求职辅助输出。

## 核心模块

- RAG 用户资料知识库：整理简历、项目经历、GitHub 仓库摘要、实习经历、技能材料等个人能力信息，后续用于检索增强生成。
- 多 Agent 编排：围绕 JD 解析、资料检索、匹配分析、简历项目描述生成、沟通话术生成等任务设计可控工作流。

## 第一阶段目标

第一阶段坚持文档先行，先明确项目边界、模块拆分、协作规范、任务流程和验收方式。当前阶段不实现完整前后端，不实现 RAG，不实现 Agent workflow，不实现 Streamlit 页面。

## 当前状态

项目处于初始化阶段，尚未实现业务代码。当前仓库只包含中文项目文档体系、AI 协作规范和基础目录占位。

## 后续开发流程

后续开发遵循：文档设计 -> `docs/superpowers/specs/`、`docs/superpowers/plans/`、`docs/superpowers/tasks/` -> 代码实现 -> 测试验证 -> GitHub 同步 -> 学校服务器部署展示。

## 维护规则

- 任何业务实现前必须先补充对应任务说明。
- 不允许在没有授权的情况下修改全局架构、核心 schema、workflow 集成和技术选型。
- 执行任务后必须更新 `documents/97-journal.md` 和 `documents/99-project-planning.md`。
