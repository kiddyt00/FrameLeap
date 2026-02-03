"""
图像生成API集成

支持多种图像生成服务
"""

from pathlib import Path
from typing import Optional
import httpx
import base64


class ImageGenAPI:
    """图像生成API基类"""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url

    def generate(self, prompt: str, negative: str = "", **kwargs) -> bytes:
        """生成图像，返回图像数据"""
        raise NotImplementedError


class OpenAIImageAPI(ImageGenAPI):
    """OpenAI DALL-E API"""

    def __init__(self, api_key: str):
        super().__init__(api_key, "https://api.openai.com/v1")

    def generate(self, prompt: str, negative: str = "", **kwargs) -> bytes:
        """使用DALL-E生成图像"""
        import httpx

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": kwargs.get("size", "1024x1024"),
            "quality": kwargs.get("quality", "standard"),
        }

        response = httpx.post(
            f"{self.base_url}/images/generations",
            headers=headers,
            json=data,
            timeout=60.0,
        )

        response.raise_for_status()
        result = response.json()

        # 获取图像URL并下载
        image_url = result["data"][0]["url"]
        img_response = httpx.get(image_url)
        return img_response.content


class StabilityAPI(ImageGenAPI):
    """Stability AI (Stable Diffusion) API"""

    def __init__(self, api_key: str):
        super().__init__(api_key, "https://api.stability.ai")

    def generate(
        self,
        prompt: str,
        negative: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 30,
        cfg_scale: float = 7.5,
        **kwargs
    ) -> bytes:
        """使用Stability AI生成图像"""
        import httpx

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "image/png",
        }

        # 使用SDXL模型
        url = f"{self.base_url}/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"

        body = {
            "text_prompts": [
                {"text": prompt, "weight": 1.0},
                {"text": negative, "weight": -1.0} if negative else None,
            ],
            "cfg_scale": cfg_scale,
            "height": height,
            "width": width,
            "steps": steps,
            "samples": 1,
        }

        # 移除None值
        body["text_prompts"] = [p for p in body["text_prompts"] if p is not None]

        response = httpx.post(url, headers=headers, json=body, timeout=120)
        response.raise_for_status()
        return response.content


class ReplicateAPI(ImageGenAPI):
    """Replicate API（支持多种模型）"""

    def __init__(self, api_key: str):
        super().__init__(api_key, "https://api.replicate.com")

    def generate(
        self,
        prompt: str,
        negative: str = "",
        model: str = "stability-ai/sdxl",
        **kwargs
    ) -> bytes:
        """使用Replicate生成图像"""
        import httpx
        import time

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # 创建预测
        create_response = httpx.post(
            f"{self.base_url}/v1/predictions",
            headers=headers,
            json={
                "version": self._get_model_version(model),
                "input": {
                    "prompt": prompt,
                    "negative_prompt": negative,
                    "width": kwargs.get("width", 1024),
                    "height": kwargs.get("height", 1024),
                }
            },
        )

        create_response.raise_for_status()
        prediction = create_response.json()

        # 轮询结果
        get_url = prediction["urls"]["get"]
        while True:
            response = httpx.get(get_url, headers=headers)
            response.raise_for_status()
            result = response.json()

            if result["status"] == "succeeded":
                # 下载图像
                image_url = result["output"][0]
                img_response = httpx.get(image_url)
                return img_response.content
            elif result["status"] in ["failed", "canceled"]:
                raise RuntimeError(f"Generation failed: {result.get('error')}")

            time.sleep(1)

    def _get_model_version(self, model: str) -> str:
        """获取模型版本"""
        versions = {
            "stability-ai/sdxl": "8beff3369e845b1df2f8f0a15874b2c1e2da02796b1f389519c39aaac8c345",
            "flux": "flux-realism",
        }
        return versions.get(model, versions["stability-ai/sdxl"])


class LocalSDAPI(ImageGenAPI):
    """本地Stable Diffusion API（ComfyUI/A1111）"""

    def __init__(self, base_url: str = "http://127.0.0.1:7860"):
        super().__init__("", base_url)

    def generate(
        self,
        prompt: str,
        negative: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 30,
        cfg_scale: float = 7.5,
        **kwargs
    ) -> bytes:
        """使用本地SD生成图像"""
        import httpx

        url = f"{self.base_url}/sdapi/v1/txt2img"

        payload = {
            "prompt": prompt,
            "negative_prompt": negative,
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "save_images": False,
        }

        response = httpx.post(url, json=payload, timeout=300)
        response.raise_for_status()

        result = response.json()
        # base64编码的图像
        image_data = base64.b64decode(result["images"][0])
        return image_data


def create_image_api(provider: str, **kwargs) -> ImageGenAPI:
    """创建图像生成API实例"""
    factories = {
        "openai": lambda: OpenAIImageAPI(kwargs["api_key"]),
        "stability": lambda: StabilityAPI(kwargs["api_key"]),
        "replicate": lambda: ReplicateAPI(kwargs["api_key"]),
        "local": lambda: LocalSDAPI(kwargs.get("base_url", "http://127.0.0.1:7860")),
    }

    if provider not in factories:
        raise ValueError(f"Unknown provider: {provider}")

    return factories[provider]()


__all__ = [
    "ImageGenAPI",
    "OpenAIImageAPI",
    "StabilityAPI",
    "ReplicateAPI",
    "LocalSDAPI",
    "create_image_api",
]
