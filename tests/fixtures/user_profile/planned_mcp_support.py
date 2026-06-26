"""Planned MCP support — status=planned, used to test evidence constraints."""
from __future__ import annotations

from career_agent.profile.schema import ProfileItem, STATUS_PLANNED


def make_item() -> ProfileItem:
    return ProfileItem(
        item_id="proj-planned-mcp",
        source_path="github/career-agent-assistant/docs/roadmap.md",
        source_type="design_doc",
        title="MCP 协议支持（计划中）",
        project_name="career-agent-assistant",
        skills=["MCP", "Tool Calling", "协议设计", "外部工具集成"],
        claims=[
            "计划接入 MCP 协议，支持外部工具扩展",
            "拟设计统一的 Tool Registry 接口",
            "后续规划支持 MCP server 注册与发现",
        ],
        status=STATUS_PLANNED,
        confidence=0.30,
        raw_content="""# MCP 协议支持规划

## 当前状态：规划中

计划为 career-agent-assistant 添加 MCP（Model Context Protocol）协议支持。

## 目标
- 接入 MCP 协议，使 Agent 能调用外部工具
- 统一 Tool Registry 接口设计
- 支持 MCP server 的注册与发现

## 时间线
- 方案设计：2025 Q3
- 原型开发：2025 Q4
""",
        metadata={
            "source_url": "https://github.com/yfn-1116/career-agent-assistant/issues/42",
            "tags": ["planned", "mcp", "tool-calling", "protocol"],
            "status_note": "此项目尚未开始编码，仅完成方案设计阶段",
        },
    )
