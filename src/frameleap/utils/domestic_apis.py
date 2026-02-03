"""
国内API集成 - 优先使用，降低延迟

支持的国内服务：
- LLM: DeepSeek、通义千问、文心一言、智谱AI、Kimi
- 图像: Flux(国内镜像)、通义万相、百度文心一格
- TTS: 鱼声、标贝、出门问问、火山引擎
"""

from abc import ABC, abstractmethod
from typing import Any
import base64


# =============================================================================
# 国内LLM API
# =============================================================================

class BaseLLMAPI(ABC):
    """国内LLM API基类"""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
    ) -> None:
        """初始化LLM API客户端

        Args:
            api_key: API密钥
            model: 模型名称
            base_url: API基础URL
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    @abstractmethod
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs: Any,
    ) -> str:
        """生成文本

        Args:
            prompt: 输入提示词
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数

        Returns:
            生成的文本
        """
        raise NotImplementedError


class DeepSeek_API(BaseLLMAPI):
    """DeepSeek API - 国内首选，性价比高

    高性能国产大模型，价格亲民

    Example:
        >>> api = DeepSeek_API("sk-xxx")
        >>> result = api.generate("写一个故事")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com",
    ) -> None:
        """初始化DeepSeek API客户端

        Args:
            api_key: DeepSeek API密钥
            base_url: API基础URL
        """
        super().__init__(api_key, "deepseek-chat", base_url)

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs: Any,
    ) -> str:
        """生成文本"""
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
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]


class Qwen_API(BaseLLMAPI):
    """通义千问 API - 阿里云

    阿里云推出的大语言模型服务

    Example:
        >>> api = Qwen_API("sk-xxx")
        >>> result = api.generate("写一个故事")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://dashscope.aliyuncs.com",
    ) -> None:
        """初始化通义千问 API客户端

        Args:
            api_key: 阿里云API密钥
            base_url: API基础URL
        """
        super().__init__(api_key, "qwen-turbo", base_url)

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs: Any,
    ) -> str:
        """生成文本"""
        import httpx

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": self.model,
            "input": {
                "messages": [{"role": "user", "content": prompt}]
            },
            "parameters": {
                "temperature": temperature,
                "max_tokens": max_tokens,
                "result_format": "message"
            }
        }

        response = httpx.post(
            f"{self.base_url}/api/v1/services/aigc/text-generation/generation",
            headers=headers,
            json=data,
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
        return result["output"]["text"]


class Zhipu_API(BaseLLMAPI):
    """智谱AI GLM - 清华系

    清华大学背景的大模型公司

    Example:
        >>> api = Zhipu_API("xxx")
        >>> result = api.generate("写一个故事")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://open.bigmodel.cn",
    ) -> None:
        """初始化智谱AI API客户端

        Args:
            api_key: 智谱API密钥
            base_url: API基础URL
        """
        super().__init__(api_key, "glm-4", base_url)

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs: Any,
    ) -> str:
        """生成文本"""
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
            f"{self.base_url}/api/paas/v4/chat/completions",
            headers=headers,
            json=data,
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]


class Kimi_API(BaseLLMAPI):
    """Kimi API - Moonshot

    月之暗面推出的大模型

    Example:
        >>> api = Kimi_API("sk-xxx")
        >>> result = api.generate("写一个故事")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.moonshot.cn",
    ) -> None:
        """初始化Kimi API客户端

        Args:
            api_key: Moonshot API密钥
            base_url: API基础URL
        """
        super().__init__(api_key, "moonshot-v1-8k", base_url)

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs: Any,
    ) -> str:
        """生成文本"""
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
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]


# =============================================================================
# 国内图像生成API
# =============================================================================

class BaseImageAPI(ABC):
    """图像生成API基类"""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        negative: str = "",
        width: int = 1024,
        height: int = 1024,
        **kwargs: Any,
    ) -> bytes:
        """生成图像

        Args:
            prompt: 提示词
            negative: 负面提示词
            width: 图像宽度
            height: 图像高度
            **kwargs: 其他参数

        Returns:
            图像二进制数据
        """
        raise NotImplementedError


class FluxCN_API(BaseImageAPI):
    """Flux国内镜像API - 快速高质量

    Flux模型的国内中转服务，速度快质量高

    Example:
        >>> api = FluxCN_API("sk-xxx")
        >>> image_data = api.generate("一只猫", width=1024, height=1024)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
    ) -> None:
        """初始化FluxCN API客户端

        Args:
            api_key: API密钥
            base_url: API基础URL，默认使用官方中转
        """
        self.api_key = api_key
        self.base_url = base_url or "https://api.fluxcn.cn"

    def generate(
        self,
        prompt: str,
        negative: str = "",
        width: int = 1024,
        height: int = 1024,
        **kwargs: Any,
    ) -> bytes:
        """生成图像"""
        import httpx

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "prompt": prompt,
            "negative_prompt": negative,
            "width": width,
            "height": height,
            "steps": kwargs.get("steps", 28),
            "guidance_scale": kwargs.get("cfg_scale", 7.5),
        }

        response = httpx.post(
            f"{self.base_url}/v1/generate",
            headers=headers,
            json=data,
            timeout=120,
        )
        response.raise_for_status()
        result = response.json()

        # 下载图像
        if "image_url" in result:
            img_response = httpx.get(result["image_url"])
            return img_response.content
        elif "image_base64" in result:
            return base64.b64decode(result["image_base64"])
        else:
            raise ValueError("Unknown response format")


class QwenImage_API(BaseImageAPI):
    """通义万相 - 阿里云图像生成

    阿里云推出的文生图服务

    Example:
        >>> api = QwenImage_API("sk-xxx")
        >>> image_data = api.generate("一只猫")
    """

    def __init__(
        self,
        api_key: str,
    ) -> None:
        """初始化通义万相 API客户端

        Args:
            api_key: 阿里云API密钥
        """
        self.api_key = api_key
        self.base_url = "https://dashscope.aliyuncs.com"

    def generate(
        self,
        prompt: str,
        negative: str = "",
        width: int = 1024,
        height: int = 1024,
        **kwargs: Any,
    ) -> bytes:
        """生成图像"""
        import httpx

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": "wanx-v1",
            "input": {
                "prompt": prompt,
                "negative_prompt": negative,
            },
            "parameters": {
                "size": f"{width}*{height}",
                "n": 1,
            }
        }

        response = httpx.post(
            f"{self.base_url}/api/v1/services/aigc/text2image/image-synthesis",
            headers=headers,
            json=data,
            timeout=120,
        )
        response.raise_for_status()
        result = response.json()

        if "output" in result and "results" in result["output"]:
            return base64.b64decode(result["output"]["results"][0]["b64_image"])
        raise ValueError("Unknown response format")


# =============================================================================
# 国内TTS API
# =============================================================================

class BaseTTSAPI(ABC):
    """TTS API基类"""

    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        **kwargs: Any,
    ) -> bytes:
        """合成语音

        Args:
            text: 待合成文本
            voice_id: 音色ID
            **kwargs: 其他参数

        Returns:
            音频二进制数据
        """
        raise NotImplementedError


class FishAudio_API(BaseTTSAPI):
    """鱼声AI TTS - 高质量中文语音

    提供高质量中文语音合成服务

    Example:
        >>> api = FishAudio_API("sk-xxx")
        >>> audio_data = api.synthesize("你好世界", voice_id="female_qingxin")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.fish.audio",
    ) -> None:
        """初始化鱼声API客户端

        Args:
            api_key: API密钥
            base_url: API基础URL
        """
        self.api_key = api_key
        self.base_url = base_url

    def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        **kwargs: Any,
    ) -> bytes:
        """合成语音"""
        import httpx

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "text": text,
            "voice": voice_id or "female_qingxin",
            "speed": kwargs.get("speed", 1.0),
            "format": "mp3",
        }

        response = httpx.post(
            f"{self.base_url}/v1/tts",
            headers=headers,
            json=data,
            timeout=30,
        )
        response.raise_for_status()

        # 返回音频数据
        if response.headers.get("content-type", "").startswith("audio"):
            return response.content

        result = response.json()
        if "audio_url" in result:
            return httpx.get(result["audio_url"]).content

        raise ValueError("Unknown response format")


class XingTuo_API(BaseTTSAPI):
    """标贝TTS - 专业语音合成

    专业级语音合成服务

    Example:
        >>> api = XingTuo_API(api_key="xxx", app_id="xxx")
        >>> audio_data = api.synthesize("你好")
    """

    def __init__(
        self,
        api_key: str,
        app_id: str,
    ) -> None:
        """初始化标贝API客户端

        Args:
            api_key: API密钥
            app_id: 应用ID
        """
        self.api_key = api_key
        self.app_id = app_id
        self.base_url = "https://api.xfyun.cn"

    def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        **kwargs: Any,
    ) -> bytes:
        """合成语音"""
        # 标贝API实现
        # TODO: 根据实际API文档实现
        raise NotImplementedError("标贝API待实现")


# =============================================================================
# API工厂 - 优先使用国内服务
# =============================================================================

def create_llm_api(
    provider: str,
    api_key: str,
    **kwargs: Any,
) -> BaseLLMAPI:
    """创建LLM API - 优先国内服务

    Args:
        provider: 提供商名称
            - "deepseek": DeepSeek
            - "qwen": 通义千问
            - "zhipu": 智谱AI
            - "kimi": Moonshot Kimi
            - "openai": OpenAI (备用)
            - "anthropic": Anthropic (备用)
        api_key: API密钥
        **kwargs: 其他参数

    Returns:
        LLM API实例

    Raises:
        ValueError: 不支持的提供商

    Examples:
        >>> api = create_llm_api("deepseek", "sk-xxx")
        >>> result = api.generate("写一个故事")
    """
    factories: dict[str, type[BaseLLMAPI]] = {
        "deepseek": DeepSeek_API,
        "qwen": Qwen_API,
        "zhipu": Zhipu_API,
        "kimi": Kimi_API,
    }

    if provider in factories:
        return factories[provider](api_key, **kwargs)

    # 备用国外服务
    if provider == "openai":
        from frameleap.utils.llm_api import OpenAI_API
        return OpenAI_API(api_key, **kwargs)  # type: ignore
    if provider == "anthropic":
        from frameleap.utils.llm_api import Anthropic_API
        return Anthropic_API(api_key, **kwargs)  # type: ignore

    raise ValueError(
        f"Unknown provider: {provider}. "
        f"Supported: {', '.join(list(factories.keys()) + ['openai', 'anthropic'])}"
    )


def create_image_api(
    provider: str,
    api_key: str,
    **kwargs: Any,
) -> BaseImageAPI:
    """创建图像生成API - 优先国内服务

    Args:
        provider: 提供商名称
            - "flux_cn": Flux国内镜像
            - "qwen_image": 通义万相
            - "openai": DALL-E (备用)
            - "stability": Stability AI (备用)
        api_key: API密钥
        **kwargs: 其他参数

    Returns:
        图像生成API实例

    Raises:
        ValueError: 不支持的提供商

    Examples:
        >>> api = create_image_api("flux_cn", "sk-xxx")
        >>> image = api.generate("一只猫")
    """
    factories: dict[str, type[BaseImageAPI]] = {
        "flux_cn": FluxCN_API,
        "qwen_image": QwenImage_API,
    }

    if provider in factories:
        return factories[provider](api_key, **kwargs)

    # 备用国外服务
    if provider == "openai":
        from frameleap.utils.image_api import OpenAIImageAPI
        return OpenAIImageAPI(api_key)  # type: ignore
    if provider == "stability":
        from frameleap.utils.image_api import StabilityAPI
        return StabilityAPI(api_key)  # type: ignore

    raise ValueError(
        f"Unknown provider: {provider}. "
        f"Supported: {', '.join(list(factories.keys()) + ['openai', 'stability'])}"
    )


def create_tts_api(
    provider: str,
    api_key: str | None = None,
    **kwargs: Any,
) -> BaseTTSAPI:
    """创建TTS API

    Args:
        provider: 提供商名称
            - "fish": 鱼声AI
            - "xingtuo": 标贝TTS
        api_key: API密钥（鱼声需要，标贝需要app_id）
        **kwargs: 其他参数

    Returns:
        TTS API实例

    Raises:
        ValueError: 不支持的提供商

    Examples:
        >>> api = create_tts_api("fish", api_key="sk-xxx")
        >>> audio = api.synthesize("你好")
    """
    factories: dict[str, type[BaseTTSAPI]] = {
        "fish": FishAudio_API,
        "xingtuo": XingTuo_API,
    }

    if provider not in factories:
        raise ValueError(
            f"Unknown provider: {provider}. "
            f"Supported: {', '.join(factories.keys())}"
        )

    if provider == "fish":
        return FishAudio_API(api_key or kwargs["fish_key"])
    if provider == "xingtuo":
        return XingTuo_API(api_key, kwargs["app_id"])

    raise ValueError(f"Missing required parameters for {provider}")


__all__ = [
    # LLM
    "BaseLLMAPI",
    "DeepSeek_API",
    "Qwen_API",
    "Zhipu_API",
    "Kimi_API",
    # Image
    "BaseImageAPI",
    "FluxCN_API",
    "QwenImage_API",
    # TTS
    "BaseTTSAPI",
    "FishAudio_API",
    "XingTuo_API",
    # Factories
    "create_llm_api",
    "create_image_api",
    "create_tts_api",
]
