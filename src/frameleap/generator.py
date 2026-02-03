"""
FrameLeap - 个人动态漫生成器

单用户版本，简化使用
"""

from pathlib import Path
from typing import Optional

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


class Generator:
    """FrameLeap生成器（个人版）"""

    def __init__(self, cfg: Optional[Config] = None):
        self.cfg = cfg or config
        self._init_stages()

    def _init_stages(self):
        """初始化各阶段"""
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

    def generate(
        self,
        text: str,
        style: str | None = None,
        duration: int | None = None,
        resolution: str | None = None,
    ) -> GenerationResult:
        """
        生成动态漫

        Args:
            text: 输入文本
            style: 风格 (anime, manhwa, manhua, watercolor等)
            duration: 时长(秒)
            resolution: 分辨率 (1080p, 1080p_v, 720p, 4k, cinema)

        Returns:
            生成结果
        """
        import time
        start = time.perf_counter()

        try:
            # 更新配置
            if resolution:
                self.cfg.video = self.cfg.video.__class__.from_preset(resolution)
            if style:
                self.cfg.style.art_style = style

            # 执行各阶段
            input_data = self.input.process(text)
            script = self.script.generate(input_data)
            scenes = self.scene_desc.generate(script)
            images = self.image.generate(scenes)
            storyboard = self.storyboard.arrange(script, images)
            animations = self.animation.animate(storyboard)
            audio = self.audio.generate(script)
            text_layers = self.text.generate(script)
            video = self.compose.compose(animations, audio, text_layers)
            output_path = self.output.deliver(video)

            return GenerationResult(
                success=True,
                video_path=str(output_path),
                script=script,
                images=images,
                generation_time=time.perf_counter() - start,
            )

        except Exception as e:
            return GenerationResult(
                success=False,
                error_message=str(e),
                generation_time=time.perf_counter() - start,
            )


# 便捷函数
def generate(
    text: str,
    style: str = "anime",
    resolution: str = "1080p",
    **kwargs
) -> GenerationResult:
    """
    快速生成动态漫

    示例:
        generate("一个少年在雨夜中遇到了神秘少女")
        generate("...", style="manhwa", resolution="1080p_v")
    """
    gen = Generator()
    return gen.generate(text, style=style, resolution=resolution, **kwargs)


__all__ = ["Generator", "generate"]
