"""
FrameLeap主生成器

协调整个动态漫生成流程
"""

import logging
from pathlib import Path
from typing import Optional

from frameleap.config import Settings
from frameleap.models import (
    ScriptData,
    GenerationResult,
)
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

logger = logging.getLogger(__name__)


class FrameLeapGenerator:
    """
    FrameLeap动态漫生成器

    这是整个系统的主入口类，负责协调整个10阶段的生成流程。
    """

    def __init__(self, settings: Optional[Settings] = None):
        """
        初始化生成器

        Args:
            settings: 配置对象，如果为None则使用默认配置
        """
        self.settings = settings or Settings()
        self._setup_stages()

        # 配置日志
        if not logging.getLogger("frameleap").handlers:
            setup_logging(
                level=self.settings.log_level,
                log_file=str(self.settings.paths.work_dir / "frameleap.log"),
            )

        logger.info("FrameLeap generator initialized")

    def _setup_stages(self):
        """初始化所有阶段"""
        self.input_stage = InputStage(self.settings)
        self.script_stage = ScriptGenerationStage(self.settings)
        self.scene_desc_stage = SceneDescriptionStage(self.settings)
        self.image_stage = ImageGenerationStage(self.settings)
        self.storyboard_stage = StoryboardStage(self.settings)
        self.animation_stage = AnimationStage(self.settings)
        self.audio_stage = AudioGenerationStage(self.settings)
        self.text_stage = TextSubtitleStage(self.settings)
        self.composition_stage = CompositionRenderingStage(self.settings)
        self.output_stage = OutputDeliveryStage(self.settings)

    def generate(
        self,
        input_text: str,
        style: Optional[str] = None,
        duration: Optional[int] = None,
        resolution: Optional[str] = None,
        **kwargs
    ) -> GenerationResult:
        """
        生成动态漫

        Args:
            input_text: 输入文本（一句话或短文）
            style: 艺术风格（如：anime, realistic, watercolor等）
            duration: 目标时长（秒）
            resolution: 分辨率预设（如：1080p, 720p, 4k等）
            **kwargs: 其他参数

        Returns:
            GenerationResult: 生成结果
        """
        import time
        start_time = time.perf_counter()

        logger.info(f"Starting generation with input: {input_text[:50]}...")

        try:
            # 更新配置
            if resolution:
                self.settings.video = self.settings.video.__class__.from_preset(resolution)
            if duration:
                self.settings.video.duration = duration
            if style:
                self.settings.style.art_style = style

            # 阶段1：输入处理
            logger.info("Stage 1: Processing input...")
            input_data = self.input_stage.process(
                text=input_text,
                style=style,
                duration=duration,
            )

            # 阶段2：剧本生成
            logger.info("Stage 2: Generating script...")
            script = self.script_stage.generate(input_data)
            logger.info(f"Generated {len(script.scenes)} scenes")

            # 阶段3：画面描述生成
            logger.info("Stage 3: Generating scene descriptions...")
            scene_descriptions = self.scene_desc_stage.generate(script)

            # 阶段4：图像生成
            logger.info("Stage 4: Generating images...")
            images = self.image_stage.generate(scene_descriptions)
            logger.info(f"Generated {len(images)} images")

            # 阶段5：分镜编排
            logger.info("Stage 5: Creating storyboard...")
            storyboard = self.storyboard_stage.arrange(script, images)

            # 阶段6：动画化
            logger.info("Stage 6: Animating...")
            animations = self.animation_stage.animate(storyboard)

            # 阶段7：音频生成
            logger.info("Stage 7: Generating audio...")
            audio = self.audio_stage.generate(script)

            # 阶段8：文字与字幕
            logger.info("Stage 8: Adding text and subtitles...")
            text_layers = self.text_stage.generate(script)

            # 阶段9：合成渲染
            logger.info("Stage 9: Composing and rendering...")
            video = self.composition_stage.compose(
                animations=animations,
                audio=audio,
                text=text_layers,
            )

            # 阶段10：输出交付
            logger.info("Stage 10: Delivering output...")
            output_path = self.output_stage.deliver(video)

            elapsed = time.perf_counter() - start_time
            logger.info(f"Generation completed in {elapsed:.2f} seconds")

            return GenerationResult(
                success=True,
                video_path=str(output_path),
                script=script,
                images=images,
                audio=audio,
                generation_time=elapsed,
            )

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"Generation failed after {elapsed:.2f} seconds: {e}")
            return GenerationResult(
                success=False,
                error_message=str(e),
                generation_time=elapsed,
            )

    def generate_from_file(self, input_file: str | Path, **kwargs) -> GenerationResult:
        """
        从文件生成动态漫

        Args:
            input_file: 输入文件路径
            **kwargs: 其他参数

        Returns:
            GenerationResult: 生成结果
        """
        path = Path(input_file)
        text = path.read_text(encoding="utf-8")
        return self.generate(text, **kwargs)


def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """设置日志系统"""
    import logging
    from frameleap.utils import setup_logging as _setup_logging

    return _setup_logging(level=level, log_file=log_file)


__all__ = ["FrameLeapGenerator"]
