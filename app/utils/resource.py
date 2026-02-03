"""
资源管理模块

提供临时文件自动清理、资源上下文管理器和内存监控
"""

import os
import gc
import logging
import tempfile
from pathlib import Path
from typing import Any, Generator, Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
import weakref

logger = logging.getLogger(__name__)


# =============================================================================
# 配置常量
# =============================================================================

DEFAULT_MAX_CACHE_SIZE = 1024 * 1024 * 1024  # 1GB
DEFAULT_MAX_TEMP_SIZE = 1024 * 1024 * 512  # 512MB
DEFAULT_MAX_MEMORY_USAGE = 0.8  # 80%


# =============================================================================
# 资源统计
# =============================================================================

@dataclass
class ResourceStats:
    """资源使用统计

    Attributes:
        temp_files_count: 临时文件数量
        temp_size_mb: 临时文件总大小（MB）
        cache_files_count: 缓存文件数量
        cache_size_mb: 缓存文件总大小（MB）
        memory_usage_mb: 内存使用量（MB）
        memory_available_mb: 可用内存（MB）
    """
    temp_files_count: int = 0
    temp_size_mb: float = 0.0
    cache_files_count: int = 0
    cache_size_mb: float = 0.0
    memory_usage_mb: float = 0.0
    memory_available_mb: float = 0.0

    @property
    def total_size_mb(self) -> float:
        """总占用空间（MB）"""
        return self.temp_size_mb + self.cache_size_mb

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "temp_files_count": self.temp_files_count,
            "temp_size_mb": round(self.temp_size_mb, 2),
            "cache_files_count": self.cache_files_count,
            "cache_size_mb": round(self.cache_size_mb, 2),
            "total_size_mb": round(self.total_size_mb, 2),
            "memory_usage_mb": round(self.memory_usage_mb, 2),
            "memory_available_mb": round(self.memory_available_mb, 2),
        }


# =============================================================================
# 资源监控器
# =============================================================================

class ResourceMonitor:
    """资源监控器

    监控内存、磁盘和临时文件的使用情况

    Attributes:
        temp_dir: 临时目录
        cache_dir: 缓存目录
        max_temp_size: 最大临时文件大小（字节）
        max_cache_size: 最大缓存大小（字节）
    """

    def __init__(
        self,
        temp_dir: Path,
        cache_dir: Path,
        max_temp_size: int = DEFAULT_MAX_TEMP_SIZE,
        max_cache_size: int = DEFAULT_MAX_CACHE_SIZE,
    ) -> None:
        """初始化资源监控器

        Args:
            temp_dir: 临时目录路径
            cache_dir: 缓存目录路径
            max_temp_size: 最大临时文件大小
            max_cache_size: 最大缓存大小
        """
        self.temp_dir = Path(temp_dir)
        self.cache_dir = Path(cache_dir)
        self.max_temp_size = max_temp_size
        self.max_cache_size = max_cache_size

    def get_stats(self) -> ResourceStats:
        """获取资源统计信息

        Returns:
            资源统计对象
        """
        stats = ResourceStats()

        # 统计临时文件
        if self.temp_dir.exists():
            for file_path in self.temp_dir.rglob("*"):
                if file_path.is_file():
                    stats.temp_files_count += 1
                    stats.temp_size_mb += file_path.stat().st_size / (1024 * 1024)

        # 统计缓存文件
        if self.cache_dir.exists():
            for file_path in self.cache_dir.rglob("*"):
                if file_path.is_file():
                    stats.cache_files_count += 1
                    stats.cache_size_mb += file_path.stat().st_size / (1024 * 1024)

        # 获取内存信息
        try:
            import psutil
            process = psutil.Process()
            mem_info = process.memory_info()
            stats.memory_usage_mb = mem_info.rss / (1024 * 1024)

            # 系统可用内存
            sys_mem = psutil.virtual_memory()
            stats.memory_available_mb = sys_mem.available / (1024 * 1024)
        except ImportError:
            # psutil 不可用时使用简化版本
            import resource
            stats.memory_usage_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024

        return stats

    def check_limits(self) -> dict[str, bool]:
        """检查资源限制

        Returns:
            各项限制检查结果
        """
        stats = self.get_stats()

        return {
            "temp_exceeded": stats.temp_size_mb * 1024 * 1024 > self.max_temp_size,
            "cache_exceeded": stats.cache_size_mb * 1024 * 1024 > self.max_cache_size,
            "memory_high": stats.memory_available_mb < 100,  # 少于100MB
        }

    def cleanup_if_needed(self) -> ResourceStats:
        """根据需要清理资源

        Returns:
            清理后的资源统计
        """
        limits = self.check_limits()

        if limits["temp_exceeded"]:
            logger.warning(f"临时文件超限，清理: {self.temp_dir}")
            self.cleanup_temp()

        if limits["cache_exceeded"]:
            logger.warning(f"缓存超限，清理: {self.cache_dir}")
            self.cleanup_cache()

        if limits["memory_high"]:
            logger.warning("内存不足，触发垃圾回收")
            gc.collect()

        return self.get_stats()

    def cleanup_temp(self) -> int:
        """清理临时文件

        Returns:
            删除的文件数量
        """
        count = 0
        if self.temp_dir.exists():
            for file_path in self.temp_dir.rglob("*"):
                try:
                    if file_path.is_file():
                        file_path.unlink()
                        count += 1
                    elif file_path.is_dir() and not any(file_path.iterdir()):
                        file_path.rmdir()
                except OSError as e:
                    logger.warning(f"清理临时文件失败: {file_path}, {e}")

        logger.info(f"清理临时文件: {count} 个")
        return count

    def cleanup_cache(self) -> int:
        """清理缓存文件

        Returns:
            删除的文件数量
        """
        count = 0
        if self.cache_dir.exists():
            for file_path in self.cache_dir.rglob("*"):
                try:
                    if file_path.is_file():
                        file_path.unlink()
                        count += 1
                except OSError as e:
                    logger.warning(f"清理缓存文件失败: {file_path}, {e}")

        logger.info(f"清理缓存文件: {count} 个")
        return count


# =============================================================================
# 临时文件管理
# =============================================================================

class TempFileManager:
    """临时文件管理器

    自动创建和清理临时文件

    Attributes:
        temp_dir: 临时目录
        prefix: 文件名前缀
        suffix: 文件名后缀
        _files: 已创建的文件列表
    """

    def __init__(
        self,
        temp_dir: Path | None = None,
        prefix: str = "frameleap_",
        suffix: str = "",
    ) -> None:
        """初始化临时文件管理器

        Args:
            temp_dir: 临时目录，None则使用系统默认
            prefix: 文件名前缀
            suffix: 文件名后缀
        """
        if temp_dir is None:
            temp_dir = Path(tempfile.gettempdir())
        self.temp_dir = Path(temp_dir)
        self.prefix = prefix
        self.suffix = suffix
        self._files: list[Path] = []

    def create(
        self,
        content: bytes | None = None,
        name: str | None = None,
    ) -> Path:
        """创建临时文件

        Args:
            content: 文件内容
            name: 文件名（不含扩展名）

        Returns:
            临时文件路径
        """
        if name:
            file_path = self.temp_dir / f"{self.prefix}{name}{self.suffix}"
        else:
            file_path = self.temp_dir / f"{self.prefix}{id(self)}{self.suffix}"

        file_path.parent.mkdir(parents=True, exist_ok=True)

        if content is not None:
            file_path.write_bytes(content)

        self._files.append(file_path)
        return file_path

    def cleanup(self) -> int:
        """清理所有临时文件

        Returns:
            删除的文件数量
        """
        count = 0
        for file_path in self._files:
            try:
                if file_path.exists():
                    file_path.unlink()
                    count += 1
            except OSError as e:
                logger.warning(f"删除临时文件失败: {file_path}, {e}")

        self._files.clear()
        return count

    def __del__(self) -> None:
        """析构时自动清理"""
        self.cleanup()


# =============================================================================
# 资源上下文管理器
# =============================================================================

@contextmanager
def temp_file(
    content: bytes | None = None,
    temp_dir: Path | None = None,
    prefix: str = "frameleap_",
    suffix: str = "",
) -> Generator[Path, None, None]:
    """临时文件上下文管理器

    Args:
        content: 文件内容
        temp_dir: 临时目录
        prefix: 文件名前缀
        suffix: 文件名后缀

    Yields:
        临时文件路径

    Examples:
        >>> with temp_file(b"test data") as f:
        ...     process_file(f)
        # 文件自动删除
    """
    manager = TempFileManager(temp_dir, prefix, suffix)
    file_path = manager.create(content)

    try:
        yield file_path
    finally:
        manager.cleanup()


@contextmanager
def temp_directory(
    prefix: str = "frameleap_",
    temp_dir: Path | None = None,
) -> Generator[Path, None, None]:
    """临时目录上下文管理器

    Args:
        prefix: 目录名前缀
        temp_dir: 父临时目录

    Yields:
        临时目录路径

    Examples:
        >>> with temp_directory() as tmpdir:
        ...     (tmpdir / "file.txt").write_text("test")
        # 目录自动删除
    """
    if temp_dir is None:
        temp_dir = Path(tempfile.gettempdir())

    temp_path = Path(tempfile.mkdtemp(prefix=prefix, dir=temp_dir))

    try:
        yield temp_path
    finally:
        # 清理目录内容
        for item in temp_path.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    # 递归删除子目录
                    import shutil
                    shutil.rmtree(item)
            except OSError as e:
                logger.warning(f"删除失败: {item}, {e}")

        # 删除目录本身
        try:
            temp_path.rmdir()
        except OSError as e:
            logger.warning(f"删除目录失败: {temp_path}, {e}")


@contextmanager
def resource_monitor(
    temp_dir: Path,
    cache_dir: Path,
    cleanup_on_exit: bool = True,
) -> Generator[ResourceMonitor, None, None]:
    """资源监控上下文管理器

    Args:
        temp_dir: 临时目录
        cache_dir: 缓存目录
        cleanup_on_exit: 退出时是否清理

    Yields:
        资源监控器

    Examples:
        >>> with resource_monitor(temp_dir, cache_dir) as monitor:
        ...     stats = monitor.get_stats()
        ...     # 执行操作
        ... # 自动检查并清理
    """
    monitor = ResourceMonitor(temp_dir, cache_dir)

    try:
        yield monitor
    finally:
        if cleanup_on_exit:
            monitor.cleanup_if_needed()


# =============================================================================
# 全局资源跟踪
# =============================================================================

_global_resources: weakref.WeakValueDictionary[object, ResourceMonitor] = (
    weakref.WeakValueDictionary()
)


def register_resource(obj: object, monitor: ResourceMonitor) -> None:
    """注册资源监控器

    Args:
        obj: 要监控的对象
        monitor: 资源监控器
    """
    _global_resources[obj] = monitor


def get_resource_monitor(obj: object) -> ResourceMonitor | None:
    """获取对象的资源监控器

    Args:
        obj: 已注册的对象

    Returns:
        资源监控器，不存在返回None
    """
    return _global_resources.get(obj)


__all__ = [
    "ResourceStats",
    "ResourceMonitor",
    "TempFileManager",
    "temp_file",
    "temp_directory",
    "resource_monitor",
    "register_resource",
    "get_resource_monitor",
    "DEFAULT_MAX_CACHE_SIZE",
    "DEFAULT_MAX_TEMP_SIZE",
    "DEFAULT_MAX_MEMORY_USAGE",
]
