"""
FrameLeap 个人配置

单用户版本，简化配置管理
"""

import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class VideoConfig:
    """视频配置"""
    width: int = 1920
    height: int = 1080
    fps: int = 30

    @classmethod
    def from_preset(cls, preset: str) -> "VideoConfig":
        """从预设创建"""
        presets = {
            "1080p": (1920, 1080, 30),
            "1080p_v": (1080, 1920, 30),
            "720p": (1280, 720, 30),
            "4k": (3840, 2160, 30),
            "cinema": (2560, 1080, 24),
        }
        if preset not in presets:
            raise ValueError(f"未知预设: {preset}")
        w, h, f = presets[preset]
        return cls(width=w, height=h, fps=f)


@dataclass
class StyleConfig:
    """风格配置"""
    art_style: str = "anime"  # anime, manhwa, manhua, watercolor, oil, etc.
    color_tone: str = "normal"  # bright, normal, dark, cool, warm
    line_strength: int = 70  # 0-100


@dataclass
class APIConfig:
    """API配置"""
    # LLM
    llm_provider: str = "openai"  # openai, anthropic, deepseek
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_model: str = "gpt-4"

    # 图像生成
    image_provider: str = "sdxl"  # sdxl, flux, midjourney
    image_api_key: Optional[str] = None
    image_base_url: Optional[str] = None

    # TTS
    tts_provider: str = "azure"  # azure, fish, elevenlabs
    tts_api_key: Optional[str] = None


@dataclass
class PathConfig:
    """路径配置"""
    work_dir: Path = field(default_factory=lambda: Path.home() / "FrameLeap" / "output")
    temp_dir: Path = field(default_factory=lambda: Path.home() / "FrameLeap" / "temp")
    cache_dir: Path = field(default_factory=lambda: Path.home() / "FrameLeap" / "cache")
    model_dir: Path = field(default_factory=lambda: Path.home() / "FrameLeap" / "models")

    def __post_init__(self):
        for p in [self.work_dir, self.temp_dir, self.cache_dir, self.model_dir]:
            p.mkdir(parents=True, exist_ok=True)


@dataclass
class Config:
    """总配置"""
    video: VideoConfig = field(default_factory=VideoConfig)
    style: StyleConfig = field(default_factory=StyleConfig)
    api: APIConfig = field(default_factory=APIConfig)
    paths: PathConfig = field(default_factory=PathConfig)

    # 性能
    max_workers: int = 4

    # 调试
    debug: bool = False

    @classmethod
    def load(cls) -> "Config":
        """从配置文件加载"""
        config_file = Path.home() / ".frameleap" / "config.json"
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls(**data)
        return cls()

    def save(self):
        """保存到配置文件"""
        config_file = Path.home() / ".frameleap" / "config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        # 转换Path为字符串
        data = asdict(self)
        data["paths"] = {k: str(v) for k, v in data["paths"].items()}

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def quick_setup(cls, **kwargs) -> "Config":
        """快速设置配置"""
        config = cls()
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        config.save()
        return config


# 全局配置实例
config = Config.load()
