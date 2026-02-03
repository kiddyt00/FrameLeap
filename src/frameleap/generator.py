"""
FrameLeap - 个人动态漫生成器

单用户版本，简化使用
"""

from pathlib import Path
from typing import Callable
import time

from frameleap.config import config, Config
from frameleap.models import GenerationResult
from frameleap.stages import (
    InputStage,
    ScriptGenerationStage,
    SceneDescriptionStage,
    ImageGenerationStage,
    StoryboardStage,
    AnimationStage,
    AudioGenerationStage,
    TextSubtitleStage,
    CompositionRenderingStage,
    OutputDeliveryStage,
)
from frameleap.stages import (
    InputData,
    StoryboardData,
    AnimationData,
    AudioData,
    TextLayerData,
    VideoData,
)
from frameleap.utils.types import ProgressCallback, ErrorCallback

# 类型别名
GeneratorCallback = Callable[[str, float], None]


class Generator:
    """FrameLeap生成器（个人版）

    负责10个阶段的编排和执行，提供端到端的动态漫生成功能

    Attributes:
        cfg: 生成器配置
        input: 输入处理阶段
        script: 剧本生成阶段
        scene_desc: 场景描述生成阶段
        image: 图像生成阶段
        storyboard: 分镜编排阶段
        animation: 动画化阶段
        audio: 音频生成阶段
        text: 文字字幕阶段
        compose: 合成渲染阶段
        output: 输出交付阶段
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
        """初始化各阶段处理器"""
        self.input = InputStage(self.cfg)
        self.script = ScriptGenerationStage(self.cfg)
        self.scene_desc = SceneDescriptionStage(self.cfg)
        self.image = ImageGenerationStage(self.cfg)
        self.storyboard = StoryboardStage(self.cfg)
        self.animation = AnimationStage(self.cfg)
        self.audio = AudioGenerationStage(self.cfg)
        self.text = TextSubtitleStage(self.cfg)
        self.compose = CompositionRenderingStage(self.cfg)
        self.output = OutputDeliveryStage(self.cfg)

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
        生成动态漫

        执行完整的10阶段流程：输入 -> 剧本 -> 画面描述 -> 图像生成
        -> 分镜编排 -> 动画化 -> 音频生成 -> 文字字幕 -> 合成渲染 -> 输出

        Args:
            text: 输入文本，一句话或短篇故事
            style: 风格 (anime, manhwa, manhua, watercolor等)
            duration: 目标时长(秒)，暂未使用
            resolution: 分辨率 (1080p, 1080p_v, 720p, 4k, cinema)

        Returns:
            GenerationResult: 生成结果对象，包含成功状态、视频路径等信息

        Raises:
            EmptyInputError: 当输入文本为空时
            ConfigValidationError: 当配置无效时
            GenerationError: 当生成过程失败时
        """
        start = time.perf_counter()

        try:
            # 验证输入
            if not text or not text.strip():
                from frameleap.exceptions import EmptyInputError
                raise EmptyInputError()

            # 更新配置
            if resolution:
                self.cfg.video = self.cfg.video.__class__.from_preset(resolution)
            if style:
                self.cfg.style.art_style = style

            # 阶段1: 输入处理
            self._report_progress("输入处理", 0.1)
            input_data = self.input.process(text)

            # 阶段2: 剧本生成
            self._report_progress("剧本生成", 0.2)
            script = self.script.generate(input_data)

            # 阶段3: 画面描述生成
            self._report_progress("画面描述", 0.3)
            scenes = self.scene_desc.generate(script)

            # 阶段4: 图像生成
            self._report_progress("图像生成", 0.4)
            images = self.image.generate(scenes)

            # 阶段5: 分镜编排
            self._report_progress("分镜编排", 0.5)
            storyboard = self.storyboard.arrange(script, images)

            # 阶段6: 动画化
            self._report_progress("动画化", 0.6)
            animations = self.animation.animate(storyboard)

            # 阶段7: 音频生成
            self._report_progress("音频生成", 0.7)
            audio = self.audio.generate(script)

            # 阶段8: 文字字幕
            self._report_progress("文字字幕", 0.8)
            text_layers = self.text.generate(script)

            # 阶段9: 合成渲染
            self._report_progress("合成渲染", 0.9)
            video = self.compose.compose(animations, audio, text_layers)

            # 阶段10: 输出交付
            self._report_progress("输出交付", 1.0)
            output_path = self.output.deliver(video)

            return GenerationResult(
                success=True,
                video_path=str(output_path),
                script=script,
                images=images,
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
    快速生成动态漫

    便捷函数，使用默认配置快速生成动态漫

    Args:
        text: 输入文本
        style: 艺术风格，默认"anime"
        resolution: 输出分辨率，默认"1080p"
        **kwargs: 其他参数传递给Generator

    Returns:
        GenerationResult: 生成结果

    Examples:
        >>> generate("一个少年在雨夜中遇到了神秘少女")
        GenerationResult(success=True, video_path="/path/to/output.mp4", ...)

        >>> generate("...", style="manhwa", resolution="1080p_v")
        GenerationResult(success=True, video_path="/path/to/output.mp4", ...)
    """
    gen = Generator()
    return gen.generate(text, style=style, resolution=resolution, **kwargs)


__all__ = ["Generator", "generate"]
