"""
类型别名定义

集中定义项目中的类型别名，提高代码可读性和可维护性
"""

from typing import TypeAlias, Any, Callable
from pathlib import Path

# 基础类型别名
JSONDict: TypeAlias = dict[str, Any]
JSONList: TypeAlias = list[Any]
JSONValue: TypeAlias = str | int | float | bool | None | JSONDict | JSONList

# 路径相关
PathLike: TypeAlias = str | Path

# API相关
APIKey: TypeAlias = str
BaseURL: TypeAlias = str
ModelName: TypeAlias = str

# 生成相关
PromptText: TypeAlias = str
NegativePrompt: TypeAlias = str
StyleName: TypeAlias = str
ResolutionName: TypeAlias = str

# 配置相关
ConfigValue: TypeAlias = str | int | float | bool | list[str] | None

# 时间相关
Seconds: TypeAlias = float
Milliseconds: TypeAlias = int

# 字节数据
ImageData: TypeAlias = bytes
AudioData: TypeAlias = bytes

# ID类型
SceneID: TypeAlias = str
CharacterID: TypeAlias = str
ShotID: TypeAlias = str
NodeID: TypeAlias = str

# 回调函数类型
ProgressCallback: TypeAlias = Callable[[str, float], None]
ErrorCallback: TypeAlias = Callable[[Exception], None]

# 结果类型
ResultType: TypeAlias = JSONDict | list[JSONDict] | str | bytes | None


__all__ = [
    "JSONDict",
    "JSONList",
    "JSONValue",
    "PathLike",
    "APIKey",
    "BaseURL",
    "ModelName",
    "PromptText",
    "NegativePrompt",
    "StyleName",
    "ResolutionName",
    "ConfigValue",
    "Seconds",
    "Milliseconds",
    "ImageData",
    "AudioData",
    "SceneID",
    "CharacterID",
    "ShotID",
    "NodeID",
    "ProgressCallback",
    "ErrorCallback",
    "ResultType",
]
