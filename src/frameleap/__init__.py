"""
FrameLeap - 个人动态漫生成器

快速开始:
    from frameleap import generate

    result = generate("一个少年在雨夜中遇到了神秘少女")
    if result.success:
        print(f"视频已生成: {result.video_path}")
"""

__version__ = "0.1.0"

from frameleap.config import config, Config
from frameleap.generator import Generator, generate
from frameleap.models import GenerationResult

__all__ = [
    "config",
    "Config",
    "Generator",
    "generate",
    "GenerationResult",
    "__version__",
]
