"""Chem-auto-titration project — implemented, CV + hardware focus."""
from __future__ import annotations

from career_agent.profile.schema import ProfileItem, STATUS_IMPLEMENTED


def make_item() -> ProfileItem:
    return ProfileItem(
        item_id="proj-chem-auto-titration",
        source_path="github/chem-auto-titration/README.md",
        source_type="github_repo",
        title="自动滴定系统（Chem Auto Titration）",
        project_name="chem-auto-titration",
        skills=[
            "Python", "OpenCV", "PyTorch", "Arduino", "3D 打印",
            "串口通信", "ResNet", "状态机", "图像处理",
            "数据采集", "传感器", "PID 控制",
        ],
        claims=[
            "基于 OpenCV 实现滴定终点的自动识别",
            "使用 ResNet 进行颜色分类判断",
            "Arduino 控制滴定泵和搅拌器",
            "3D 打印设计反应池支架",
            "串口通信实现上位机与下位机数据交换",
        ],
        status=STATUS_IMPLEMENTED,
        confidence=0.90,
        raw_content="""# 自动滴定系统

化学实验室自动化项目。使用计算机视觉自动检测滴定终点，
Arduino 控制滴定泵，实现全自动滴定。

## 技术栈
- Python + OpenCV + PyTorch
- Arduino + 串口通信
- ResNet 颜色分类
- 3D 打印硬件设计

## 核心能力
- CV 图像处理：颜色变化检测
- 机器学习：ResNet 分类滴定状态
- 嵌入式：Arduino 控制 + 传感器读取
- 机械设计：3D 打印反应池和支架
""",
        metadata={
            "source_url": "https://github.com/yfn-1116/chem-auto-titration",
            "tags": ["cv", "opencv", "pytorch", "arduino", "hardware"],
            "stars": 0,
            "language": "Python",
        },
    )
