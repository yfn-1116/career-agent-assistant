"""Dog Breed CNN project — implemented, pure ML/CV focus."""
from __future__ import annotations

from career_agent.profile.schema import ProfileItem, STATUS_IMPLEMENTED


def make_item() -> ProfileItem:
    return ProfileItem(
        item_id="proj-dog-breed-cnn",
        source_path="github/dog-breed-cnn/README.md",
        source_type="github_repo",
        title="Dog Breed CNN 图像分类",
        project_name="dog-breed-cnn",
        skills=[
            "PyTorch", "CNN", "ResNet", "数据增强",
            "迁移学习", "图像分类", "Jupyter",
            "Python", "Matplotlib", "CUDA",
        ],
        claims=[
            "使用 PyTorch 实现 CNN 狗品种分类模型",
            "基于 ResNet-50 的迁移学习训练",
            "数据增强提升模型泛化能力（随机裁剪、翻转、色彩抖动）",
            "Top-1 accuracy 达到 85%",
            "Jupyter Notebook 完整记录实验过程",
        ],
        status=STATUS_IMPLEMENTED,
        confidence=0.88,
        raw_content="""# Dog Breed CNN 图像分类

基于 PyTorch 的狗品种分类深度学习项目。

## 技术栈
- PyTorch + torchvision
- ResNet-50 迁移学习
- 数据增强（augmentation）
- Jupyter Notebook 实验记录

## 核心能力
- CNN 模型搭建与训练
- 迁移学习应用
- 数据预处理和增强 pipeline
- 模型评估（accuracy、confusion matrix）
""",
        metadata={
            "source_url": "https://github.com/yfn-1116/dog-breed-cnn",
            "tags": ["cv", "pytorch", "cnn", "deep-learning", "classification"],
            "stars": 0,
            "language": "Python",
        },
    )
