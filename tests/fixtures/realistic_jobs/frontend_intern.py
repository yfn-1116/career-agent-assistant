"""Frontend intern JD fixture."""
from __future__ import annotations

from career_agent.domain.schemas import ParsedJD


def make_jd() -> ParsedJD:
    return ParsedJD(
        job_title="前端开发实习生",
        job_direction="frontend",
        hard_skills=[
            "React", "TypeScript", "JavaScript", "CSS", "HTML",
            "Vue",
        ],
        bonus_skills=[
            "Next.js", "Webpack", "Node.js", "Tailwind CSS",
            "前端性能优化", "ECharts",
        ],
        soft_skills=["审美", "沟通", "协作"],
        keywords=[
            "React", "TypeScript", "JavaScript", "CSS", "HTML",
            "Vue", "前端", "Next.js", "Webpack", "响应式",
        ],
        raw_text="""# 岗位 JD：前端开发实习生

## 基本信息
- 公司：CC 互娱（互联网方向，500 人）
- 岗位：前端开发实习生
- 地点：广州
- 类型：实习（每周 4 天以上）

## 岗位职责
1. 参与公司 Web 产品的前端页面开发
2. 使用 React / Vue 实现 UI 组件
3. 配合后端完成接口联调和数据展示
4. 参与前端性能优化和组件库维护

## 任职要求
1. 熟练掌握 HTML、CSS、JavaScript
2. 熟悉 React 或 Vue 框架
3. 了解 TypeScript
4. 了解前端工程化（Webpack / Vite）

## 加分项
- 有 Next.js 或 Nuxt.js 使用经验
- 了解 Node.js 后端开发
- 有移动端适配经验
- 参与过开源前端项目""",
    )
