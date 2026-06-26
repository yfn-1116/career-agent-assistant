"""Product intern JD fixture."""
from __future__ import annotations

from career_agent.domain.schemas import ParsedJD


def make_jd() -> ParsedJD:
    return ParsedJD(
        job_title="产品实习生",
        job_direction="product",
        hard_skills=[
            "产品分析", "用户调研", "PRD 撰写", "竞品分析",
        ],
        bonus_skills=[
            "数据分析", "SQL", "Axure", "Figma",
            "敏捷开发", "项目管理",
        ],
        soft_skills=["沟通", "逻辑思维", "用户共情", "执行力"],
        keywords=[
            "产品", "用户调研", "PRD", "竞品分析", "数据分析",
            "需求文档", "原型设计",
        ],
        raw_text="""# 岗位 JD：产品实习生

## 基本信息
- 公司：EE 创投（互联网方向，80 人）
- 岗位：产品实习生
- 地点：深圳
- 类型：实习（每周 4 天以上，至少 3 个月）

## 岗位职责
1. 参与产品需求的收集、整理和优先级评估
2. 撰写 PRD（产品需求文档）和用户故事
3. 协助完成竞品分析和市场调研
4. 跟进产品开发进度，协调设计、开发、测试团队
5. 参与用户访谈和产品数据复盘

## 任职要求
1. 对互联网产品有热情和好奇心
2. 逻辑清晰，能用数据和事实支撑观点
3. 有基本的用户调研和需求分析能力
4. 能熟练使用 Office 或类似的文档协作工具

## 加分项
- 了解基本的数据分析方法（SQL 加分）
- 有产品实习或项目经验
- 会使用 Axure 或 Figma 画原型
- 了解敏捷开发流程""",
    )
