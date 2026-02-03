"""
工具类模块

提供各种辅助工具函数
"""

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Optional, Callable, TypeVar
from functools import wraps
from contextlib import contextmanager

import logging


# =============================================================================
# 日志配置
# =============================================================================

def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """配置日志系统"""
    if format_string is None:
        format_string = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"

    # 配置根日志器
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger = logging.getLogger("frameleap")

    # 添加文件处理器
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(format_string))
        logger.addHandler(file_handler)

    return logger


# =============================================================================
# 性能计时
# =============================================================================

@contextmanager
def timer(name: str, logger: Optional[logging.Logger] = None):
    """性能计时上下文管理器"""
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    message = f"{name} took {elapsed:.2f} seconds"
    if logger:
        logger.info(message)
    else:
        print(message)


def timing_decorator(func: Callable) -> Callable:
    """性能计时装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        func_name = func.__qualname__
        print(f"{func_name} took {elapsed:.2f} seconds")
        return result
    return wrapper


# =============================================================================
# 文件操作工具
# =============================================================================

def ensure_dir(path: Path | str) -> Path:
    """确保目录存在"""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_hash(content: str | bytes | Path) -> str:
    """获取内容的哈希值"""
    if isinstance(content, Path):
        content = content.read_bytes()
    elif isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.md5(content).hexdigest()


def save_json(data: Any, path: Path | str, indent: int = 2):
    """保存JSON文件"""
    p = Path(path)
    ensure_dir(p.parent)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def load_json(path: Path | str) -> Any:
    """加载JSON文件"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_unique_path(base_path: Path | str, suffix: str = "") -> Path:
    """获取唯一文件路径"""
    p = Path(base_path)
    counter = 0
    while True:
        if counter == 0:
            path = p.with_suffix(suffix) if suffix else p
        else:
            stem = p.stem
            parent = p.parent
            ext = p.suffix
            path = parent / f"{stem}_{counter}{ext}"

        if not path.exists():
            return path
        counter += 1


# =============================================================================
# 字符串工具
# =============================================================================

def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def clean_filename(filename: str) -> str:
    """清理文件名，移除非法字符"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    return filename.strip()


# =============================================================================
# 提示词构建工具
# =============================================================================

def build_prompt(
    subject: str,
    style: str = "",
    quality_tags: list[str] | None = None,
    negative_tags: list[str] | None = None,
    **kwargs
) -> str:
    """
    构建图像生成提示词

    Args:
        subject: 主体描述
        style: 风格描述
        quality_tags: 质量标签列表
        negative_tags: 负面标签列表
        **kwargs: 其他参数

    Returns:
        完整提示词
    """
    parts = []

    # 主体
    if subject:
        parts.append(subject)

    # 风格
    if style:
        parts.append(style)

    # 质量标签
    if quality_tags:
        parts.extend(quality_tags)
    else:
        # 默认质量标签
        parts.extend(["masterpiece", "best quality", "highly detailed"])

    return ", ".join(parts)


def build_negative_prompt(
    negative_tags: list[str] | None = None
) -> str:
    """
    构建负面提示词

    Args:
        negative_tags: 负面标签列表

    Returns:
        负面提示词
    """
    if negative_tags is None:
        # 默认负面标签
        negative_tags = [
            "low quality",
            "worst quality",
            "blurry",
            "ugly",
            "deformed",
            "disfigured",
            "bad anatomy",
            "extra limbs",
            "missing limbs",
            "watermark",
            "text",
        ]
    return ", ".join(negative_tags)


# =============================================================================
# 验证工具
# =============================================================================

def validate_video_size(width: int, height: int) -> bool:
    """验证视频尺寸"""
    return width > 0 and height > 0 and width % 2 == 0 and height % 2 == 0


def validate_fps(fps: int) -> bool:
    """验证帧率"""
    return fps in [24, 25, 30, 50, 60]


def validate_duration(duration: float) -> bool:
    """验证时长"""
    return duration > 0


# =============================================================================
# 异常类
# =============================================================================

class FrameLeapError(Exception):
    """FrameLeap基础异常"""
    pass


class ConfigError(FrameLeapError):
    """配置错误"""
    pass


class InputValidationError(FrameLeapError):
    """输入验证错误"""
    pass


class GenerationError(FrameLeapError):
    """生成错误"""
    pass


class APIError(FrameLeapError):
    """API调用错误"""
    pass


class FileNotFoundError(FrameLeapError):
    """文件未找到错误"""
    pass
