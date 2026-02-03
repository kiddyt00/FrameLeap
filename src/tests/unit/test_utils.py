"""
工具模块单元测试
"""

import pytest
import json
import tempfile
from pathlib import Path

from frameleap.utils import (
    # 文件操作
    ensure_dir,
    get_hash,
    save_json,
    load_json,
    get_unique_path,
    # 字符串工具
    truncate,
    clean_filename,
    # 提示词构建
    build_prompt,
    build_negative_prompt,
    # 验证工具
    validate_video_size,
    validate_fps,
    validate_duration,
    # 异常
    FrameLeapError,
    ConfigError,
    InputValidationError,
    GenerationError,
)


class TestFileOperations:
    """测试文件操作工具"""

    def test_ensure_dir(self, temp_dir):
        """测试确保目录存在"""
        new_dir = temp_dir / "new" / "nested" / "dir"
        result = ensure_dir(new_dir)
        assert result.exists()
        assert result.is_dir()

    def test_get_hash_string(self):
        """测试获取字符串哈希"""
        hash1 = get_hash("test content")
        hash2 = get_hash("test content")
        hash3 = get_hash("different content")

        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 32  # MD5哈希长度

    def test_get_hash_file(self, temp_dir):
        """测试获取文件哈希"""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        hash1 = get_hash(test_file)
        hash2 = get_hash("test content")

        assert hash1 == hash2

    def test_save_and_load_json(self, temp_dir):
        """测试保存和加载JSON"""
        data = {"key": "value", "number": 123}
        json_path = temp_dir / "test.json"

        save_json(data, json_path)
        assert json_path.exists()

        loaded = load_json(json_path)
        assert loaded == data

    def test_get_unique_path(self, temp_dir):
        """测试获取唯一路径"""
        base_path = temp_dir / "test.txt"

        # 第一次调用应该返回原始路径
        path1 = get_unique_path(base_path)
        assert path1 == base_path

        # 创建文件后再次调用
        path1.write_text("content")
        path2 = get_unique_path(base_path)
        assert path2 == temp_dir / "test_1.txt"

        # 再创建文件
        path2.write_text("content")
        path3 = get_unique_path(base_path)
        assert path3 == temp_dir / "test_2.txt"


class TestStringUtils:
    """测试字符串工具"""

    def test_truncate_no_truncation(self):
        """测试不截断"""
        text = "short text"
        result = truncate(text, 20)
        assert result == "short text"

    def test_truncate_with_truncation(self):
        """测试截断"""
        text = "this is a very long text that should be truncated"
        result = truncate(text, 20)
        assert len(result) == 20
        assert result.endswith("...")

    def test_clean_filename(self):
        """测试清理文件名"""
        filename = 'file<>:"/\\|?*name.txt'
        result = clean_filename(filename)
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert "/" not in result
        assert "\\" not in result
        assert "|" not in result
        assert "?" not in result
        assert "*" not in result
        assert result == "file______name.txt"


class TestPromptBuilding:
    """测试提示词构建工具"""

    def test_build_prompt_basic(self):
        """测试基础提示词构建"""
        prompt = build_prompt(
            subject="a beautiful girl",
            style="anime",
        )
        assert "a beautiful girl" in prompt
        assert "anime" in prompt
        assert "masterpiece" in prompt
        assert "best quality" in prompt

    def test_build_prompt_with_quality_tags(self):
        """测试带质量标签的提示词构建"""
        prompt = build_prompt(
            subject="a cat",
            quality_tags=["high quality", "detailed"],
        )
        assert "a cat" in prompt
        assert "high quality" in prompt
        assert "detailed" in prompt

    def test_build_negative_prompt_default(self):
        """测试默认负面提示词"""
        prompt = build_negative_prompt()
        assert "low quality" in prompt
        assert "worst quality" in prompt
        assert "blurry" in prompt
        assert "ugly" in prompt

    def test_build_negative_prompt_custom(self):
        """测试自定义负面提示词"""
        prompt = build_negative_prompt(
            negative_tags=["custom", "negative", "tags"]
        )
        assert "custom" in prompt
        assert "negative" in prompt
        assert "tags" in prompt


class TestValidationUtils:
    """测试验证工具"""

    def test_validate_video_size_valid(self):
        """测试有效视频尺寸"""
        assert validate_video_size(1920, 1080) is True
        assert validate_video_size(1280, 720) is True
        assert validate_video_size(1080, 1920) is True

    def test_validate_video_size_invalid(self):
        """测试无效视频尺寸"""
        assert validate_video_size(0, 1080) is False
        assert validate_video_size(1921, 1080) is False  # 奇数宽度
        assert validate_video_size(1920, 1081) is False  # 奇数高度

    def test_validate_fps_valid(self):
        """测试有效帧率"""
        assert validate_fps(24) is True
        assert validate_fps(30) is True
        assert validate_fps(60) is True

    def test_validate_fps_invalid(self):
        """测试无效帧率"""
        assert validate_fps(15) is False
        assert validate_fps(25) is False
        assert validate_fps(100) is False

    def test_validate_duration_valid(self):
        """测试有效时长"""
        assert validate_duration(10.0) is True
        assert validate_duration(0.1) is True

    def test_validate_duration_invalid(self):
        """测试无效时长"""
        assert validate_duration(0) is False
        assert validate_duration(-1.0) is False


class TestExceptions:
    """测试异常类"""

    def test_frame_leap_error(self):
        """测试基础异常"""
        with pytest.raises(FrameLeapError):
            raise FrameLeapError("Test error")

    def test_config_error(self):
        """测试配置错误"""
        with pytest.raises(ConfigError):
            raise ConfigError("Config error")

    def test_input_validation_error(self):
        """测试输入验证错误"""
        with pytest.raises(InputValidationError):
            raise InputValidationError("Invalid input")

    def test_generation_error(self):
        """测试生成错误"""
        with pytest.raises(GenerationError):
            raise GenerationError("Generation failed")
