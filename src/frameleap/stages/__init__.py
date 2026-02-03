"""
处理阶段模块 - 单用户简化版
"""

from abc import ABC, abstractmethod
from typing import Any
from pathlib import Path

from frameleap.config import Config
from frameleap.models import (
    ScriptData, SceneData, SceneElement, StoryType, CharacterData,
    CharacterAppearance, CharacterType, Emotion, Dialogue,
    ShotSize, CameraShot, TimeRange, TimelineData,
    AudioTrack, AudioData,
)


# =============================================================================
# 基础阶段类
# =============================================================================

class BaseStage(ABC):
    """基础阶段"""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.temp_dir = cfg.paths.temp_dir

    @abstractmethod
    def process(self, *args, **kwargs) -> Any:
        pass


# =============================================================================
# 阶段1：输入阶段
# =============================================================================

class InputData:
    """输入数据"""
    text: str
    style: str | None = None
    metadata: dict = {}


class InputStage(BaseStage):
    """输入处理阶段"""

    def process(self, text: str, style: str | None = None, **kwargs) -> InputData:
        """处理输入"""
        if not text or not text.strip():
            raise ValueError("输入不能为空")

        # 预处理
        text = text.strip()
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        data = InputData()
        data.text = text
        data.style = style or self.cfg.style.art_style
        data.metadata = kwargs
        return data


# =============================================================================
# 阶段2：剧本生成阶段
# =============================================================================

class ScriptGenerationStage(BaseStage):
    """剧本生成阶段"""

    def generate(self, input_data: InputData) -> ScriptData:
        """生成剧本"""
        import uuid

        script = ScriptData(
            id=str(uuid.uuid4()),
            title=f"Story_{len(input_data.text[:20])}",
            story_type=self._infer_type(input_data.text),
            theme="冒险",
            premise=input_data.text[:100],
        )

        # 解析场景
        scenes = self._parse_scenes(input_data.text)
        script.scenes.extend(scenes)

        # 解析角色
        characters = self._parse_characters(input_data.text)
        for char in characters:
            script.characters[char.id] = char

        return script

    def _infer_type(self, text: str) -> StoryType:
        """推断故事类型"""
        keywords = {
            StoryType.ROMANCE: ["恋爱", "爱情", "喜欢", "爱"],
            StoryType.ADVENTURE: ["冒险", "旅程", "探险", "冒险者"],
            StoryType.MYSTERY: ["悬疑", "谜", "推理", "真相"],
            StoryType.COMEDY: ["搞笑", "喜剧", "幽默"],
            StoryType.ACTION: ["战斗", "动作", "战争", "剑"],
            StoryType.FANTASY: ["魔法", "龙", "精灵", "奇幻"],
        }

        text_lower = text.lower()
        for story_type, words in keywords.items():
            if any(w in text_lower for w in words):
                return story_type
        return StoryType.ADVENTURE

    def _parse_scenes(self, text: str) -> list[SceneData]:
        """解析场景"""
        import uuid
        import re

        scenes = []
        paragraphs = re.split(r"\n\s*\n", text.strip())

        for i, para in enumerate(paragraphs):
            if len(para.strip()) < 10:
                continue

            scene = SceneData(
                id=f"scene_{uuid.uuid4().hex[:8]}",
                order=i,
                title=f"场景{i+1}",
                description=para.strip(),
                elements=[
                    SceneElement(
                        type="narration",
                        content=para.strip(),
                    )
                ],
            )
            scenes.append(scene)

        # 如果没有解析到场景，创建一个默认场景
        if not scenes:
            scenes.append(SceneData(
                id=f"scene_{uuid.uuid4().hex[:8]}",
                order=0,
                title="场景1",
                description=text,
                elements=[SceneElement(type="narration", content=text)],
            ))

        return scenes

    def _parse_characters(self, text: str) -> list[CharacterData]:
        """解析角色"""
        import uuid
        import re

        characters = []

        # 简单的角色识别（基于常见模式）
        patterns = [
            r"([A-Za-z\u4e00-\u9fff]{2,4})说",
            r"([A-Za-z\u4e00-\u9fff]{2,4})想",
            r"主角",
        ]

        found = set()
        for pattern in patterns:
            matches = re.findall(pattern, text)
            found.update(matches)

        # 如果没找到，创建默认角色
        if not found:
            char = CharacterData(
                id=f"char_{uuid.uuid4().hex[:8]}",
                name="主角",
                character_type=CharacterType.PROTAGONIST,
                description="故事主角",
                appearance=CharacterAppearance(
                    age="young adult",
                    gender="androgynous",
                ),
            )
            characters.append(char)
        else:
            for i, name in enumerate(found):
                char = CharacterData(
                    id=f"char_{uuid.uuid4().hex[:8]}",
                    name=name,
                    character_type=CharacterType.PROTAGONIST if i == 0 else CharacterType.SUPPORTING,
                    description=f"角色{name}",
                    appearance=CharacterAppearance(),
                )
                characters.append(char)

        return characters


# =============================================================================
# 阶段3：画面描述生成阶段
# =============================================================================

class SceneDescriptionData:
    """场景描述数据"""
    scene_id: str
    description: str
    prompt: str
    negative_prompt: str = ""


class SceneDescriptionStage(BaseStage):
    """画面描述生成阶段"""

    def generate(self, script: ScriptData) -> list[SceneDescriptionData]:
        """生成场景描述"""
        descriptions = []

        for scene in script.scenes:
            desc = SceneDescriptionData()
            desc.scene_id = scene.id
            desc.description = scene.description or scene.title
            desc.prompt = self._build_prompt(scene)
            desc.negative_prompt = self._build_negative()
            descriptions.append(desc)

        return descriptions

    def _build_prompt(self, scene: SceneData) -> str:
        """构建提示词"""
        from frameleap.utils import build_prompt

        style = self.cfg.style.art_style
        subject = scene.description or "anime scene"

        return build_prompt(subject=subject, style=style)

    def _build_negative(self) -> str:
        """构建负面提示词"""
        from frameleap.utils import build_negative_prompt
        return build_negative_prompt()


# =============================================================================
# 阶段4：图像生成阶段
# =============================================================================

class ImageGenerationStage(BaseStage):
    """图像生成阶段"""

    def generate(self, descriptions: list[SceneDescriptionData]) -> list[str]:
        """生成图像"""
        image_paths = []

        for i, desc in enumerate(descriptions):
            # 这里应该调用实际的图像生成API
            # 暂时创建占位文件
            path = self.temp_dir / f"scene_{desc.scene_id}.png"
            path.touch()

            # TODO: 调用图像生成API
            # self._generate_image(desc.prompt, desc.negative_prompt, path)

            image_paths.append(str(path))

        return image_paths

    def _generate_image(self, prompt: str, negative: str, output_path: Path):
        """生成单张图像（待实现）"""
        # TODO: 集成实际的图像生成API
        # options: SDXL, Flux, Midjourney等
        pass


# =============================================================================
# 阶段5：分镜编排阶段
# =============================================================================

class StoryboardData:
    """分镜数据"""
    timeline: TimelineData


class StoryboardStage(BaseStage):
    """分镜编排阶段"""

    def arrange(self, script: ScriptData, images: list[str]) -> StoryboardData:
        """编排分镜"""
        timeline = TimelineData()

        current_time = 0.0
        default_duration = 3.0  # 默认每场景3秒

        for i, (scene, img_path) in enumerate(zip(script.scenes, images)):
            shot = CameraShot(
                id=f"shot_{i}",
                scene_id=scene.id,
                order=i,
                time_range=TimeRange(start=current_time, end=current_time + default_duration),
                duration=default_duration,
                shot_size=self._select_shot_size(i, len(script.scenes)),
                description=scene.description,
                visual_prompt=img_path,
            )
            timeline.shots.append(shot)
            current_time += default_duration

        return StoryboardData(timeline=timeline)

    def _select_shot_size(self, index: int, total: int) -> ShotSize:
        """选择景别"""
        if index == 0:
            return ShotSize.LONG  # 开场用远景
        elif index == total - 1:
            return ShotSize.MEDIUM  # 结尾用中景
        else:
            return ShotSize.MEDIUM  # 中间用中景


# =============================================================================
# 阶段6-10（简化框架，待详细实现）
# =============================================================================

class AnimationData:
    """动画数据"""
    frames: list[str] = []


class AnimationStage(BaseStage):
    """动画化阶段"""
    def animate(self, storyboard: StoryboardData) -> AnimationData:
        return AnimationData()


class TextLayerData:
    """文字层数据"""
    subtitles: list[dict] = []
    bubbles: list[dict] = []


class AudioGenerationStage(BaseStage):
    """音频生成阶段"""
    def generate(self, script: ScriptData) -> AudioData:
        return AudioData()


class TextSubtitleStage(BaseStage):
    """文字字幕阶段"""
    def generate(self, script: ScriptData) -> TextLayerData:
        return TextLayerData()


class VideoData:
    """视频数据"""
    path: str | None = None


class CompositionRenderingStage(BaseStage):
    """合成渲染阶段"""
    def compose(self, animations: AnimationData, audio: AudioData, text: TextLayerData) -> VideoData:
        return VideoData()


class OutputDeliveryStage(BaseStage):
    """输出交付阶段"""
    def deliver(self, video: VideoData) -> str:
        output_path = self.cfg.paths.work_dir / "output.mp4"
        return str(output_path)


__all__ = [
    "InputStage", "ScriptGenerationStage", "SceneDescriptionStage",
    "ImageGenerationStage", "StoryboardStage", "AnimationStage",
    "AudioGenerationStage", "TextSubtitleStage",
    "CompositionRenderingStage", "OutputDeliveryStage",
]
