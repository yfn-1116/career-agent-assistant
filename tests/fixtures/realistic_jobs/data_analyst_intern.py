"""Data analyst intern JD fixture."""
from __future__ import annotations

from career_agent.domain.schemas import ParsedJD


def make_jd() -> ParsedJD:
    return ParsedJD(
        job_title="数据分析实习生",
        job_direction="data",
        hard_skills=[
            "Python", "SQL", "Pandas", "NumPy",
            "数据可视化", "Excel",
        ],
        bonus_skills=[
            "Tableau", "PowerBI", "统计学", "A/B 测试",
            "机器学习",
        ],
        soft_skills=["业务理解", "沟通", "数据敏感度"],
        keywords=[
            "Python", "SQL", "Pandas", "数据分析", "可视化",
            "Excel", "Tableau", "统计学",
        ],
        raw_text="""# 岗位 JD：数据分析实习生

## 基本信息
- 公司：DD 数据科技（大数据方向，150 人）
- 岗位：数据分析实习生
- 地点：成都
- 类型：实习（每周 4 天以上，至少 2 个月）

## 岗位职责
1. 使用 SQL 从数据库提取和清洗业务数据
2. 使用 Python（Pandas / Matplotlib）进行数据分析
3. 制作数据可视化报告支持业务决策
4. 参与 A/B 测试的设计和结果分析

## 任职要求
1. 熟练使用 SQL 进行数据查询
2. 掌握 Python 数据分析相关库（Pandas、NumPy）
3. 能使用可视化工具（Tableau / PowerBI / Matplotlib）
4. 具备基本的统计学知识
5. 对数据敏感，能从数据中发现业务洞察

## 加分项
- 了解机器学习基础
- 有 Kaggle 数据分析比赛经验
- 了解 A/B 测试方法论""",
    )
