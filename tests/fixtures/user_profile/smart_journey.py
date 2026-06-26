"""PolyU Smart Journey project — implemented, backend + GIS focus."""
from __future__ import annotations

from career_agent.profile.schema import ProfileItem, STATUS_IMPLEMENTED


def make_item() -> ProfileItem:
    return ProfileItem(
        item_id="proj-smart-journey",
        source_path="github/polyu-internship-project/README.md",
        source_type="github_repo",
        title="PolyU Smart Journey 智能路径规划",
        project_name="smart-journey",
        skills=[
            "FastAPI", "PostgreSQL", "Docker", "REST API",
            "Leaflet.js", "A-star", "路径规划", "地图服务",
            "SQL", "数据库", "Python",
        ],
        claims=[
            "使用 FastAPI 开发 RESTful API 后端",
            "实现 A-star 算法进行校园路径规划",
            "Docker 容器化部署",
            "PostgreSQL 存储地图和路径数据",
            "Leaflet.js 前端地图可视化",
        ],
        status=STATUS_IMPLEMENTED,
        confidence=0.85,
        raw_content="""# PolyU Smart Journey

基于 A-star 算法的校园智能路径规划 Web 应用。

## 技术栈
- FastAPI + PostgreSQL + Docker
- A-star 路径规划算法
- Leaflet.js 地图可视化
- RESTful API 设计

## 核心能力
- 后端 API 开发（FastAPI）
- 数据库设计（PostgreSQL）
- 算法实现（A-star 寻路）
- Docker 容器化
""",
        metadata={
            "source_url": "https://github.com/yfn-1116/polyu-internship-project",
            "tags": ["backend", "fastapi", "postgresql", "docker", "gis"],
            "stars": 0,
            "language": "Python",
        },
    )
