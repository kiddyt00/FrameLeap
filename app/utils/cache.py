"""
缓存机制实现

提供基于文件系统的缓存，支持缓存过期和键生成
"""

from pathlib import Path
from typing import Any, Callable, TypeVar
import hashlib
import json
import pickle
import logging
import time
from functools import wraps

from app.utils.types import Seconds

logger = logging.getLogger(__name__)

# 泛型类型变量
T = TypeVar("T")


# =============================================================================
# 缓存键生成
# =============================================================================

def generate_cache_key(
    *args: Any,
    **kwargs: Any,
) -> str:
    """生成缓存键

    将参数序列化为字符串后计算哈希值

    Args:
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        缓存键（十六进制哈希字符串）

    Examples:
        >>> generate_cache_key("test", param1=1, param2=2)
        'a1b2c3d4e5f6...'
    """
    # 序列化参数
    key_data = {
        "args": args,
        "kwargs": sorted(kwargs.items()),
    }
    key_string = json.dumps(key_data, sort_keys=True, default=str)

    # 计算哈希
    hash_obj = hashlib.sha256(key_string.encode())
    return hash_obj.hexdigest()


def generate_file_cache_key(
    content: str | bytes,
    salt: str = "",
) -> str:
    """为文件内容生成缓存键

    Args:
        content: 文件内容（字符串或字节）
        salt: 随机盐值

    Returns:
        缓存键
    """
    if isinstance(content, str):
        content = content.encode()

    hash_obj = hashlib.sha256(content)
    if salt:
        hash_obj.update(salt.encode())

    return hash_obj.hexdigest()


# =============================================================================
# 文件系统缓存
# =============================================================================

class FileCache:
    """文件系统缓存

    使用文件系统存储缓存数据，支持过期时间

    Attributes:
        cache_dir: 缓存目录
        default_ttl: 默认过期时间（秒）
    """

    def __init__(
        self,
        cache_dir: Path,
        default_ttl: Seconds = 3600,
    ) -> None:
        """初始化文件缓存

        Args:
            cache_dir: 缓存目录路径
            default_ttl: 默认过期时间（秒），默认1小时
        """
        self.cache_dir = Path(cache_dir)
        self.default_ttl = default_ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, key: str) -> Path:
        """获取缓存文件路径

        Args:
            key: 缓存键

        Returns:
            缓存文件路径
        """
        # 使用前两位作为子目录，避免单个目录文件过多
        subdir = key[:2]
        return self.cache_dir / subdir / f"{key}.cache"

    def get(
        self,
        key: str,
        default: T | None = None,
    ) -> T | None:
        """获取缓存

        Args:
            key: 缓存键
            default: 默认值（缓存不存在时返回）

        Returns:
            缓存的值，不存在返回默认值
        """
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return default

        try:
            with open(cache_path, "rb") as f:
                data = pickle.load(f)

            # 检查是否过期
            if data.get("expires_at", float("inf")) < time.time():
                self.delete(key)
                return default

            logger.debug(f"缓存命中: {key}")
            return data.get("value")

        except (pickle.PickleError, EOFError) as e:
            logger.warning(f"缓存读取失败: {key}, {e}")
            self.delete(key)
            return default

    def set(
        self,
        key: str,
        value: T,
        ttl: Seconds | None = None,
    ) -> None:
        """设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None表示使用默认值
        """
        cache_path = self._get_cache_path(key)
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        ttl = ttl if ttl is not None else self.default_ttl
        data = {
            "value": value,
            "created_at": time.time(),
            "expires_at": time.time() + ttl,
            "ttl": ttl,
        }

        try:
            with open(cache_path, "wb") as f:
                pickle.dump(data, f)
            logger.debug(f"缓存已保存: {key}, ttl={ttl}s")
        except (pickle.PickleError, IOError) as e:
            logger.error(f"缓存保存失败: {key}, {e}")

    def delete(self, key: str) -> bool:
        """删除缓存

        Args:
            key: 缓存键

        Returns:
            是否成功删除
        """
        cache_path = self._get_cache_path(key)

        if cache_path.exists():
            try:
                cache_path.unlink()
                logger.debug(f"缓存已删除: {key}")
                return True
            except IOError as e:
                logger.error(f"缓存删除失败: {key}, {e}")
                return False

        return False

    def clear(self) -> int:
        """清空所有缓存

        Returns:
            删除的缓存文件数量
        """
        count = 0
        for cache_file in self.cache_dir.rglob("*.cache"):
            try:
                cache_file.unlink()
                count += 1
            except IOError as e:
                logger.warning(f"删除缓存文件失败: {cache_file}, {e}")

        logger.info(f"已清空 {count} 个缓存文件")
        return count

    def cleanup_expired(self) -> int:
        """清理过期缓存

        Returns:
            清理的缓存文件数量
        """
        count = 0
        now = time.time()

        for cache_file in self.cache_dir.rglob("*.cache"):
            try:
                with open(cache_file, "rb") as f:
                    data = pickle.load(f)

                if data.get("expires_at", float("inf")) < now:
                    cache_file.unlink()
                    count += 1
            except (pickle.PickleError, EOFError, IOError):
                # 读取失败的文件也删除
                try:
                    cache_file.unlink()
                    count += 1
                except IOError:
                    pass

        if count > 0:
            logger.info(f"已清理 {count} 个过期缓存")

        return count

    def get_info(self, key: str) -> dict[str, Any] | None:
        """获取缓存信息

        Args:
            key: 缓存键

        Returns:
            缓存信息字典，不存在返回None
        """
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "rb") as f:
                data = pickle.load(f)

            return {
                "created_at": data.get("created_at"),
                "expires_at": data.get("expires_at"),
                "ttl": data.get("ttl"),
                "size": cache_path.stat().st_size,
                "expired": data.get("expires_at", float("inf")) < time.time(),
            }
        except (pickle.PickleError, EOFError, IOError):
            return None

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计信息

        Returns:
            统计信息字典
        """
        total_size = 0
        total_count = 0
        expired_count = 0
        now = time.time()

        for cache_file in self.cache_dir.rglob("*.cache"):
            total_count += 1
            total_size += cache_file.stat().st_size

            try:
                with open(cache_file, "rb") as f:
                    data = pickle.load(f)

                if data.get("expires_at", float("inf")) < now:
                    expired_count += 1
            except (pickle.PickleError, EOFError, IOError):
                expired_count += 1

        return {
            "total_count": total_count,
            "total_size": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "expired_count": expired_count,
            "valid_count": total_count - expired_count,
        }


# =============================================================================
# 缓存装饰器
# =============================================================================

def cached(
    cache: FileCache | None = None,
    ttl: Seconds | None = None,
    key_func: Callable[..., str] | None = None,
) -> Callable:
    """缓存装饰器

    Args:
        cache: 缓存实例，None则使用默认缓存
        ttl: 过期时间（秒）
        key_func: 自定义缓存键函数

    Returns:
        装饰器函数

    Examples:
        >>> cache = FileCache(Path("/tmp/cache"))
        >>> @cached(cache, ttl=600)
        >>> def expensive_function(x, y):
        ...     return x + y

        >>> # 使用自定义键函数
        >>> @cached(key_func=lambda self, url: hashlib.md5(url.encode()).hexdigest())
        >>> def fetch_data(self, url):
        ...     return requests.get(url).json()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = generate_cache_key(
                    func.__name__,
                    *args,
                    **kwargs,
                )

            # 尝试从缓存获取
            _cache = cache or _default_cache
            cached_value = _cache.get(cache_key)

            if cached_value is not None:
                return cached_value

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            _cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper
    return decorator


def cached_async(
    cache: FileCache | None = None,
    ttl: Seconds | None = None,
    key_func: Callable[..., str] | None = None,
) -> Callable:
    """异步缓存装饰器

    Args:
        cache: 缓存实例
        ttl: 过期时间（秒）
        key_func: 自定义缓存键函数

    Returns:
        装饰器函数

    Examples:
        >>> @cached_async(ttl=600)
        >>> async def async_fetch(url):
        ...     return await aiohttp.get(url)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = generate_cache_key(
                    func.__name__,
                    *args,
                    **kwargs,
                )

            # 尝试从缓存获取
            _cache = cache or _default_cache
            cached_value = _cache.get(cache_key)

            if cached_value is not None:
                return cached_value

            # 执行异步函数并缓存结果
            result = await func(*args, **kwargs)
            _cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper
    return decorator


# =============================================================================
# 默认缓存实例
# =============================================================================

_default_cache: FileCache | None = None


def get_default_cache() -> FileCache:
    """获取默认缓存实例

    Returns:
        默认文件缓存实例
    """
    global _default_cache
    if _default_cache is None:
        from app.config import config
        cache_dir = config.paths.cache_dir / "api"
        _default_cache = FileCache(cache_dir, default_ttl=3600)
    return _default_cache


def set_default_cache(cache: FileCache) -> None:
    """设置默认缓存实例

    Args:
        cache: 缓存实例
    """
    global _default_cache
    _default_cache = cache


__all__ = [
    "generate_cache_key",
    "generate_file_cache_key",
    "FileCache",
    "cached",
    "cached_async",
    "get_default_cache",
    "set_default_cache",
]
