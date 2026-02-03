"""
工具类模块

提供各种辅助工具函数
"""

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any
from functools import wraps
from contextlib import contextmanager


# 导出制品存储
from app.utils.artifact_store import ArtifactStore


# =============================================================================
# 日志配置
# =============================================================================

def setup_logging(
    level: str = "INFO",
    log_file: str | None = None,
    format_string: str | None = None,
) -> logging.Logger:
    """配置日志系统

    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        log_file: 日志文件路径
        format_string: 日志格式字符串

    Returns:
        配置好的日志记录器
    """
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
def timer(name: str, logger: logging.Logger | None = None):
    """性能计时上下文管理器

    Args:
        name: 计时名称
        logger: 日志记录器

    Examples:
        >>> with timer("数据加载"):
        ...     data = load_large_file()
    """
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    message = f"{name} took {elapsed:.2f} seconds"
    if logger:
        logger.info(message)
    else:
        print(message)


def timing_decorator(func: callable) -> callable:
    """性能计时装饰器

    Args:
        func: 要计时的函数

    Returns:
        包装后的函数

    Examples:
        >>> @timing_decorator
        >>> def slow_function():
        ...     time.sleep(1)
    """
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
    """确保目录存在

    Args:
        path: 目录路径

    Returns:
        Path对象
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_hash(content: str | bytes | Path) -> str:
    """获取内容的哈希值

    Args:
        content: 字符串、字节或文件路径

    Returns:
        MD5哈希值（十六进制）
    """
    if isinstance(content, Path):
        content = content.read_bytes()
    elif isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.md5(content).hexdigest()


def save_json(data: Any, path: Path | str, indent: int = 2) -> None:
    """保存JSON文件

    Args:
        data: 要保存的数据
        path: 文件路径
        indent: 缩进空格数
    """
    p = Path(path)
    ensure_dir(p.parent)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def load_json(path: Path | str) -> Any:
    """加载JSON文件

    Args:
        path: 文件路径

    Returns:
        解析后的数据
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_unique_path(base_path: Path | str, suffix: str = "") -> Path:
    """获取唯一文件路径

    如果文件存在，自动添加数字后缀

    Args:
        base_path: 基础路径
        suffix: 文件后缀

    Returns:
        唯一的文件路径

    Examples:
        >>> get_unique_path("output.png")
        Path('output_1.png')
    """
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
    """截断文本

    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后缀

    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def clean_filename(filename: str) -> str:
    """清理文件名，移除非法字符

    Args:
        filename: 原始文件名

    Returns:
        清理后的文件名
    """
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
    **kwargs,
) -> str:
    """
    构建图像生成提示词

    Args:
        subject: 主体描述
        style: 风格描述
        quality_tags: 质量标签列表
        negative_tags: 负面标签列表（未使用）
        **kwargs: 其他参数

    Returns:
        完整提示词

    Examples:
        >>> build_prompt("一只猫", "anime风格")
        '一只猫, anime风格, masterpiece, best quality, highly detailed'
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
    negative_tags: list[str] | None = None,
) -> str:
    """
    构建负面提示词

    Args:
        negative_tags: 负面标签列表

    Returns:
        负面提示词

    Examples:
        >>> build_negative_prompt(["blurry", "ugly"])
        'blurry, ugly'
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
    """验证视频尺寸

    Args:
        width: 宽度
        height: 高度

    Returns:
        是否有效
    """
    return width > 0 and height > 0 and width % 2 == 0 and height % 2 == 0


def validate_fps(fps: int) -> bool:
    """验证帧率

    Args:
        fps: 帧率

    Returns:
        是否有效
    """
    return fps in [24, 25, 30, 50, 60]


def validate_duration(duration: float) -> bool:
    """验证时长

    Args:
        duration: 时长（秒）

    Returns:
        是否有效
    """
    return duration > 0


__all__ = [
    "setup_logging",
    "timer",
    "timing_decorator",
    "ensure_dir",
    "get_hash",
    "save_json",
    "load_json",
    "get_unique_path",
    "truncate",
    "clean_filename",
    "build_prompt",
    "build_negative_prompt",
    "validate_video_size",
    "validate_fps",
    "validate_duration",
]
