"""
FrameLeap - AI驱动的动态漫自动生成系统

FrameLeap是一个端到端的动态漫生成解决方案，从用户的一句话或短文输入出发，
自动完成剧本创作、角色设计、画面生成、分镜编排、动画制作、音频合成等全流程。
"""

__version__ = "0.1.0"
__author__ = "FrameLeap Team"

from frameleap.generator import FrameLeapGenerator
from frameleap.config import Settings
from frameleap.models import (
    ScriptData,
    SceneData,
    ShotData,
    CharacterData,
    AudioData,
    VideoConfig,
    StyleConfig,
)

__all__ = [
    "FrameLeapGenerator",
    "Settings",
    "ScriptData",
    "SceneData",
    "ShotData",
    "CharacterData",
    "AudioData",
    "VideoConfig",
    "StyleConfig",
    "__version__",
]
