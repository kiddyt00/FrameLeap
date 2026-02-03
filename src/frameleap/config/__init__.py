"""
配置管理模块

管理系统配置、参数设置、环境变量等
"""

from typing import Optional
from pathlib import Path
from dataclasses import dataclass, field
import os
import yaml


@dataclass
class VideoConfig:
    """视频配置"""

    width: int = 1920
    height: int = 1080
    fps: int = 30
    duration: Optional[int] = None  # 目标时长（秒），None表示自动计算
    aspect_ratio: str = "16:9"  # 16:9, 9:16, 4:3, 21:9, 1:1

    @property
    def resolution(self) -> str:
        return f"{self.width}x{self.height}"

    @classmethod
    def from_preset(cls, preset: str) -> "VideoConfig":
        """从预设创建配置"""
        presets = {
            "1080p": (1920, 1080, 30),
            "1080p_vertical": (1080, 1920, 30),
            "720p": (1280, 720, 30),
            "4k": (3840, 2160, 30),
            "cinema": (2560, 1080, 24),
            "square": (1080, 1080, 30),
        }
        if preset not in presets:
            raise ValueError(f"Unknown preset: {preset}")
        width, height, fps = presets[preset]
        return cls(width=width, height=height, fps=fps)


@dataclass
class StyleConfig:
    """风格配置"""

    # 绘画风格
    art_style: str = "anime"  # anime, comic, manhwa, manhua, watercolor, oil, etc.
    rendering_style: str = "2d"  # 2d, 2.5d, 3d, mixed

    # 时代风格
    era_style: Optional[str] = None  # ancient_chinese, japanese, medieval, cyberpunk, etc.

    # 题材风格
    genre_style: Optional[str] = None  # school, fantasy, scifi, etc.

    # 色彩基调
    color_tone: str = "normal"  # bright, normal, dark, cool, warm, vintage

    # 线稿强度
    line_strength: int = 70  # 0-100

    # 阴影类型
    shadow_type: str = "normal"  # none, simple, detailed, cartoon


@dataclass
class LLMConfig:
    """语言模型配置"""

    provider: str = "openai"  # openai, anthropic, local
    model: str = "gpt-4"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4000

    def __post_init__(self):
        if self.api_key is None:
            self.api_key = os.getenv("LLM_API_KEY")


@dataclass
class ImageGenConfig:
    """图像生成配置"""

    provider: str = "sdxl"  # sdxl, sd3, flux, midjourney, dalle
    model: str = "sd_xl_base_1.0"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    steps: int = 30
    cfg_scale: float = 7.5
    width: int = 1024
    height: int = 1024
    seed: Optional[int] = None

    # 角色一致性
    use_lora: bool = True
    lora_path: Optional[str] = None
    use_controlnet: bool = True
    use_ip_adapter: bool = True

    def __post_init__(self):
        if self.api_key is None:
            self.api_key = os.getenv("IMAGE_GEN_API_KEY")


@dataclass
class AudioConfig:
    """音频配置"""

    # TTS配置
    tts_provider: str = "azure"  # azure, google, fish, elevenlabs
    tts_api_key: Optional[str] = None

    # 音效配置
    sfx_provider: str = "audioldm"  # audioldm, library
    sfx_library_path: Optional[str] = None

    # BGM配置
    bgm_provider: str = "library"  # suno, udio, library
    bgm_library_path: Optional[str] = None

    def __post_init__(self):
        if self.tts_api_key is None:
            self.tts_api_key = os.getenv("TTS_API_KEY")


@dataclass
class PathConfig:
    """路径配置"""

    # 工作目录
    work_dir: Path = field(default_factory=lambda: Path.cwd() / "output")
    temp_dir: Path = field(default_factory=lambda: Path.cwd() / "temp")
    cache_dir: Path = field(default_factory=lambda: Path.cwd() / "cache")

    # 模型路径
    model_dir: Path = field(default_factory=lambda: Path.cwd() / "models")
    lora_dir: Path = field(default_factory=lambda: Path.cwd() / "models" / "loras")

    # 输出路径
    output_dir: Path = field(default_factory=lambda: Path.cwd() / "output")

    def __post_init__(self):
        # 确保目录存在
        for path in [self.work_dir, self.temp_dir, self.cache_dir, self.model_dir, self.lora_dir, self.output_dir]:
            path.mkdir(parents=True, exist_ok=True)


@dataclass
class Settings:
    """全局设置"""

    # 视频配置
    video: VideoConfig = field(default_factory=VideoConfig)

    # 风格配置
    style: StyleConfig = field(default_factory=StyleConfig)

    # LLM配置
    llm: LLMConfig = field(default_factory=LLMConfig)

    # 图像生成配置
    image_gen: ImageGenConfig = field(default_factory=ImageGenConfig)

    # 音频配置
    audio: AudioConfig = field(default_factory=AudioConfig)

    # 路径配置
    paths: PathConfig = field(default_factory=PathConfig)

    # 并发配置
    max_workers: int = 4
    batch_size: int = 4

    # 调试配置
    debug: bool = False
    log_level: str = "INFO"

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Settings":
        """从YAML文件加载配置"""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # 递归创建配置对象
        def create_config(config_class, data):
            if data is None:
                return config_class()
            fields = {}
            for field_name, field_def in config_class.__dataclass_fields__.items():
                if field_name in data:
                    field_type = field_def.type
                    field_value = data[field_name]
                    # 嵌套配置类
                    if hasattr(field_type, "__dataclass_fields__"):
                        fields[field_name] = create_config(field_type, field_value)
                    else:
                        fields[field_name] = field_value
                else:
                    # 使用默认值
                    if field_def.default_factory is not dataclasses.MISSING:
                        fields[field_name] = field_def.default_factory()
                    elif field_def.default is not dataclasses.MISSING:
                        fields[field_name] = field_def.default
            return config_class(**fields)

        return create_config(cls, data)

    def to_yaml(self, path: str | Path):
        """保存配置到YAML文件"""
        from dataclasses import asdict

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(asdict(self), f, allow_unicode=True, default_flow_style=False)


# 默认配置实例
default_settings = Settings()
