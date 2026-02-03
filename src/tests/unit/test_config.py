"""
配置模块单元测试
"""

import pytest
import tempfile
from pathlib import Path

from frameleap.config import (
    Settings,
    VideoConfig,
    StyleConfig,
    LLMConfig,
    ImageGenConfig,
    AudioConfig,
    PathConfig,
)


class TestVideoConfig:
    """测试VideoConfig"""

    def test_default_config(self):
        """测试默认配置"""
        config = VideoConfig()
        assert config.width == 1920
        assert config.height == 1080
        assert config.fps == 30
        assert config.resolution == "1920x1080"

    def test_preset_1080p(self):
        """测试1080p预设"""
        config = VideoConfig.from_preset("1080p")
        assert config.width == 1920
        assert config.height == 1080
        assert config.fps == 30

    def test_preset_vertical(self):
        """测试竖屏预设"""
        config = VideoConfig.from_preset("1080p_vertical")
        assert config.width == 1080
        assert config.height == 1920

    def test_preset_4k(self):
        """测试4K预设"""
        config = VideoConfig.from_preset("4k")
        assert config.width == 3840
        assert config.height == 2160

    def test_preset_invalid(self):
        """测试无效预设"""
        with pytest.raises(ValueError, match="Unknown preset"):
            VideoConfig.from_preset("invalid_preset")

    def test_resolution_property(self):
        """测试resolution属性"""
        config = VideoConfig(width=1280, height=720)
        assert config.resolution == "1280x720"


class TestStyleConfig:
    """测试StyleConfig"""

    def test_default_config(self):
        """测试默认配置"""
        config = StyleConfig()
        assert config.art_style == "anime"
        assert config.rendering_style == "2d"
        assert config.color_tone == "normal"

    def test_custom_style(self):
        """测试自定义风格"""
        config = StyleConfig(
            art_style="watercolor",
            rendering_style="2.5d",
            color_tone="warm",
        )
        assert config.art_style == "watercolor"
        assert config.rendering_style == "2.5d"
        assert config.color_tone == "warm"


class TestLLMConfig:
    """测试LLMConfig"""

    def test_default_config(self):
        """测试默认配置"""
        config = LLMConfig()
        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.temperature == 0.7
        assert config.max_tokens == 4000

    def test_custom_provider(self):
        """测试自定义provider"""
        config = LLMConfig(provider="anthropic", model="claude-3")
        assert config.provider == "anthropic"
        assert config.model == "claude-3"


class TestPathConfig:
    """测试PathConfig"""

    def test_default_config(self):
        """测试默认配置"""
        config = PathConfig()
        assert config.work_dir.name == "output"
        assert config.temp_dir.name == "temp"
        assert config.cache_dir.name == "cache"
        assert config.model_dir.name == "models"

    def test_custom_paths(self, temp_dir):
        """测试自定义路径"""
        config = PathConfig(
            work_dir=temp_dir / "work",
            temp_dir=temp_dir / "temp",
        )
        assert config.work_dir == temp_dir / "work"
        assert config.temp_dir == temp_dir / "temp"

    def test_directories_created(self, temp_dir):
        """测试目录自动创建"""
        config = PathConfig(
            work_dir=temp_dir / "new_work",
            temp_dir=temp_dir / "new_temp",
        )
        assert config.work_dir.exists()
        assert config.temp_dir.exists()


class TestSettings:
    """测试Settings"""

    def test_default_settings(self):
        """测试默认设置"""
        settings = Settings()
        assert isinstance(settings.video, VideoConfig)
        assert isinstance(settings.style, StyleConfig)
        assert isinstance(settings.llm, LLMConfig)
        assert isinstance(settings.image_gen, ImageGenConfig)
        assert isinstance(settings.audio, AudioConfig)
        assert isinstance(settings.paths, PathConfig)

    def test_custom_settings(self):
        """测试自定义设置"""
        settings = Settings(
            video=VideoConfig(width=1280, height=720),
            style=StyleConfig(art_style="watercolor"),
        )
        assert settings.video.width == 1280
        assert settings.style.art_style == "watercolor"

    def test_yaml_export(self, temp_dir):
        """测试YAML导出"""
        settings = Settings()
        yaml_path = temp_dir / "config.yaml"

        settings.to_yaml(yaml_path)

        assert yaml_path.exists()

    def test_yaml_import(self, temp_dir):
        """测试YAML导入"""
        # 先导出
        original = Settings(
            video=VideoConfig(width=1280, height=720),
            style=StyleConfig(art_style="watercolor"),
        )
        yaml_path = temp_dir / "config.yaml"
        original.to_yaml(yaml_path)

        # 再导入
        loaded = Settings.from_yaml(yaml_path)

        assert loaded.video.width == 1280
        assert loaded.style.art_style == "watercolor"
