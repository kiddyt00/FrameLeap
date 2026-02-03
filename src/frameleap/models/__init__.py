"""
数据模型模块

定义系统中使用的所有数据结构
"""

from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import timedelta


# =============================================================================
# 枚举类型
# =============================================================================

class ShotSize(str, Enum):
    """景别枚举"""
    EXTREME_LONG = "extreme_long"  # 大远景
    LONG = "long"  # 远景
    FULL = "full"  # 全景
    MEDIUM = "medium"  # 中景
    MEDIUM_CLOSE = "medium_close"  # 中近景
    CLOSE = "close"  # 近景
    EXTREME_CLOSE = "extreme_close"  # 特写
    BIG_EXTREME_CLOSE = "big_extreme_close"  # 大特写


class CameraMovement(str, Enum):
    """运镜类型枚举"""
    STATIC = "static"  # 固定
    PAN_LEFT = "pan_left"  # 左平移
    PAN_RIGHT = "pan_right"  # 右平移
    TILT_UP = "tilt_up"  # 上摇
    TILT_DOWN = "tilt_down"  # 下摇
    ZOOM_IN = "zoom_in"  # 推进
    ZOOM_OUT = "zoom_out"  # 拉远
    DOLLY_IN = "dolly_in"  # 移进
    DOLLY_OUT = "dolly_out"  # 移出
    TRACK_LEFT = "track_left"  # 左跟
    TRACK_RIGHT = "track_right"  # 右跟
    ARC_LEFT = "arc_left"  # 左环绕
    ARC_RIGHT = "arc_right"  # 右环绕
    ROTATE_LEFT = "rotate_left"  # 左旋转
    ROTATE_RIGHT = "rotate_right"  # 右旋转


class TransitionType(str, Enum):
    """转场类型枚举"""
    CUT = "cut"  # 切换
    FADE_IN = "fade_in"  # 淡入
    FADE_OUT = "fade_out"  # 淡出
    CROSS_FADE = "cross_fade"  # 溶解
    WIPE_LEFT = "wipe_left"  # 左擦除
    WIPE_RIGHT = "wipe_right"  # 右擦除
    WIPE_UP = "wipe_up"  # 上擦除
    WIPE_DOWN = "wipe_down"  # 下擦除
    ZOOM_IN = "zoom_in"  # 缩放进
    ZOOM_OUT = "zoom_out"  # 缩放出


class Emotion(str, Enum):
    """情感类型枚举"""
    NEUTRAL = "neutral"  # 中性
    HAPPY = "happy"  # 开心
    SAD = "sad"  # 悲伤
    ANGRY = "angry"  # 愤怒
    SURPRISED = "surprised"  # 惊讶
    FEAR = "fear"  # 恐惧
    DISGUST = "disgust"  # 厌恶
    EXCITED = "excited"  # 兴奋
    MELANCHOLIC = "melancholic"  # 忧郁
    SERIOUS = "serious"  # 严肃


class StoryType(str, Enum):
    """故事类型枚举"""
    ADVENTURE = "adventure"  # 冒险
    ROMANCE = "romance"  # 恋爱
    MYSTERY = "mystery"  # 悬疑
    HORROR = "horror"  # 恐怖
    COMEDY = "comedy"  # 喜剧
    TRAGEDY = "tragedy"  # 悲剧
    ACTION = "action"  # 动作
    HEALING = "healing"  # 治愈
    HOT_BLOODED = "hot_blooded"  # 热血
    FANTASY = "fantasy"  # 奇幻


class CharacterType(str, Enum):
    """角色类型枚举"""
    PROTAGONIST = "protagonist"  # 主角
    ANTAGONIST = "antagonist"  # 反派
    SUPPORTING = "supporting"  # 配角
    MENTOR = "mentor"  # 导师
    COMIC_RELIEF = "comic_relief"  # 搞笑担当
    STRATEGIST = "strategist"  # 智囊
    FIGHTER = "fighter"  # 战斗担当
    HEALER = "healer"  # 治愈者
    REBEL = "rebel"  # 叛逆者
    GUARDIAN = "guardian"  # 守护者


# =============================================================================
# 基础数据模型
# =============================================================================

@dataclass
class Vector2:
    """二维向量"""
    x: float
    y: float


@dataclass
class Vector3:
    """三维向量"""
    x: float
    y: float
    z: float


@dataclass
class Rect:
    """矩形区域"""
    x: float
    y: float
    width: float
    height: float

    @property
    def left(self) -> float:
        return self.x

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def top(self) -> float:
        return self.y

    @property
    def bottom(self) -> float:
        return self.y + self.height


@dataclass
class TimeRange:
    """时间范围"""
    start: float  # 秒
    end: float  # 秒

    @property
    def duration(self) -> float:
        return self.end - self.start

    def overlaps(self, other: "TimeRange") -> bool:
        """检查是否与另一个时间范围重叠"""
        return not (self.end <= other.start or self.start >= other.end)


# =============================================================================
# 角色相关模型
# =============================================================================

@dataclass
class CharacterAppearance:
    """角色外观描述"""
    age: Optional[str] = None  # e.g., "16 year old", "young adult"
    gender: Optional[str] = None  # male, female, androgynous
    height: Optional[str] = None  # tall, average, short
    body_type: Optional[str] = None  # slim, athletic, muscular

    # 头部特征
    hair_style: Optional[str] = None  # short, long, messy, ponytail
    hair_color: Optional[str] = None  # black, brown, blonde, silver, pink
    eye_color: Optional[str] = None  # brown, blue, green, amber, heterochromia
    eye_shape: Optional[str] = None  # normal, cat-like, round
    skin_tone: Optional[str] = None  # pale, fair, tan, dark

    # 服装
    outfit: Optional[str] = None  # school uniform, casual wear, armor
    accessories: List[str] = field(default_factory=list)  # glasses, ribbon, necklace


@dataclass
class CharacterData:
    """角色数据"""
    id: str
    name: str
    character_type: CharacterType

    # 基础描述
    description: str
    personality: List[str] = field(default_factory=list)  # 性格特征列表
    background: Optional[str] = None  # 背景故事

    # 外观
    appearance: CharacterAppearance = field(default_factory=CharacterAppearance)

    # 声音
    voice_id: Optional[str] = None  # TTS音色ID
    voice_description: Optional[str] = None  # 声音描述

    # 参考图（用于角色一致性）
    reference_images: List[str] = field(default_factory=list)
    lora_path: Optional[str] = None  # 角色LoRA路径


# =============================================================================
# 剧本相关模型
# =============================================================================

@dataclass
class Dialogue:
    """对话"""
    character_id: str
    text: str
    emotion: Emotion = Emotion.NEUTRAL
    pause_after: float = 0.0  # 说话后停顿时长（秒）


@dataclass
class Action:
    """动作描述"""
    description: str
    duration: Optional[float] = None  # 动作持续时长


@dataclass
class SceneElement:
    """场景元素"""
    type: str  # dialogue, action, narration, etc.
    content: str
    metadata: dict = field(default_factory=dict)


@dataclass
class SceneData:
    """场景数据"""
    id: str
    order: int  # 场景顺序

    # 基本信息
    title: Optional[str] = None
    location: Optional[str] = None  # 场景地点
    time_of_day: Optional[str] = None  # 时间：morning, afternoon, night, etc.
    weather: Optional[str] = None  # 天气

    # 场景内容
    elements: List[SceneElement] = field(default_factory=list)

    # 场景描述（用于图像生成）
    description: Optional[str] = None
    atmosphere: Optional[str] = None  # 氛围描述

    # 出场角色
    characters: List[str] = field(default_factory=list)  # 角色ID列表

    @property
    def dialogues(self) -> List[Dialogue]:
        """获取所有对话"""
        result = []
        for elem in self.elements:
            if elem.type == "dialogue":
                data = elem.metadata
                result.append(Dialogue(
                    character_id=data.get("character_id", ""),
                    text=elem.content,
                    emotion=Emotion(data.get("emotion", "neutral")),
                    pause_after=data.get("pause_after", 0.0)
                ))
        return result


@dataclass
class ScriptData:
    """剧本数据"""
    id: str
    title: str

    # 故事信息
    story_type: StoryType
    theme: str  # 核心主题
    premise: str  # 故事前提

    # 剧本结构
    structure_type: str = "three_act"  # three_act, hero_journey, etc.

    # 场景列表
    scenes: List[SceneData] = field(default_factory=list)

    # 角色列表
    characters: dict[str, CharacterData] = field(default_factory=dict)

    # 元数据
    metadata: dict = field(default_factory=dict)

    @property
    def total_scenes(self) -> int:
        return len(self.scenes)

    @property
    def total_duration_estimate(self) -> float:
        """估算总时长（秒）"""
        # 简单估算：每个场景平均3秒
        return len(self.scenes) * 3.0


# =============================================================================
# 分镜相关模型
# =============================================================================

@dataclass
class CameraShot:
    """镜头数据"""
    id: str
    scene_id: str
    order: int

    # 时间
    time_range: TimeRange
    duration: float  # 镜头时长（秒）

    # 景别与运镜
    shot_size: ShotSize
    camera_movement: Optional[CameraMovement] = None
    movement_speed: float = 1.0  # 运镜速度（0.1-10）

    # 构图
    angle: float = 0.0  # 拍摄角度（度），负数为俯视，正数为仰视
    focus_point: Optional[Vector2] = None  # 焦点位置（归一化坐标0-1）

    # 转场
    transition_in: Optional[TransitionType] = None
    transition_out: Optional[TransitionType] = None
    transition_duration: float = 0.5  # 转场时长（秒）

    # 描述
    description: Optional[str] = None
    visual_prompt: Optional[str] = None  # 图像生成提示词

    # 出场角色
    characters: List[str] = field(default_factory=list)


@dataclass
class TimelineData:
    """时间轴数据"""
    shots: List[CameraShot] = field(default_factory=list)

    @property
    def total_duration(self) -> float:
        """总时长"""
        if not self.shots:
            return 0.0
        return max(shot.time_range.end for shot in self.shots)

    def get_shot_at_time(self, time: float) -> Optional[CameraShot]:
        """获取指定时间的镜头"""
        for shot in self.shots:
            if shot.time_range.start <= time < shot.time_range.end:
                return shot
        return None


# =============================================================================
# 音频相关模型
# =============================================================================

@dataclass
class AudioTrack:
    """音轨数据"""
    id: str
    type: str  # dialogue, sfx, bgm

    # 时间
    time_range: TimeRange

    # 内容
    source_path: Optional[str] = None  # 音频文件路径
    text: Optional[str] = None  # 对于TTS，原始文本
    character_id: Optional[str] = None  # 对于对话，角色ID

    # 音频参数
    volume: float = 1.0  # 音量（0-1）
    pan: float = 0.0  # 声相（-1左，0中，1右）
    fade_in: float = 0.0  # 淡入时长（秒）
    fade_out: float = 0.0  # 淡出时长（秒）

    # 元数据
    metadata: dict = field(default_factory=dict)


@dataclass
class AudioData:
    """音频数据"""
    tracks: List[AudioTrack] = field(default_factory=list)

    def get_tracks_at_time(self, time: float) -> List[AudioTrack]:
        """获取指定时间的所有音轨"""
        return [track for track in self.tracks if track.time_range.start <= time < track.time_range.end]


# =============================================================================
# 输出相关模型
# =============================================================================

@dataclass
class GenerationResult:
    """生成结果"""
    success: bool
    video_path: Optional[str] = None
    error_message: Optional[str] = None

    # 中间结果
    script: Optional[ScriptData] = None
    images: List[str] = field(default_factory=list)
    audio: Optional[AudioData] = None

    # 元数据
    generation_time: float = 0.0  # 生成耗时（秒）
    metadata: dict = field(default_factory=dict)
