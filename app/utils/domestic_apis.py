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

from app.utils.http_client import BaseHTTPClient
from app.utils.types import ImageData, AudioData


# =============================================================================
# 国内LLM API
# =============================================================================

class BaseLLMAPI(BaseHTTPClient):
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
        super().__init__(api_key, base_url)
        self.model = model


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
    ) -> None:
        """初始化DeepSeek API客户端"""
        super().__init__(api_key, "deepseek-chat", "https://api.deepseek.com")

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs: Any,
    ) -> str:
        """生成文本"""
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        response = self.post("/v1/chat/completions", data=data)
        result = self.parse_json_response(response)
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
    ) -> None:
        """初始化通义千问 API客户端"""
        super().__init__(api_key, "qwen-turbo", "https://dashscope.aliyuncs.com")

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs: Any,
    ) -> str:
        """生成文本"""
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

        response = self.post(
            "/api/v1/services/aigc/text-generation/generation",
            data=data
        )
        result = self.parse_json_response(response)

        # 检查是否有错误
        if "code" in result and result["code"] != "Success":
            raise ValueError(f"Qwen API Error: {result.get('message', 'Unknown error')}")

        # 使用 result_format: "message" 时的响应格式
        return result["output"]["choices"][0]["message"]["content"]


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
    ) -> None:
        """初始化智谱AI API客户端"""
        super().__init__(api_key, "glm-4", "https://open.bigmodel.cn")

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs: Any,
    ) -> str:
        """生成文本"""
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        response = self.post("/api/paas/v4/chat/completions", data=data)
        result = self.parse_json_response(response)
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
    ) -> None:
        """初始化Kimi API客户端"""
        super().__init__(api_key, "moonshot-v1-8k", "https://api.moonshot.cn")

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs: Any,
    ) -> str:
        """生成文本"""
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        response = self.post("/v1/chat/completions", data=data)
        result = self.parse_json_response(response)
        return result["choices"][0]["message"]["content"]


# =============================================================================
# 国内图像生成API
# =============================================================================

class BaseImageAPI(BaseHTTPClient):
    """图像生成API基类"""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        negative: str = "",
        width: int = 1024,
        height: int = 1024,
        **kwargs: Any,
    ) -> ImageData:
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
        base_url: str = "https://api.fluxcn.cn",
    ) -> None:
        """初始化FluxCN API客户端"""
        super().__init__(api_key, base_url)

    def generate(
        self,
        prompt: str,
        negative: str = "",
        width: int = 1024,
        height: int = 1024,
        **kwargs: Any,
    ) -> ImageData:
        """生成图像"""
        data = {
            "prompt": prompt,
            "negative_prompt": negative,
            "width": width,
            "height": height,
            "steps": kwargs.get("steps", 28),
            "guidance_scale": kwargs.get("cfg_scale", 7.5),
        }

        response = self.post("/v1/generate", data=data)
        result = self.parse_json_response(response)

        # 下载图像
        if "image_url" in result:
            img_response = self.get(result["image_url"])
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
        """初始化通义万相 API客户端"""
        super().__init__(api_key, "https://dashscope.aliyuncs.com")

    @property
    def headers(self) -> dict[str, str]:
        """获取默认请求头（添加异步调用支持）"""
        base_headers = super().headers
        base_headers["X-DashScope-Async"] = "enable"
        return base_headers

    def generate(
        self,
        prompt: str,
        negative: str = "",
        width: int = 1024,
        height: int = 1024,
        **kwargs: Any,
    ) -> ImageData:
        """生成图像（异步模式）"""
        import time

        # 步骤1: 提交任务
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

        print(f"[DEBUG] 提交通义万相任务（异步模式）...")
        response = self.post(
            "/api/v1/services/aigc/text2image/image-synthesis",
            data=data
        )
        result = self.parse_json_response(response)

        print(f"[DEBUG] 任务提交响应: {result}")

        # 检查是否有错误（空code表示成功）
        if "code" in result:
            code = result["code"]
            if code and code != "Success" and code != "":
                error_msg = result.get("message", "未知错误")
                if code == "AccessDenied":
                    raise ValueError(f"访问被拒绝: {error_msg}。可能需要添加异步请求头或检查API密钥权限。")
                elif code == "Throttling.RateQuota":
                    raise ValueError(f"速率限制: {error_msg}。请稍后再试。")
                else:
                    raise ValueError(f"通义万相API错误 [{code}]: {error_msg}")

        # 获取task_id
        if "output" not in result or "task_id" not in result["output"]:
            print(f"[ERROR] 未知的响应格式: {result}")
            raise ValueError(f"Unknown response format. Keys: {result.keys()}")

        task_id = result["output"]["task_id"]
        print(f"[DEBUG] 任务ID: {task_id}")

        # 步骤2: 轮询任务结果
        max_wait = 120  # 最多等待120秒
        interval = 3    # 每3秒检查一次（降低频率避免速率限制）
        waited = 0

        while waited < max_wait:
            time.sleep(interval)
            waited += interval

            print(f"[DEBUG] 查询任务状态 ({waited}s)...")

            # 查询任务结果
            result_response = self.get(
                f"/api/v1/tasks/{task_id}"
            )
            task_result = self.parse_json_response(result_response)

            # 检查任务状态
            if "output" in task_result:
                task_status = task_result["output"].get("task_status", "")
                print(f"[DEBUG] 任务状态: {task_status}")

                if task_status == "SUCCEEDED":
                    # 任务成功，获取结果
                    results = task_result["output"].get("results", [])
                    if results and "url" in results[0]:
                        image_url = results[0]["url"]
                        print(f"[DEBUG] 图像URL: {image_url}")

                        # 下载图像（使用完整URL）
                        import httpx
                        img_response = httpx.get(image_url, timeout=60.0)
                        if img_response.status_code == 200:
                            print(f"[DEBUG] 图像下载成功，大小: {len(img_response.content)} 字节")
                            return img_response.content
                        else:
                            raise ValueError(f"图像下载失败: HTTP {img_response.status_code}")

                    # 如果有b64_image字段
                    if results and "b64_image" in results[0]:
                        return base64.b64decode(results[0]["b64_image"])

                elif task_status == "FAILED":
                    error_msg = task_result["output"].get("message", "未知错误")
                    raise ValueError(f"通义万相任务失败: {error_msg}")

                # 任务仍在处理中（PENDING, RUNNING），继续等待

        raise ValueError(f"通义万相任务超时（等待{max_wait}秒）")


# =============================================================================
# 国内TTS API
# =============================================================================

class BaseTTSAPI(BaseHTTPClient):
    """TTS API基类"""

    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        **kwargs: Any,
    ) -> AudioData:
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
    ) -> None:
        """初始化鱼声API客户端"""
        super().__init__(api_key, "https://api.fish.audio")

    def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        **kwargs: Any,
    ) -> AudioData:
        """合成语音"""
        data = {
            "text": text,
            "voice": voice_id or "female_qingxin",
            "speed": kwargs.get("speed", 1.0),
            "format": "mp3",
        }

        response = self.post("/v1/tts", data=data)

        # 返回音频数据
        if response.headers.get("content-type", "").startswith("audio"):
            return response.content

        result = self.parse_json_response(response)
        if "audio_url" in result:
            audio_response = self.get(result["audio_url"])
            return audio_response.content

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
        """初始化标贝API客户端"""
        super().__init__(api_key, "https://api.xfyun.cn")
        self.app_id = app_id

    def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        **kwargs: Any,
    ) -> AudioData:
        """合成语音"""
        # 标贝API实现
        # TODO: 根据实际API文档实现
        raise NotImplementedError("标贝API待实现")


class QwenTTS_API(BaseTTSAPI):
    """通义千问TTS - 阿里云语音合成

    使用CosyVoice或Sambert模型进行语音合成

    支持音色:
    - Cherry: 活泼女声
    - Aijia: 温柔女声
    - Aida: 沉稳女声
    - Aimei: 甜美女声
    - Zhichu: 知性女声
    - Aixia: 活泼女声
    - Aibin: 沉稳男声
    - Aitong: 童声
    - Aiyue: 温暖女声

    Example:
        >>> api = QwenTTS_API("sk-xxx")
        >>> audio_data = api.synthesize("你好世界", voice_id="Cherry")
    """

    def __init__(
        self,
        api_key: str,
    ) -> None:
        """初始化通义千问TTS API客户端"""
        super().__init__(api_key, "https://dashscope.aliyuncs.com")

    @property
    def headers(self) -> dict[str, str]:
        """获取默认请求头"""
        base_headers = super().headers
        base_headers["X-DashScope-Async"] = "enable"
        return base_headers

    def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        **kwargs: Any,
    ) -> AudioData:
        """合成语音（使用HTTP REST API）"""
        import time

        # 默认使用 Cherry 音色
        voice = voice_id or kwargs.get("voice", "Cherry")

        # 步骤1: 提交任务
        data = {
            "model": "cosyvoice-v1",
            "input": {
                "text": text
            },
            "parameters": {
                "text_type": "PlainText",
                "voice": voice,
                # 可选参数
                "sample_rate": kwargs.get("sample_rate", 24000),
                "format": kwargs.get("format", "mp3"),
                "rate": kwargs.get("rate", 1.0),  # 语速，范围0.5-2.0
                "volume": kwargs.get("volume", 50),  # 音量，范围0-100
            }
        }

        print(f"[DEBUG] 提交通义千问TTS任务...")
        response = self.post(
            "/api/v1/services/audio/generation/generation",
            data=data
        )
        result = self.parse_json_response(response)

        print(f"[DEBUG] TTS任务提交响应: {result}")

        # 检查是否有错误
        if "code" in result:
            code = result["code"]
            if code and code != "Success" and code != "":
                error_msg = result.get("message", "未知错误")
                raise ValueError(f"通义千问TTS API错误 [{code}]: {error_msg}")

        # 获取task_id
        if "output" not in result or "task_id" not in result["output"]:
            print(f"[ERROR] 未知的响应格式: {result}")
            raise ValueError(f"Unknown response format. Keys: {result.keys()}")

        task_id = result["output"]["task_id"]
        print(f"[DEBUG] TTS任务ID: {task_id}")

        # 步骤2: 轮询任务结果
        max_wait = 60  # 最多等待60秒
        interval = 1   # 每1秒检查一次
        waited = 0

        while waited < max_wait:
            time.sleep(interval)
            waited += interval

            print(f"[DEBUG] 查询TTS任务状态 ({waited}s)...")

            # 查询任务结果
            result_response = self.get(
                f"/api/v1/tasks/{task_id}"
            )
            task_result = self.parse_json_response(result_response)

            # 检查任务状态
            if "output" in task_result:
                task_status = task_result["output"].get("task_status", "")
                print(f"[DEBUG] TTS任务状态: {task_status}")

                if task_status == "SUCCEEDED":
                    # 任务成功，获取结果
                    output_url = task_result["output"].get("output_url", "")
                    if output_url:
                        print(f"[DEBUG] 音频URL: {output_url}")

                        # 下载音频（使用完整URL）
                        import httpx
                        audio_response = httpx.get(output_url, timeout=60.0)
                        if audio_response.status_code == 200:
                            print(f"[DEBUG] 音频下载成功，大小: {len(audio_response.content)} 字节")
                            return audio_response.content
                        else:
                            raise ValueError(f"音频下载失败: HTTP {audio_response.status_code}")

                elif task_status == "FAILED":
                    error_msg = task_result["output"].get("message", "未知错误")
                    raise ValueError(f"通义千问TTS任务失败: {error_msg}")

                # 任务仍在处理中（PENDING, RUNNING），继续等待

        raise ValueError(f"通义千问TTS任务超时（等待{max_wait}秒）")


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
        api_key: API密钥
        **kwargs: 其他参数

    Returns:
        LLM API实例
    """
    factories: dict[str, type[BaseLLMAPI]] = {
        "deepseek": DeepSeek_API,
        "qwen": Qwen_API,
        "zhipu": Zhipu_API,
        "kimi": Kimi_API,
    }

    if provider not in factories:
        raise ValueError(
            f"Unknown provider: {provider}. "
            f"Supported: {', '.join(factories.keys())}"
        )

    return factories[provider](api_key, **kwargs)


def create_image_api(
    provider: str,
    api_key: str,
    **kwargs: Any,
) -> BaseImageAPI:
    """创建图像生成API - 优先国内服务

    Args:
        provider: 提供商名称
        api_key: API密钥
        **kwargs: 其他参数

    Returns:
        图像生成API实例
    """
    factories: dict[str, type[BaseImageAPI]] = {
        "flux_cn": FluxCN_API,
        "qwen_image": QwenImage_API,
    }

    if provider not in factories:
        raise ValueError(
            f"Unknown provider: {provider}. "
            f"Supported: {', '.join(factories.keys())}"
        )

    return factories[provider](api_key, **kwargs)


def create_tts_api(
    provider: str,
    api_key: str | None = None,
    **kwargs: Any,
) -> BaseTTSAPI:
    """创建TTS API

    Args:
        provider: 提供商名称 (qwen, fish, xingtuo)
        api_key: API密钥
        **kwargs: 其他参数

    Returns:
        TTS API实例
    """
    factories: dict[str, type[BaseTTSAPI]] = {
        "qwen": QwenTTS_API,
        "fish": FishAudio_API,
        "xingtuo": XingTuo_API,
    }

    if provider not in factories:
        raise ValueError(
            f"Unknown provider: {provider}. "
            f"Supported: {', '.join(factories.keys())}"
        )

    if provider == "qwen":
        return QwenTTS_API(api_key)
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
    "QwenTTS_API",
    "FishAudio_API",
    "XingTuo_API",
    # Factories
    "create_llm_api",
    "create_image_api",
    "create_tts_api",
]
