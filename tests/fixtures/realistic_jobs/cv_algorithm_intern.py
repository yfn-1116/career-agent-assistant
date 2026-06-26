"""CV algorithm intern JD fixture."""
from __future__ import annotations

from career_agent.domain.schemas import ParsedJD


def make_jd() -> ParsedJD:
    return ParsedJD(
        job_title="计算机视觉算法实习生",
        job_direction="cv",
        hard_skills=[
            "Python", "PyTorch", "TensorFlow", "OpenCV",
            "CNN", "图像处理", "目标检测",
        ],
        bonus_skills=[
            "ResNet", "YOLO", "数据增强", "迁移学习",
            "模型部署", "TensorRT",
        ],
        soft_skills=["论文阅读", "实验设计", "文档"],
        keywords=[
            "Python", "PyTorch", "OpenCV", "CNN", "ResNet",
            "YOLO", "图像处理", "目标检测", "机器学习",
            "深度学习", "数据增强", "迁移学习",
        ],
        raw_text="""# 岗位 JD：计算机视觉算法实习生

## 基本信息
- 公司：BB 视觉科技（AI 视觉方向，100 人）
- 岗位：计算机视觉算法实习生
- 地点：深圳
- 类型：实习（每周 5 天，至少 3 个月）

## 岗位职责
1. 参与图像分类和目标检测模型的训练与优化
2. 负责数据集的收集、清洗和增强（augmentation）
3. 实现和复现 CV 论文中的算法
4. 参与模型推理性能的优化和部署

## 任职要求
1. 计算机视觉或机器学习相关方向
2. 熟练使用 PyTorch 或 TensorFlow
3. 了解 CNN、ResNet、YOLO 等经典模型架构
4. 有图像处理或 OpenCV 的实际使用经验
5. 能阅读和理解英文论文

## 加分项
- 有 Kaggle 或 CV 竞赛经验
- 了解模型量化、剪枝等压缩技术
- 了解 TensorRT 或 ONNX 部署
- 有 3D 视觉或点云处理经验""",
    )
