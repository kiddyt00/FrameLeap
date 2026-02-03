"""
FrameLeap 异常类层次结构

定义项目中所有自定义异常，提供清晰的错误分类和处理
"""

from typing import Any


# =============================================================================
# 基础异常
# =============================================================================

class FrameLeapError(Exception):
    """FrameLeap 基础异常类

    所有自定义异常的基类，提供统一的错误处理接口
    """

    def __init__(self, message: str, *, code: str | None = None, details: dict[str, Any] | None = None):
        """初始化异常

        Args:
            message: 错误信息
            code: 错误代码，用于程序化处理
            details: 额外的错误详情
        """
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (详情: {self.details})"
        return self.message

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式，便于序列化"""
        return {
            "error_type": self.__class__.__name__,
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


# =============================================================================
# 配置相关异常
# =============================================================================

class ConfigError(FrameLeapError):
    """配置错误基类"""

    pass


class ConfigValidationError(ConfigError):
    """配置验证失败

    当配置值不符合预期格式或范围时抛出
    """

    def __init__(self, message: str, field: str, value: Any):
        super().__init__(message, details={"field": field, "value": str(value)})
        self.field = field
        self.value = value


class ConfigNotFoundError(ConfigError):
    """配置文件未找到"""

    def __init__(self, path: str):
        super().__init__(f"配置文件未找到: {path}", details={"path": path})
        self.path = path


# =============================================================================
# API相关异常
# =============================================================================

class APIError(FrameLeapError):
    """API调用错误基类"""

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        status_code: int | None = None,
        response_text: str | None = None,
    ):
        super().__init__(message, details={
            "provider": provider,
            "status_code": status_code,
            "response": response_text[:200] if response_text else None,
        })
        self.provider = provider
        self.status_code = status_code
        self.response_text = response_text


class APIConnectionError(APIError):
    """API连接错误

    网络问题、超时或DNS解析失败
    """

    def __init__(self, message: str, *, provider: str, url: str | None = None):
        super().__init__(message, provider=provider)
        if url:
            self.details["url"] = url
        self.url = url


class APIAuthenticationError(APIError):
    """API认证错误

    API密钥无效、过期或权限不足
    """

    def __init__(self, message: str, *, provider: str):
        super().__init__(message, provider=provider, status_code=401)


class APIRateLimitError(APIError):
    """API速率限制错误

    请求过于频繁，超过速率限制
    """

    def __init__(self, message: str, *, provider: str, retry_after: int | None = None):
        super().__init__(message, provider=provider, status_code=429)
        self.retry_after = retry_after
        if retry_after:
            self.details["retry_after"] = retry_after


class APIResponseError(APIError):
    """API响应错误

    服务器返回错误响应
    """

    pass


class APITimeoutError(APIError):
    """API超时错误"""

    def __init__(self, message: str, *, provider: str, timeout: float):
        super().__init__(message, provider=provider)
        self.timeout = timeout
        self.details["timeout"] = timeout


# =============================================================================
# 生成相关异常
# =============================================================================

class GenerationError(FrameLeapError):
    """生成过程错误基类"""

    pass


class ScriptGenerationError(GenerationError):
    """剧本生成错误"""

    pass


class ImageGenerationError(GenerationError):
    """图像生成错误"""

    def __init__(self, message: str, *, scene_id: str | None = None, prompt: str | None = None):
        super().__init__(message, details={
            "scene_id": scene_id,
            "prompt": prompt[:100] if prompt else None,
        })
        self.scene_id = scene_id
        self.prompt = prompt


class AudioGenerationError(GenerationError):
    """音频生成错误"""

    pass


class VideoCompositionError(GenerationError):
    """视频合成错误"""

    pass


# =============================================================================
# 输入相关异常
# =============================================================================

class InputError(FrameLeapError):
    """输入错误基类"""

    pass


class InvalidInputError(InputError):
    """无效输入错误"""

    def __init__(self, message: str, *, field: str | None = None, value: Any = None):
        super().__init__(message, details={"field": field, "value": str(value) if value else None})
        self.field = field
        self.value = value


class EmptyInputError(InvalidInputError):
    """空输入错误"""

    def __init__(self, message: str = "输入内容不能为空"):
        super().__init__(message, field="input")


# =============================================================================
# 文件相关异常
# =============================================================================

class FileError(FrameLeapError):
    """文件操作错误基类"""

    def __init__(self, message: str, *, path: str | None = None):
        super().__init__(message, details={"path": path})
        self.path = path


class FileNotFoundError(FileError):
    """文件未找到"""

    pass


class FileReadError(FileError):
    """文件读取错误"""

    pass


class FileWriteError(FileError):
    """文件写入错误"""

    pass


# =============================================================================
# 资源相关异常
# =============================================================================

class ResourceError(FrameLeapError):
    """资源错误基类"""

    pass


class OutOfMemoryError(ResourceError):
    """内存不足错误"""

    def __init__(self, message: str = "内存不足", *, required: int | None = None, available: int | None = None):
        super().__init__(message, details={
            "required_mb": required,
            "available_mb": available,
        })


class GPUResourceError(ResourceError):
    """GPU资源错误"""

    def __init__(self, message: str, *, vram_required: int | None = None, vram_available: int | None = None):
        super().__init__(message, details={
            "vram_required_mb": vram_required,
            "vram_available_mb": vram_available,
        })


class DiskSpaceError(ResourceError):
    """磁盘空间不足"""

    def __init__(self, message: str, *, required: int | None = None, available: int | None = None):
        super().__init__(message, details={
            "required_mb": required,
            "available_mb": available,
        })


# =============================================================================
# 验证相关异常
# =============================================================================

class ValidationError(FrameLeapError):
    """验证错误基类"""

    def __init__(self, message: str, *, field: str | None = None, constraint: str | None = None):
        super().__init__(message, details={
            "field": field,
            "constraint": constraint,
        })
        self.field = field
        self.constraint = constraint


class ConsistencyError(ValidationError):
    """一致性验证错误

    用于角色一致性、场景一致性等检查
    """

    def __init__(self, message: str, *, item_type: str, item_id: str):
        super().__init__(message, details={
            "type": item_type,
            "id": item_id,
        })
        self.item_type = item_type
        self.item_id = item_id


# =============================================================================
# 导出列表
# =============================================================================

__all__ = [
    # 基础
    "FrameLeapError",
    # 配置
    "ConfigError",
    "ConfigValidationError",
    "ConfigNotFoundError",
    # API
    "APIError",
    "APIConnectionError",
    "APIAuthenticationError",
    "APIRateLimitError",
    "APIResponseError",
    "APITimeoutError",
    # 生成
    "GenerationError",
    "ScriptGenerationError",
    "ImageGenerationError",
    "AudioGenerationError",
    "VideoCompositionError",
    # 输入
    "InputError",
    "InvalidInputError",
    "EmptyInputError",
    # 文件
    "FileError",
    "FileNotFoundError",
    "FileReadError",
    "FileWriteError",
    # 资源
    "ResourceError",
    "OutOfMemoryError",
    "GPUResourceError",
    "DiskSpaceError",
    # 验证
    "ValidationError",
    "ConsistencyError",
]
