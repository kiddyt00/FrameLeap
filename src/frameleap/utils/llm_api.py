"""
LLM API集成

支持多种语言模型服务（OpenAI、Anthropic、DeepSeek、本地模型）
"""

from abc import ABC, abstractmethod
from typing import Any
import time


class LLM_API(ABC):
    """LLM API基类

    定义所有LLM提供商的通用接口

    Attributes:
        api_key: API密钥
        model: 模型名称
        base_url: API基础URL（可选）
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str | None = None,
    ) -> None:
        """初始化LLM API客户端

        Args:
            api_key: API密钥
            model: 模型名称
            base_url: API基础URL，用于自定义端点
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    @abstractmethod
    def generate(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> str:
        """生成文本

        Args:
            prompt: 输入提示词
            **kwargs: 额外参数（temperature、max_tokens等）

        Returns:
            生成的文本内容

        Raises:
            APIConnectionError: 网络连接失败
            APIAuthenticationError: API密钥无效
            APIResponseError: API响应错误
        """
        raise NotImplementedError


class OpenAI_API(LLM_API):
    """OpenAI API客户端

    支持GPT-4、GPT-3.5等模型

    Example:
        >>> api = OpenAI_API("sk-xxx", "gpt-4")
        >>> result = api.generate("写一个故事", temperature=0.7)
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
    ) -> None:
        """初始化OpenAI API客户端

        Args:
            api_key: OpenAI API密钥
            model: 模型名称，默认"gpt-4"
        """
        super().__init__(api_key, model)

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs: Any,
    ) -> str:
        """使用OpenAI生成文本

        Args:
            prompt: 输入提示词
            temperature: 温度参数 (0.0-2.0)，越高越随机
            max_tokens: 最大生成token数
            **kwargs: 其他OpenAI参数

        Returns:
            生成的文本

        Raises:
            APIConnectionError: 网络错误
            APIAuthenticationError: API密钥无效
            APIResponseError: API返回错误
        """
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)

        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        return response.choices[0].message.content


class Anthropic_API(LLM_API):
    """Anthropic Claude API客户端

    支持Claude 3 Opus、Sonnet、Haiku等模型

    Example:
        >>> api = Anthropic_API("sk-ant-xxx", "claude-3-opus-20240229")
        >>> result = api.generate("写一个故事")
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-opus-20240229",
    ) -> None:
        """初始化Anthropic API客户端

        Args:
            api_key: Anthropic API密钥
            model: 模型名称，默认"claude-3-opus-20240229"
        """
        super().__init__(api_key, model)

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs: Any,
    ) -> str:
        """使用Claude生成文本

        Args:
            prompt: 输入提示词
            temperature: 温度参数 (0.0-1.0)
            max_tokens: 最大生成token数
            **kwargs: 其他Claude参数

        Returns:
            生成的文本

        Raises:
            APIConnectionError: 网络错误
            APIAuthenticationError: API密钥无效
            APIResponseError: API返回错误
        """
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key)

        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )

        return response.content[0].text


class DeepSeek_API(LLM_API):
    """DeepSeek API客户端

    高性价比的国产大模型API

    Example:
        >>> api = DeepSeek_API("sk-xxx")
        >>> result = api.generate("写一个故事")
    """

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-chat",
    ) -> None:
        """初始化DeepSeek API客户端

        Args:
            api_key: DeepSeek API密钥
            model: 模型名称，默认"deepseek-chat"
        """
        super().__init__(api_key, model, "https://api.deepseek.com")

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs: Any,
    ) -> str:
        """使用DeepSeek生成文本

        Args:
            prompt: 输入提示词
            temperature: 温度参数 (0.0-2.0)
            max_tokens: 最大生成token数
            **kwargs: 其他参数

        Returns:
            生成的文本

        Raises:
            APIConnectionError: 网络错误
            APIAuthenticationError: API密钥无效
            APIResponseError: API返回错误
        """
        import httpx

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        response = httpx.post(
            f"{self.base_url}/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=120,
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]


class LocalLLM_API(LLM_API):
    """本地LLM API客户端

    支持Ollama等本地大模型服务

    Example:
        >>> api = LocalLLM_API(model="llama2")
        >>> result = api.generate("写一个故事")
    """

    def __init__(
        self,
        model: str = "llama2",
        base_url: str = "http://localhost:11434",
    ) -> None:
        """初始化本地LLM API客户端

        Args:
            model: 模型名称，默认"llama2"
            base_url: Ollama服务地址
        """
        super().__init__("", model, base_url)

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        """使用本地LLM生成文本

        Args:
            prompt: 输入提示词
            temperature: 温度参数
            **kwargs: 其他参数

        Returns:
            生成的文本

        Raises:
            APIConnectionError: 无法连接到本地服务
            APIResponseError: 响应解析失败
        """
        import httpx

        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature},
            },
            timeout=300,
        )

        response.raise_for_status()
        result = response.json()
        return result.get("response", "")


def create_llm_api(
    provider: str,
    **kwargs: Any,
) -> LLM_API:
    """创建LLM API实例

    工厂函数，根据提供商名称创建对应的API客户端

    Args:
        provider: 提供商名称
            - "openai": OpenAI (GPT-4, GPT-3.5)
            - "anthropic": Anthropic (Claude)
            - "deepseek": DeepSeek
            - "local": 本地模型 (Ollama)
        **kwargs: 传递给具体API类的参数

    Returns:
        LLM_API实例

    Raises:
        ValueError: 不支持的提供商

    Examples:
        >>> api = create_llm_api("openai", api_key="sk-xxx")
        >>> api = create_llm_api("local", model="llama2")
    """
    factories: dict[str, type[LLM_API]] = {
        "openai": lambda: OpenAI_API(kwargs["api_key"], kwargs.get("model", "gpt-4")),
        "anthropic": lambda: Anthropic_API(
            kwargs["api_key"],
            kwargs.get("model", "claude-3-opus-20240229")
        ),
        "deepseek": lambda: DeepSeek_API(kwargs["api_key"]),
        "local": lambda: LocalLLM_API(
            kwargs.get("model", "llama2"),
            kwargs.get("base_url", "http://localhost:11434")
        ),
    }

    if provider not in factories:
        raise ValueError(
            f"Unknown provider: {provider}. "
            f"Supported providers: {', '.join(factories.keys())}"
        )

    return factories[provider]()


__all__ = [
    "LLM_API",
    "OpenAI_API",
    "Anthropic_API",
    "DeepSeek_API",
    "LocalLLM_API",
    "create_llm_api",
]
