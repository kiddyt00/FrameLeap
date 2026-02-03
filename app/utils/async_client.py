"""
异步API客户端支持

提供异步版本的API客户端，支持并发请求
"""

from typing import Any, Callable
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from app.utils.http_client import BaseAsyncHTTPClient
from app.utils.cache import cached_async, FileCache
from app.exceptions import APIError

logger = logging.getLogger(__name__)


# =============================================================================
# 异步LLM API客户端
# =============================================================================

class AsyncLLMAPI(BaseAsyncHTTPClient):
    """异步LLM API基类"""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
    ) -> None:
        """初始化异步LLM API客户端

        Args:
            api_key: API密钥
            model: 模型名称
            base_url: API基础URL
        """
        super().__init__(api_key, base_url)
        self.model = model

    async def generate(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> str:
        """异步生成文本

        Args:
            prompt: 输入提示词
            **kwargs: 额外参数

        Returns:
            生成的文本
        """
        raise NotImplementedError


class AsyncDeepSeek_API(AsyncLLMAPI):
    """异步DeepSeek API客户端"""

    def __init__(
        self,
        api_key: str,
    ) -> None:
        """初始化异步DeepSeek API客户端"""
        super().__init__(api_key, "deepseek-chat", "https://api.deepseek.com")

    @cached_async(ttl=1800)  # 30分钟缓存
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs: Any,
    ) -> str:
        """使用DeepSeek异步生成文本"""
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        response = await self.post("/v1/chat/completions", data=data)
        result = response.json()
        return result["choices"][0]["message"]["content"]


# =============================================================================
# 并发API调用
# =============================================================================

class ConcurrentAPIExecutor:
    """并发API执行器

    管理多个API调用的并发执行

    Attributes:
        max_concurrent: 最大并发数
        timeout: 单个请求超时时间
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        timeout: float = 120.0,
    ) -> None:
        """初始化并发执行器

        Args:
            max_concurrent: 最大并发请求数
            timeout: 请求超时时间（秒）
        """
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def execute(
        self,
        coro: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """执行单个协程

        Args:
            coro: 协程函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            协程结果
        """
        async with self._semaphore:
            try:
                return await asyncio.wait_for(
                    coro(*args, **kwargs),
                    timeout=self.timeout,
                )
            except asyncio.TimeoutError:
                logger.error(f"请求超时: {args}")
                raise

    async def execute_batch(
        self,
        tasks: list[tuple[Callable, tuple, dict]],
    ) -> list[Any]:
        """批量执行任务

        Args:
            tasks: 任务列表，每个元素为 (coro, args, kwargs) 元组

        Returns:
            结果列表

        Examples:
            >>> executor = ConcurrentAPIExecutor(max_concurrent=3)
            >>> tasks = [
            ...     (api1.generate, ("prompt1",), {}),
            ...     (api2.generate, ("prompt2",), {}),
            ... ]
            >>> results = await executor.execute_batch(tasks)
        """
        coros = [
            self.execute(coro, *args, **kwargs)
            for coro, args, kwargs in tasks
        ]

        return await asyncio.gather(*coros, return_exceptions=True)

    async def execute_with_progress(
        self,
        tasks: list[tuple[Callable, tuple, dict]],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[Any]:
        """带进度回调的批量执行

        Args:
            tasks: 任务列表
            progress_callback: 进度回调 (current, total)

        Returns:
            结果列表
        """
        total = len(tasks)
        results = []

        for i, (coro, args, kwargs) in enumerate(tasks):
            result = await self.execute(coro, *args, **kwargs)
            results.append(result)

            if progress_callback:
                progress_callback(i + 1, total)

        return results


# =============================================================================
# 并发图像生成
# =============================================================================

class ConcurrentImageGenerator:
    """并发图像生成器

    支持批量并发生成图像

    Attributes:
        api_client: 图像生成API客户端
        max_concurrent: 最大并发数
    """

    def __init__(
        self,
        api_client: Any,
        max_concurrent: int = 3,
    ) -> None:
        """初始化并发图像生成器

        Args:
            api_client: 图像API客户端
            max_concurrent: 最大并发数
        """
        self.api_client = api_client
        self.max_concurrent = max_concurrent
        self._executor = ConcurrentAPIExecutor(max_concurrent)

    async def generate_batch(
        self,
        prompts: list[str],
        negative: str = "",
        width: int = 1024,
        height: int = 1024,
        **kwargs: Any,
    ) -> list[bytes]:
        """批量生成图像

        Args:
            prompts: 提示词列表
            negative: 负面提示词
            width: 图像宽度
            height: 图像高度
            **kwargs: 其他参数

        Returns:
            图像数据列表

        Examples:
            >>> generator = ConcurrentImageGenerator(api, max_concurrent=3)
            >>> prompts = ["一只猫", "一只狗", "一只鸟"]
            >>> images = await generator.generate_batch(prompts)
        """
        # 使用线程池执行同步API调用
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=self.max_concurrent)

        def sync_generate(prompt: str) -> bytes:
            return self.api_client.generate(
                prompt,
                negative=negative,
                width=width,
                height=height,
                **kwargs,
            )

        tasks = [
            loop.run_in_executor(executor, sync_generate, prompt)
            for prompt in prompts
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        images = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"图像生成失败 [{i}]: {result}")
                # 返回空占位符
                images.append(b"")
            else:
                images.append(result)

        return images

    async def generate_with_progress(
        self,
        prompts: list[str],
        negative: str = "",
        width: int = 1024,
        height: int = 1024,
        progress_callback: Callable[[int, int, int, int], None] | None = None,
        **kwargs: Any,
    ) -> list[bytes]:
        """带进度回调的批量图像生成

        Args:
            prompts: 提示词列表
            negative: 负面提示词
            width: 图像宽度
            height: 图像高度
            progress_callback: 进度回调 (current, total, success, failed)
            **kwargs: 其他参数

        Returns:
            图像数据列表
        """
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=self.max_concurrent)

        def sync_generate(prompt: str) -> bytes:
            return self.api_client.generate(
                prompt,
                negative=negative,
                width=width,
                height=height,
                **kwargs,
            )

        total = len(prompts)
        success_count = 0
        failed_count = 0
        images = []

        for i, prompt in enumerate(prompts):
            try:
                result = await loop.run_in_executor(executor, sync_generate, prompt)
                images.append(result)
                success_count += 1
            except Exception as e:
                logger.error(f"图像生成失败 [{i}]: {e}")
                images.append(b"")
                failed_count += 1

            if progress_callback:
                progress_callback(i + 1, total, success_count, failed_count)

        return images


# =============================================================================
# 工厂函数
# =============================================================================

def create_async_llm_api(
    provider: str,
    api_key: str,
    **kwargs: Any,
) -> AsyncLLMAPI:
    """创建异步LLM API实例

    Args:
        provider: 提供商名称
        api_key: API密钥
        **kwargs: 其他参数

    Returns:
        异步LLM API实例

    Raises:
        ValueError: 不支持的提供商

    Examples:
        >>> api = create_async_llm_api("deepseek", "sk-xxx")
        >>> result = await api.generate("写一个故事")
    """
    factories: dict[str, type[AsyncLLMAPI]] = {
        "deepseek": AsyncDeepSeek_API,
    }

    if provider not in factories:
        raise ValueError(
            f"Unknown provider: {provider}. "
            f"Supported: {', '.join(factories.keys())}"
        )

    return factories[provider](api_key, **kwargs)


__all__ = [
    "AsyncLLMAPI",
    "AsyncDeepSeek_API",
    "ConcurrentAPIExecutor",
    "ConcurrentImageGenerator",
    "create_async_llm_api",
]
