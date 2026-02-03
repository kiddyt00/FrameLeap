"""
HTTP客户端基类

提供统一的HTTP请求处理、连接池管理、重试机制和日志记录
"""

from abc import ABC, abstractmethod
from typing import Any, Callable
import logging
import functools
import time

import httpx

from app.exceptions import (
    APIConnectionError,
    APIAuthenticationError,
    APIRateLimitError,
    APIResponseError,
    APITimeoutError,
)
from app.utils.types import Seconds

logger = logging.getLogger(__name__)


# =============================================================================
# 重试装饰器
# =============================================================================

def retry_on_error(
    max_retries: int = 3,
    base_delay: Seconds = 1.0,
    max_delay: Seconds = 60.0,
    backoff_factor: float = 2.0,
    retry_on: tuple[type[Exception], ...] = (
        httpx.TimeoutException,
        httpx.ConnectError,
        httpx.RemoteProtocolError,
    ),
) -> Callable:
    """请求重试装饰器

    Args:
        max_retries: 最大重试次数
        base_delay: 基础延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        backoff_factor: 退避因子
        retry_on: 需要重试的异常类型

    Returns:
        装饰器函数

    Examples:
        >>> @retry_on_error(max_retries=3)
        >>> def fetch_data():
        ...     return httpx.get("https://api.example.com")
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            delay = base_delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e

                    if attempt >= max_retries:
                        logger.error(
                            f"请求失败，已达最大重试次数 {max_retries}: {e}"
                        )
                        raise

                    logger.warning(
                        f"请求失败，{delay}秒后重试 ({attempt + 1}/{max_retries}): {e}"
                    )
                    time.sleep(min(delay, max_delay))
                    delay *= backoff_factor
                except Exception as e:
                    # 不重试的错误直接抛出
                    raise

            # 不应该到达这里
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


# =============================================================================
# HTTP客户端基类
# =============================================================================

class BaseHTTPClient(ABC):
    """HTTP客户端基类

    提供统一的HTTP请求接口、连接池管理、错误处理和日志记录

    Attributes:
        api_key: API密钥
        base_url: API基础URL
        timeout: 默认请求超时时间
        max_retries: 最大重试次数
        _client: httpx客户端实例
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        *,
        timeout: Seconds = 60.0,
        max_retries: int = 3,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
    ) -> None:
        """初始化HTTP客户端

        Args:
            api_key: API密钥
            base_url: API基础URL
            timeout: 默认请求超时时间（秒）
            max_retries: 最大重试次数
            max_connections: 最大连接数
            max_keepalive_connections: 最大保持连接数
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        # 创建连接池
        limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
        )

        self._client = httpx.Client(
            timeout=timeout,
            limits=limits,
        )

    def __enter__(self) -> "BaseHTTPClient":
        """上下文管理器入口"""
        return self

    def __exit__(self, *args: Any) -> None:
        """上下文管理器退出"""
        self.close()

    def close(self) -> None:
        """关闭客户端连接"""
        if hasattr(self, "_client") and self._client:
            self._client.close()

    @property
    def headers(self) -> dict[str, str]:
        """获取默认请求头

        Returns:
            默认请求头字典
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "FrameLeap/0.1.0",
        }

    def _build_url(self, path: str) -> str:
        """构建完整URL

        Args:
            path: API路径

        Returns:
            完整URL
        """
        return f"{self.base_url}/{path.lstrip('/')}"

    @retry_on_error(max_retries=3)
    def _request(
        self,
        method: str,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: Seconds | None = None,
    ) -> httpx.Response:
        """发送HTTP请求

        Args:
            method: HTTP方法 (GET, POST, PUT, DELETE)
            path: API路径
            data: 请求体数据
            params: 查询参数
            headers: 额外请求头
            timeout: 超时时间（覆盖默认值）

        Returns:
            HTTP响应对象

        Raises:
            APIConnectionError: 连接失败
            APIAuthenticationError: 认证失败
            APIRateLimitError: 速率限制
            APITimeoutError: 请求超时
            APIResponseError: 响应错误
        """
        url = self._build_url(path)
        request_headers = {**self.headers, **(headers or {})}
        request_timeout = timeout or self.timeout

        logger.debug(f"发送{method}请求: {url}")

        try:
            response = self._client.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=request_headers,
                timeout=request_timeout,
            )
            return response

        except httpx.TimeoutException as e:
            raise APITimeoutError(
                f"请求超时: {url}",
                provider=self.__class__.__name__,
                timeout=request_timeout,
            ) from e

        except httpx.ConnectError as e:
            raise APIConnectionError(
                f"连接失败: {url}",
                provider=self.__class__.__name__,
            ) from e

        except httpx.HTTPStatusError as e:
            # 处理HTTP错误状态码
            status_code = e.response.status_code
            response_text = e.response.text

            if status_code == 401:
                raise APIAuthenticationError(
                    f"认证失败，请检查API密钥: {response_text}",
                    provider=self.__class__.__name__,
                ) from e

            if status_code == 429:
                retry_after = e.response.headers.get("Retry-After")
                retry_after_seconds = int(retry_after) if retry_after else None
                raise APIRateLimitError(
                    f"请求过于频繁: {response_text}",
                    provider=self.__class__.__name__,
                    retry_after=retry_after_seconds,
                ) from e

            raise APIResponseError(
                f"API返回错误 (status={status_code}): {response_text}",
                provider=self.__class__.__name__,
                status_code=status_code,
                response_text=response_text,
            ) from e

        except httpx.HTTPError as e:
            raise APIConnectionError(
                f"HTTP请求失败: {e}",
                provider=self.__class__.__name__,
            ) from e

    def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: Seconds | None = None,
    ) -> httpx.Response:
        """发送GET请求

        Args:
            path: API路径
            params: 查询参数
            headers: 额外请求头
            timeout: 超时时间

        Returns:
            HTTP响应对象
        """
        return self._request("GET", path, params=params, headers=headers, timeout=timeout)

    def post(
        self,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: Seconds | None = None,
    ) -> httpx.Response:
        """发送POST请求

        Args:
            path: API路径
            data: 请求体数据
            headers: 额外请求头
            timeout: 超时时间

        Returns:
            HTTP响应对象
        """
        return self._request("POST", path, data=data, headers=headers, timeout=timeout)

    def put(
        self,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: Seconds | None = None,
    ) -> httpx.Response:
        """发送PUT请求

        Args:
            path: API路径
            data: 请求体数据
            headers: 额外请求头
            timeout: 超时时间

        Returns:
            HTTP响应对象
        """
        return self._request("PUT", path, data=data, headers=headers, timeout=timeout)

    def delete(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: Seconds | None = None,
    ) -> httpx.Response:
        """发送DELETE请求

        Args:
            path: API路径
            params: 查询参数
            headers: 额外请求头
            timeout: 超时时间

        Returns:
            HTTP响应对象
        """
        return self._request("DELETE", path, params=params, headers=headers, timeout=timeout)

    def parse_json_response(self, response: httpx.Response) -> dict[str, Any]:
        """解析JSON响应

        Args:
            response: HTTP响应对象

        Returns:
            解析后的JSON字典

        Raises:
            APIResponseError: JSON解析失败
        """
        try:
            return response.json()
        except ValueError as e:
            raise APIResponseError(
                f"无法解析JSON响应: {response.text[:200]}",
                provider=self.__class__.__name__,
            ) from e


# =============================================================================
# 异步HTTP客户端
# =============================================================================

class BaseAsyncHTTPClient(BaseHTTPClient):
    """异步HTTP客户端基类

    提供异步HTTP请求支持
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        *,
        timeout: Seconds = 60.0,
        max_retries: int = 3,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
    ) -> None:
        """初始化异步HTTP客户端

        Args:
            api_key: API密钥
            base_url: API基础URL
            timeout: 默认请求超时时间（秒）
            max_retries: 最大重试次数
            max_connections: 最大连接数
            max_keepalive_connections: 最大保持连接数
        """
        # 调用父类初始化但不创建客户端
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        # 创建异步连接池
        limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
        )

        self._client = httpx.AsyncClient(
            timeout=timeout,
            limits=limits,
        )

    async def close(self) -> None:
        """关闭异步客户端连接"""
        if hasattr(self, "_client") and self._client:
            await self._client.aclose()

    async def __aenter__(self) -> "BaseAsyncHTTPClient":
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """异步上下文管理器退出"""
        await self.close()

    @retry_on_error(max_retries=3)
    async def _request(
        self,
        method: str,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: Seconds | None = None,
    ) -> httpx.Response:
        """发送异步HTTP请求

        Args:
            method: HTTP方法
            path: API路径
            data: 请求体数据
            params: 查询参数
            headers: 额外请求头
            timeout: 超时时间

        Returns:
            HTTP响应对象

        Raises:
            APIConnectionError: 连接失败
            APIAuthenticationError: 认证失败
            APIRateLimitError: 速率限制
            APITimeoutError: 请求超时
            APIResponseError: 响应错误
        """
        url = self._build_url(path)
        request_headers = {**self.headers, **(headers or {})}
        request_timeout = timeout or self.timeout

        logger.debug(f"发送异步{method}请求: {url}")

        try:
            response = await self._client.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=request_headers,
                timeout=request_timeout,
            )
            return response

        except httpx.TimeoutException as e:
            raise APITimeoutError(
                f"请求超时: {url}",
                provider=self.__class__.__name__,
                timeout=request_timeout,
            ) from e

        except httpx.ConnectError as e:
            raise APIConnectionError(
                f"连接失败: {url}",
                provider=self.__class__.__name__,
            ) from e

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            response_text = e.response.text

            if status_code == 401:
                raise APIAuthenticationError(
                    f"认证失败: {response_text}",
                    provider=self.__class__.__name__,
                ) from e

            if status_code == 429:
                retry_after = e.response.headers.get("Retry-After")
                retry_after_seconds = int(retry_after) if retry_after else None
                raise APIRateLimitError(
                    f"请求过于频繁: {response_text}",
                    provider=self.__class__.__name__,
                    retry_after=retry_after_seconds,
                ) from e

            raise APIResponseError(
                f"API返回错误 (status={status_code}): {response_text}",
                provider=self.__class__.__name__,
                status_code=status_code,
                response_text=response_text,
            ) from e

        except httpx.HTTPError as e:
            raise APIConnectionError(
                f"HTTP请求失败: {e}",
                provider=self.__class__.__name__,
            ) from e

    async def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: Seconds | None = None,
    ) -> httpx.Response:
        """发送异步GET请求"""
        return await self._request("GET", path, params=params, headers=headers, timeout=timeout)

    async def post(
        self,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: Seconds | None = None,
    ) -> httpx.Response:
        """发送异步POST请求"""
        return await self._request("POST", path, data=data, headers=headers, timeout=timeout)


__all__ = [
    "retry_on_error",
    "BaseHTTPClient",
    "BaseAsyncHTTPClient",
]
