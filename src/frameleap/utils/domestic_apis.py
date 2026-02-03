"""
国内API集成 - 优先使用，降低延迟

支持的国内服务：
- LLM: DeepSeek、通义千问、文心一言、智谱AI、Kimi
- 图像: Flux(国内镜像)、通义万相、百度文心一格
- TTS: 鱼声、标贝、出门问问、火山引擎
"""

from typing import Optional
import httpx
import json


class DeepSeek_API:
    """DeepSeek API - 国内首选，性价比高"""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = "deepseek-chat"

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 4000, **kwargs) -> str:
        """生成文本"""
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


class Qwen_API:
    """通义千问 API - 阿里云"""

    def __init__(self, api_key: str, base_url: str = "https://dashscope.aliyuncs.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = "qwen-turbo"

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 4000, **kwargs) -> str:
        """生成文本"""
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


class Zhipu_API:
    """智谱AI GLM - 清华系"""

    def __init__(self, api_key: str, base_url: str = "https://open.bigmodel.cn"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = "glm-4"

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 4000, **kwargs) -> str:
        """生成文本"""
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


class Kimi_API:
    """Kimi API - Moonshot"""

    def __init__(self, api_key: str, base_url: str = "https://api.moonshot.cn"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = "moonshot-v1-8k"

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 4000, **kwargs) -> str:
        """生成文本"""
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

class FluxCN_API:
    """Flux国内镜像API - 快速高质量"""

    def __init__(self, api_key: str, base_url: str = None):
        self.api_key = api_key
        # 使用国内中转服务
        self.base_url = base_url or "https://api.fluxcn.cn"

    def generate(self, prompt: str, negative: str = "", width: int = 1024, height: int = 1024, **kwargs) -> bytes:
        """生成图像"""
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
            import base64
            return base64.b64decode(result["image_base64"])
        else:
            raise ValueError("Unknown response format")


class QwenImage_API:
    """通义万相 - 阿里云图像生成"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://dashscope.aliyuncs.com"

    def generate(self, prompt: str, negative: str = "", width: int = 1024, height: int = 1024, **kwargs) -> bytes:
        """生成图像"""
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
            import base64
            return base64.b64decode(result["output"]["results"][0]["b64_image"])
        raise ValueError("Unknown response format")


# =============================================================================
# 国内TTS API
# =============================================================================

class FishAudio_API:
    """鱼声AI TTS - 高质量中文语音"""

    def __init__(self, api_key: str, base_url: str = "https://api.fish.audio"):
        self.api_key = api_key
        self.base_url = base_url

    def synthesize(self, text: str, voice_id: str = None, **kwargs) -> bytes:
        """合成语音"""
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


class XingTuo_API:
    """标贝TTS - 专业语音合成"""

    def __init__(self, api_key: str, app_id: str):
        self.api_key = api_key
        self.app_id = app_id
        self.base_url = "https://api.xfyun.cn"

    def synthesize(self, text: str, voice_id: str = None, **kwargs) -> bytes:
        """合成语音"""
        # 标贝API实现
        # TODO: 根据实际API文档实现
        raise NotImplementedError("标贝API待实现")


# =============================================================================
# API工厂 - 优先使用国内服务
# =============================================================================

def create_llm_api(provider: str, api_key: str, **kwargs) -> object:
    """创建LLM API - 优先国内服务"""
    factories = {
        "deepseek": lambda: DeepSeek_API(api_key),
        "qwen": lambda: Qwen_API(api_key),
        "zhipu": lambda: Zhipu_API(api_key),
        "kimi": lambda: Kimi_API(api_key),
        # 备用国外服务
        "openai": lambda: __import__("frameleap.utils.llm_api", fromlist=["OpenAI_API"]).OpenAI_API(api_key),
        "anthropic": lambda: __import__("frameleap.utils.llm_api", fromlist=["Anthropic_API"]).Anthropic_API(api_key),
    }

    if provider not in factories:
        raise ValueError(f"Unknown provider: {provider}")

    return factories[provider]()


def create_image_api(provider: str, api_key: str, **kwargs) -> object:
    """创建图像生成API - 优先国内服务"""
    factories = {
        "flux_cn": lambda: FluxCN_API(api_key),
        "qwen_image": lambda: QwenImage_API(api_key),
        # 备用国外服务
        "openai": lambda: __import__("frameleap.utils.image_api", fromlist=["OpenAIImageAPI"]).OpenAIImageAPI(api_key),
        "stability": lambda: __import__("frameleap.utils.image_api", fromlist=["StabilityAPI"]).StabilityAPI(api_key),
    }

    if provider not in factories:
        raise ValueError(f"Unknown provider: {provider}")

    return factories[provider]()


def create_tts_api(provider: str, api_key: str = None, **kwargs) -> object:
    """创建TTS API"""
    factories = {
        "fish": lambda: FishAudio_API(api_key or kwargs.get("fish_key")),
        "xingtuo": lambda: XingTuo_API(api_key, kwargs.get("app_id")),
    }

    if provider not in factories:
        raise ValueError(f"Unknown provider: {provider}")

    return factories[provider]()


__all__ = [
    "DeepSeek_API", "Qwen_API", "Zhipu_API", "Kimi_API",
    "FluxCN_API", "QwenImage_API",
    "FishAudio_API", "XingTuo_API",
    "create_llm_api", "create_image_api", "create_tts_api",
]
