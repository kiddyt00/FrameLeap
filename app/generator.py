"""
FrameLeap - 剧本与图像生成器（4阶段版）

负责：
1. 输入处理
2. 剧本生成（使用千问LLM）
3. 场景描述生成
4. 图像生成（使用通义万相）
"""

from pathlib import Path
from typing import Callable
import time

from app.config import config, Config
from app.models import GenerationResult
from app.stages import (
    InputStage,
    ScriptGenerationStage,
    SceneDescriptionStage,
    ImageGenerationStage,
)
from app.stages import InputData
from app.utils.types import ProgressCallback, ErrorCallback

# 类型别名
GeneratorCallback = Callable[[str, float], None]


class Generator:
    """FrameLeap剧本与图像生成器（4阶段版）

    负责4个阶段的编排和执行：
    - 输入处理
    - 剧本生成（调用千问LLM）
    - 场景描述生成
    - 图像生成（调用通义万相）

    Attributes:
        cfg: 生成器配置
        input: 输入处理阶段
        script: 剧本生成阶段
        scene_desc: 场景描述生成阶段
        image: 图像生成阶段
    """

    def __init__(
        self,
        cfg: Config | None = None,
        progress_callback: ProgressCallback | None = None,
        error_callback: ErrorCallback | None = None,
    ) -> None:
        """初始化生成器

        Args:
            cfg: 配置对象，默认使用全局配置
            progress_callback: 进度回调函数，接收(stage_name, progress)参数
            error_callback: 错误回调函数，接收异常对象
        """
        self.cfg = cfg or config
        self._progress_callback = progress_callback
        self._error_callback = error_callback
        self._init_stages()

    def _init_stages(self) -> None:
        """初始化各阶段处理器（4个阶段）"""
        print("[DEBUG] _init_stages: Starting...")
        self.input = InputStage(self.cfg)
        print("[DEBUG] _init_stages: InputStage created")
        self.script = ScriptGenerationStage(self.cfg)
        print("[DEBUG] _init_stages: ScriptGenerationStage created")
        self.scene_desc = SceneDescriptionStage(self.cfg)
        print("[DEBUG] _init_stages: SceneDescriptionStage created")
        self.image = ImageGenerationStage(self.cfg)
        print("[DEBUG] _init_stages: ImageGenerationStage created")
        print("[DEBUG] _init_stages: All 4 stages created")

    def _report_progress(self, stage_name: str, progress: float) -> None:
        """报告进度

        Args:
            stage_name: 阶段名称
            progress: 进度值 (0.0 - 1.0)
        """
        if self._progress_callback:
            self._progress_callback(stage_name, progress)

    def _report_error(self, error: Exception) -> None:
        """报告错误

        Args:
            error: 异常对象
        """
        if self._error_callback:
            self._error_callback(error)

    def generate(
        self,
        text: str,
        style: str | None = None,
        duration: int | None = None,
        resolution: str | None = None,
    ) -> GenerationResult:
        """
        生成剧本和图像（4阶段流程）

        执行：输入处理 -> 剧本生成（LLM） -> 场景描述生成 -> 图像生成（通义万相）

        Args:
            text: 输入文本，一句话或短篇故事
            style: 风格 (anime, manhwa, manhua, watercolor等)
            duration: 目标时长(秒)，暂未使用
            resolution: 分辨率 (1080p, 1080p_v, 720p, 4k, cinema)

        Returns:
            GenerationResult: 生成结果对象，包含剧本数据和图像路径等信息

        Raises:
            EmptyInputError: 当输入文本为空时
            ConfigValidationError: 当配置无效时
            GenerationError: 当生成过程失败时
        """
        start = time.perf_counter()

        try:
            # 验证输入
            if not text or not text.strip():
                from app.exceptions import EmptyInputError
                raise EmptyInputError()

            # 更新配置
            if resolution:
                self.cfg.video = self.cfg.video.__class__.from_preset(resolution)
            if style:
                self.cfg.style.art_style = style

            # 阶段1: 输入处理
            self._report_progress("输入处理", 0.25)
            input_data = self.input.process(text, style)

            # 阶段2: 剧本生成（调用千问LLM）
            self._report_progress("剧本生成", 0.5)
            script = self.script.generate(input_data)

            # 阶段3: 场景描述生成
            self._report_progress("场景描述生成", 0.75)
            scene_descriptions = self.scene_desc.generate(script)

            # 阶段4: 图像生成（调用通义万相）
            self._report_progress("图像生成", 1.0)
            image_paths = self.image.generate(scene_descriptions)

            return GenerationResult(
                success=True,
                video_path=None,
                script=script,
                images=image_paths,
                generation_time=time.perf_counter() - start,
            )

        except Exception as e:
            self._report_error(e)
            return GenerationResult(
                success=False,
                error_message=str(e),
                generation_time=time.perf_counter() - start,
            )


def generate(
    text: str,
    style: str = "anime",
    resolution: str = "1080p",
    **kwargs
) -> GenerationResult:
    """
    快速生成剧本

    便捷函数，使用默认配置快速生成剧本

    Args:
        text: 输入文本
        style: 艺术风格，默认"anime"
        resolution: 输出分辨率，默认"1080p"
        **kwargs: 其他参数传递给Generator

    Returns:
        GenerationResult: 生成结果

    Examples:
        >>> generate("一个少年在雨夜中遇到了神秘少女")
        GenerationResult(success=True, script=..., ...)

        >>> generate("...", style="manhwa", resolution="1080p_v")
        GenerationResult(success=True, script=..., ...)
    """
    gen = Generator()
    return gen.generate(text, style=style, resolution=resolution, **kwargs)


__all__ = ["Generator", "generate"]
