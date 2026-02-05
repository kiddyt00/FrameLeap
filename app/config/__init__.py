"""
FrameLeap 个人配置

单用户版本，简化配置管理

支持：
- Pydantic 验证
- 环境变量覆盖
- 配置文件保存/加载
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

try:
    from pydantic import BaseModel, Field, field_validator
    from pydantic_settings import BaseSettings
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    # 回退到dataclass
    BaseModel = object  # type: ignore


# =============================================================================
# 视频配置
# =============================================================================

class VideoConfig:
    """视频配置

    Attributes:
        width: 视频宽度（像素）
        height: 视频高度（像素）
        fps: 帧率
    """

    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
    ):
        self.width = width
        self.height = height
        self.fps = fps

    @classmethod
    def from_preset(cls, preset: str) -> "VideoConfig":
        """从预设创建配置

        Args:
            preset: 预设名称
                - 1080p: 1920x1080, 30fps
                - 1080p_v: 1080x1920, 30fps (竖屏)
                - 720p: 1280x720, 30fps
                - 4k: 3840x2160, 30fps
                - cinema: 2560x1080, 24fps

        Returns:
            视频配置对象

        Raises:
            ValueError: 未知预设
        """
        presets = {
            "1080p": (1920, 1080, 30),
            "1080p_v": (1080, 1920, 30),
            "720p": (1280, 720, 30),
            "4k": (3840, 2160, 30),
            "cinema": (2560, 1080, 24),
        }
        if preset not in presets:
            raise ValueError(
                f"未知预设: {preset}. "
                f"可用预设: {', '.join(presets.keys())}"
            )
        w, h, f = presets[preset]
        return cls(width=w, height=h, fps=f)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
        }


# =============================================================================
# 风格配置
# =============================================================================

class StyleConfig:
    """风格配置

    Attributes:
        art_style: 艺术风格
        color_tone: 色调
        line_strength: 线条强度 (0-100)
    """

    # 支持的艺术风格
    ART_STYLES = [
        "anime",      # 日式动漫
        "manhwa",     # 韩漫
        "manhua",     # 国漫
        "watercolor", # 水彩
        "oil",        # 油画
        "sketch",     # 素描
        "flat",       # 扁平
    ]

    COLOR_TONES = [
        "bright",    # 明亮
        "normal",    # 正常
        "dark",      # 暗色
        "cool",      # 冷色
        "warm",      # 暖色
    ]

    def __init__(
        self,
        art_style: str = "anime",
        color_tone: str = "normal",
        line_strength: int = 70,
    ):
        self.art_style = art_style
        self.color_tone = color_tone
        self.line_strength = max(0, min(100, line_strength))

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "art_style": self.art_style,
            "color_tone": self.color_tone,
            "line_strength": self.line_strength,
        }


# =============================================================================
# API配置
# =============================================================================

class APIConfig:
    """API配置

    支持从环境变量读取敏感信息

    Attributes:
        llm_provider: LLM提供商
        llm_api_key: LLM API密钥
        llm_base_url: LLM API基础URL
        llm_model: LLM模型名称
        image_provider: 图像提供商
        image_api_key: 图像API密钥
        image_base_url: 图像API基础URL
        tts_provider: TTS提供商
        tts_api_key: TTS API密钥
    """

    def __init__(
        self,
        llm_provider: str = "deepseek",
        llm_api_key: str | None = None,
        llm_base_url: str | None = None,
        llm_model: str = "deepseek-chat",
        image_provider: str = "qwen_image",
        image_api_key: str | None = None,
        image_base_url: str | None = None,
        tts_provider: str = "qwen",
        tts_api_key: str | None = None,
    ):
        # 优先从环境变量读取
        self.llm_provider = os.getenv("FRAMELEAP_LLM_PROVIDER", llm_provider)
        self.llm_api_key = llm_api_key or os.getenv("FRAMELEAP_LLM_API_KEY")
        self.llm_base_url = llm_base_url or os.getenv("FRAMELEAP_LLM_BASE_URL")
        self.llm_model = os.getenv("FRAMELEAP_LLM_MODEL", llm_model)

        self.image_provider = os.getenv("FRAMELEAP_IMAGE_PROVIDER", image_provider)
        # 图像API密钥默认复用LLM的API密钥（通义万相与通义千问共用密钥）
        self.image_api_key = image_api_key or os.getenv("FRAMELEAP_IMAGE_API_KEY") or self.llm_api_key
        self.image_base_url = image_base_url or os.getenv("FRAMELEAP_IMAGE_BASE_URL")

        self.tts_provider = os.getenv("FRAMELEAP_TTS_PROVIDER", tts_provider)
        # TTS API密钥默认复用LLM的API密钥（因为同一服务商通常共用密钥）
        self.tts_api_key = tts_api_key or os.getenv("FRAMELEAP_TTS_API_KEY") or self.llm_api_key

    def to_dict(self) -> dict[str, Any]:
        """转换为字典（隐藏敏感信息）"""
        return {
            "llm_provider": self.llm_provider,
            "llm_api_key": "***" if self.llm_api_key else None,
            "llm_base_url": self.llm_base_url,
            "llm_model": self.llm_model,
            "image_provider": self.image_provider,
            "image_api_key": "***" if self.image_api_key else None,
            "image_base_url": self.image_base_url,
            "tts_provider": self.tts_provider,
            "tts_api_key": "***" if self.tts_api_key else None,
        }

    def validate(self) -> list[str]:
        """验证配置

        Returns:
            错误信息列表，空列表表示验证通过
        """
        errors = []

        if self.llm_provider and not self.llm_api_key:
            errors.append(f"LLM API密钥未设置 (provider: {self.llm_provider})")

        if self.image_provider and not self.image_api_key:
            errors.append(f"图像API密钥未设置 (provider: {self.image_provider})")

        return errors


# =============================================================================
# 路径配置
# =============================================================================

class PathConfig:
    """路径配置

    Attributes:
        work_dir: 工作目录（输出文件）
        temp_dir: 临时文件目录
        cache_dir: 缓存目录
        model_dir: 模型文件目录
    """

    def __init__(
        self,
        work_dir: Path | None = None,
        temp_dir: Path | None = None,
        cache_dir: Path | None = None,
        model_dir: Path | None = None,
    ):
        # 默认使用项目目录
        # 获取app/config/__init__.py所在的项目根目录
        import inspect
        config_file = Path(inspect.getfile(PathConfig))
        project_root = config_file.parent.parent.parent  # 从app/config/回到项目根目录

        self.work_dir = Path(work_dir or project_root / "output")
        self.temp_dir = Path(temp_dir or project_root / "temp")
        self.cache_dir = Path(cache_dir or project_root / "cache")
        self.model_dir = Path(model_dir or project_root / "models")

        # 创建目录
        self._create_directories()

    def _create_directories(self) -> None:
        """创建所有目录"""
        for p in [self.work_dir, self.temp_dir, self.cache_dir, self.model_dir]:
            p.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> dict[str, str]:
        """转换为字典"""
        return {
            "work_dir": str(self.work_dir),
            "temp_dir": str(self.temp_dir),
            "cache_dir": str(self.cache_dir),
            "model_dir": str(self.model_dir),
        }


# =============================================================================
# 总配置
# =============================================================================

class Config:
    """总配置

    Attributes:
        video: 视频配置
        style: 风格配置
        api: API配置
        paths: 路径配置
        max_workers: 最大工作线程数
        debug: 调试模式
    """

    def __init__(
        self,
        video: VideoConfig | None = None,
        style: StyleConfig | None = None,
        api: APIConfig | None = None,
        paths: PathConfig | None = None,
        max_workers: int = 4,
        debug: bool = False,
    ):
        self.video = video or VideoConfig()
        self.style = style or StyleConfig()
        self.api = api or APIConfig()
        self.paths = paths or PathConfig()
        self.max_workers = max_workers
        self.debug = debug

    @classmethod
    def load(cls) -> "Config":
        """从配置文件加载

        优先级：项目目录 config.json > 用户目录 ~/.frameleap/config.json > 默认配置

        Returns:
            配置对象

        Examples:
            >>> config = Config.load()
        """
        # 检查多个配置文件位置
        config_files = [
            # 当前项目目录下的 config.json
            Path(__file__).parent.parent.parent / "config.json",
            # 用户主目录下的配置
            Path.home() / ".frameleap" / "config.json",
        ]

        for config_file in config_files:
            if config_file.exists():
                try:
                    with open(config_file, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    print(f"从配置文件加载: {config_file}")

                    # 从字典创建配置
                    return cls(
                        video=VideoConfig(**data.get("video", {})),
                        style=StyleConfig(**data.get("style", {})),
                        api=APIConfig(**data.get("api", {})),
                        paths=PathConfig(**data.get("paths", {})),
                        max_workers=data.get("max_workers", 4),
                        debug=data.get("debug", False),
                    )
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"配置文件解析失败 ({config_file}): {e}，使用默认配置")
                    continue

        # 没有找到配置文件，使用默认配置
        return cls()

    def save(self) -> None:
        """保存到配置文件

        Examples:
            >>> config = Config()
            >>> config.save()
        """
        config_file = Path.home() / ".frameleap" / "config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "video": self.video.to_dict(),
            "style": self.style.to_dict(),
            "api": self.api.to_dict(),
            "paths": self.paths.to_dict(),
            "max_workers": self.max_workers,
            "debug": self.debug,
        }

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def validate(self) -> list[str]:
        """验证配置

        Returns:
            错误信息列表，空列表表示验证通过
        """
        errors = []

        # 验证API配置
        errors.extend(self.api.validate())

        # 验证视频尺寸
        if not (0 < self.video.width <= 7680):
            errors.append(f"无效的视频宽度: {self.video.width}")
        if not (0 < self.video.height <= 4320):
            errors.append(f"无效的视频高度: {self.video.height}")
        if self.video.fps not in [24, 25, 30, 50, 60]:
            errors.append(f"无效的帧率: {self.video.fps}")

        # 验证风格
        if self.style.art_style not in StyleConfig.ART_STYLES:
            errors.append(
                f"无效的艺术风格: {self.style.art_style}. "
                f"可用: {', '.join(StyleConfig.ART_STYLES)}"
            )

        return errors

    @classmethod
    def quick_setup(
        cls,
        llm_api_key: str | None = None,
        image_api_key: str | None = None,
        **kwargs
    ) -> "Config":
        """快速设置配置

        Args:
            llm_api_key: LLM API密钥
            image_api_key: 图像API密钥
            **kwargs: 其他配置参数

        Returns:
            配置对象

        Examples:
            >>> config = Config.quick_setup(
            ...     llm_api_key="sk-xxx",
            ...     art_style="manhwa"
            ... )
            >>> config.save()
        """
        config = cls()

        if llm_api_key:
            config.api.llm_api_key = llm_api_key
        if image_api_key:
            config.api.image_api_key = image_api_key

        # 应用其他配置
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
            elif hasattr(config.style, key):
                setattr(config.style, key, value)
            elif hasattr(config.video, key):
                setattr(config.video, key, value)

        return config


# =============================================================================
# 全局配置实例
# =============================================================================

config = Config.load()


__all__ = [
    "VideoConfig",
    "StyleConfig",
    "APIConfig",
    "PathConfig",
    "Config",
    "config",
]
