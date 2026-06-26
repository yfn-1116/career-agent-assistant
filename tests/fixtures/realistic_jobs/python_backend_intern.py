"""Python backend intern JD fixture."""
from __future__ import annotations

from career_agent.domain.schemas import ParsedJD


def make_jd() -> ParsedJD:
    return ParsedJD(
        job_title="Python 后端开发实习生",
        job_direction="backend",
        hard_skills=[
            "Python", "FastAPI", "PostgreSQL", "MySQL", "Redis",
            "Docker", "SQL", "RESTful", "API",
        ],
        bonus_skills=[
            "Kubernetes", "CI/CD", "Git", "微服务", "Flask",
            "Django", "消息队列",
        ],
        soft_skills=["协作", "文档", "工程化"],
        keywords=[
            "Python", "FastAPI", "PostgreSQL", "MySQL", "Redis",
            "Docker", "SQL", "API", "后端", "Flask", "Django",
            "微服务", "Kubernetes", "CI/CD",
        ],
        raw_text="""# 岗位 JD：Python 后端开发实习生

## 基本信息
- 公司：AA 信息技术（SaaS 方向，300 人）
- 岗位：Python 后端开发实习生
- 地点：上海
- 类型：实习（每周 4 天以上，至少 3 个月）

## 岗位职责
1. 参与公司后端 API 服务的开发和维护
2. 编写数据库查询和优化 SQL 性能
3. 参与微服务架构的模块拆分和接口设计
4. 编写单元测试和接口文档

## 任职要求
1. 熟练掌握 Python，有 Web 后端开发经验（FastAPI / Flask / Django）
2. 了解关系型数据库（PostgreSQL / MySQL）的使用
3. 了解 RESTful API 设计规范
4. 了解 Docker 的基本使用
5. 了解 Git 版本控制和团队协作流程

## 加分项
- 了解 Redis 等缓存中间件
- 有微服务相关项目经验
- 了解消息队列（Kafka / RabbitMQ）
- 了解 CI/CD 流水线配置""",
    )
