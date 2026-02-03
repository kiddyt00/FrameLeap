"""
长视频生成策略 - 解决时长限制问题

策略：
1. 分段生成：将长视频切分为多个短视频段（每段5-10秒）
2. 平滑拼接：使用智能转场和淡入淡出连接各段
3. 一致性保持：角色、场景、风格跨段一致性
4. 音画同步：分段生成音频后与视频对齐拼接
"""

from typing import List
import re
import uuid
from pathlib import Path

from app.config import Config
from app.models import ScriptData, SceneData, CameraShot, TimeRange


# =============================================================================
# 配置常量
# =============================================================================

# 时间相关常量
DEFAULT_MAX_SEGMENT_DURATION = 8.0  # 每段最长8秒
DEFAULT_TRANSITION_DURATION = 0.5  # 转场时长（秒）

# 时长估算常量
BASE_SCENE_DURATION = 3.0  # 基础场景时长（秒）
READING_SPEED = 4.0  # 阅读速度（字/秒）
AVG_DIALOGUE_DURATION = 2.5  # 平均每句对话时长（秒）

# 节奏系数
RHYTHM_MULTIPLIERS = {
    "slow": 1.5,
    "medium": 1.0,
    "fast": 0.7,
}

# FFmpeg 常量
VIDEO_CODEC = "libx264"
VIDEO_PRESET = "medium"
VIDEO_CRF = "23"
PIX_FMT = "yuv420p"


# =============================================================================
# 视频分段规划器
# =============================================================================

class VideoSegmentPlanner:
    """
    视频分段规划器

    从导演角度：
    - 根据情节断点规划分段
    - 保持每个分段的叙事完整性
    - 在高潮点避免分段
    """

    def __init__(self, cfg: Config):
        """初始化分段规划器

        Args:
            cfg: 配置对象
        """
        self.cfg = cfg
        self.max_segment_duration = DEFAULT_MAX_SEGMENT_DURATION

    def plan_segments(self, script: ScriptData) -> List[List[SceneData]]:
        """规划视频分段

        Args:
            script: 剧本数据

        Returns:
            分段列表，每个元素是一组场景
        """
        segments = []
        current_segment = []
        current_duration = 0.0

        for scene in script.scenes:
            scene_duration = self._estimate_scene_duration(scene)

            if current_duration + scene_duration > self.max_segment_duration:
                if scene_duration > self.max_segment_duration:
                    # 场景内部分段
                    sub_segments = self._split_scene(
                        scene,
                        self.max_segment_duration - current_duration
                    )
                    if current_segment:
                        current_segment.append(sub_segments[0])
                        segments.append(current_segment)
                        current_segment = sub_segments[1:]
                    else:
                        current_segment = sub_segments
                    current_duration = sum(
                        self._estimate_scene_duration(s) for s in current_segment
                    )
                else:
                    # 新分段
                    current_segment.append(scene)
                    segments.append(current_segment)
                    current_segment = []
                    current_duration = 0.0
            else:
                current_segment.append(scene)
                current_duration += scene_duration

        # 处理剩余
        if current_segment:
            segments.append(current_segment)

        return segments

    def _estimate_scene_duration(self, scene: SceneData) -> float:
        """估算场景时长

        从导演角度：
        - 对话场景：根据字数估算（约3字/秒）
        - 动作场景：固定时长
        - 情感场景：适当延长

        Args:
            scene: 场景数据

        Returns:
            估算的时长（秒）
        """
        # 获取场景文本
        text = scene.description or ""
        for elem in scene.elements:
            text += " " + elem.content

        char_count = len(text.strip())

        # 获取节奏信息
        rhythm = scene.metadata.get("rhythm", "medium")
        intensity = scene.metadata.get("intensity", 0.5)

        # 基础时长
        base_duration = BASE_SCENE_DURATION

        # 根据字数调整
        if char_count > 0:
            reading_time = char_count / READING_SPEED
            base_duration = max(BASE_SCENE_DURATION, reading_time)

        # 根据节奏调整
        base_duration *= RHYTHM_MULTIPLIERS.get(rhythm, 1.0)

        # 根据强度调整
        base_duration *= (1.2 - intensity * 0.4)

        return min(base_duration, self.max_segment_duration)

    def _split_scene(
        self,
        scene: SceneData,
        max_duration: float,
    ) -> List[SceneData]:
        """分割场景

        Args:
            scene: 要分割的场景
            max_duration: 最大时长

        Returns:
            分割后的场景列表
        """
        dialogues = [e for e in scene.elements if e.type == "dialogue"]

        if dialogues:
            return self._split_by_dialogue(scene, max_duration, dialogues)
        else:
            return self._split_by_content(scene, max_duration)

    def _split_by_dialogue(
        self,
        scene: SceneData,
        max_duration: float,
        dialogues: list,
    ) -> List[SceneData]:
        """按对话分割场景

        Args:
            scene: 场景数据
            max_duration: 最大时长
            dialogues: 对话元素列表

        Returns:
            分割后的场景列表
        """
        segments = []
        current_elements = []
        current_text = ""

        max_dialogues = int(max_duration / AVG_DIALOGUE_DURATION)

        for i, dialogue in enumerate(dialogues):
            current_elements.append(dialogue)
            current_text += " " + dialogue.content

            if len(current_elements) >= max_dialogues:
                new_scene = SceneData(
                    id=f"{scene.id}_part_{len(segments)}",
                    order=scene.order,
                    title=f"{scene.title} (续)",
                    description=current_text.strip(),
                    location=scene.location,
                    time_of_day=scene.time_of_day,
                    weather=scene.weather,
                    elements=current_elements.copy(),
                    characters=scene.characters.copy(),
                    atmosphere=scene.atmosphere,
                    metadata=scene.metadata.copy(),
                )
                segments.append(new_scene)

                current_elements = []
                current_text = ""

        # 处理剩余
        if current_elements:
            new_scene = SceneData(
                id=f"{scene.id}_part_{len(segments)}",
                order=scene.order,
                title=f"{scene.title} (续)",
                description=current_text.strip(),
                location=scene.location,
                time_of_day=scene.time_of_day,
                weather=scene.weather,
                elements=current_elements,
                characters=scene.characters,
                atmosphere=scene.atmosphere,
                metadata=scene.metadata,
            )
            segments.append(new_scene)

        return segments if segments else [scene]

    def _split_by_content(
        self,
        scene: SceneData,
        max_duration: float,
    ) -> List[SceneData]:
        """按内容分割场景

        Args:
            scene: 场景数据
            max_duration: 最大时长

        Returns:
            分割后的场景列表
        """
        description = scene.description or ""

        # 按句子分割
        sentences = re.split(r'[。！？\n]', description)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) <= 1:
            return [scene]

        avg_sentence_duration = max_duration / len(sentences)

        segments = []
        current_content = ""
        current_duration = 0.0

        for sentence in sentences:
            sentence_duration = len(sentence) / READING_SPEED

            if current_duration + sentence_duration > max_duration and current_content:
                new_scene = SceneData(
                    id=f"{scene.id}_part_{len(segments)}",
                    order=scene.order,
                    title=f"{scene.title} (续)",
                    description=current_content.strip(),
                    location=scene.location,
                    elements=[e for e in scene.elements if e.type != "dialogue"],
                    characters=scene.characters,
                    atmosphere=scene.atmosphere,
                    metadata=scene.metadata,
                )
                segments.append(new_scene)
                current_content = sentence
                current_duration = sentence_duration
            else:
                current_content += sentence + "。"
                current_duration += sentence_duration

        # 处理剩余
        if current_content:
            new_scene = SceneData(
                id=f"{scene.id}_part_{len(segments)}",
                order=scene.order,
                title=f"{scene.title} (续)",
                description=current_content.strip(),
                location=scene.location,
                elements=[e for e in scene.elements if e.type != "dialogue"],
                characters=scene.characters,
                atmosphere=scene.atmosphere,
                metadata=scene.metadata,
            )
            segments.append(new_scene)

        return segments if segments else [scene]


# =============================================================================
# 视频分段合成器
# =============================================================================

class VideoSegmentComposer:
    """
    视频分段合成器

    从剪辑师角度：
    - 平滑的淡入淡出转场
    - 音频跨段连续
    - 风格一致性检查
    """

    def __init__(self, cfg: Config):
        """初始化合成器

        Args:
            cfg: 配置对象
        """
        self.cfg = cfg
        self.transition_duration = DEFAULT_TRANSITION_DURATION

    def compose_segments(
        self,
        segment_paths: List[str],
        output_path: Path,
    ) -> str:
        """合并视频分段

        Args:
            segment_paths: 视频分段路径列表
            output_path: 输出路径

        Returns:
            合并后的视频路径

        Raises:
            ValueError: 没有分段可合并
        """
        if not segment_paths:
            raise ValueError("No segments to compose")

        if len(segment_paths) == 1:
            return segment_paths[0]

        import subprocess

        # 创建临时文件列表
        list_file = self.cfg.paths.temp_dir / "segments.txt"
        with open(list_file, "w") as f:
            for path in segment_paths:
                f.write(f"file '{path}'\n")

        # 尝试带转场合并
        filter_complex = self._build_transition_filter(len(segment_paths))

        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-filter_complex", filter_complex,
            "-c:v", VIDEO_CODEC,
            "-preset", VIDEO_PRESET,
            "-crf", VIDEO_CRF,
            "-pix_fmt", PIX_FMT,
            str(output_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            # 转场失败，使用简单合并
            return self._simple_concat(segment_paths, output_path)

        return str(output_path)

    def _build_transition_filter(self, segment_count: int) -> str:
        """构建转场滤镜

        Args:
            segment_count: 分段数量

        Returns:
            FFmpeg滤镜字符串
        """
        if segment_count <= 1:
            return ""

        parts = []
        for i in range(segment_count):
            parts.append(
                f"[{i}:v]fade=t=in:st=0:d=0.5,fade=t=out:"
                f"st={DEFAULT_MAX_SEGMENT_DURATION-0.5}:d=0.5[v{i}]"
            )

        concat_inputs = "".join([f"[v{i}]" for i in range(segment_count)])
        parts.append(
            f"{concat_inputs}concat=n={segment_count}:v=1:a=0[outv]"
        )

        return ";".join(parts)

    def _simple_concat(
        self,
        segment_paths: List[str],
        output_path: Path,
    ) -> str:
        """简单合并（无转场）

        Args:
            segment_paths: 视频分段路径列表
            output_path: 输出路径

        Returns:
            合并后的视频路径
        """
        import subprocess

        list_file = self.cfg.paths.temp_dir / "segments_simple.txt"
        with open(list_file, "w") as f:
            for path in segment_paths:
                f.write(f"file '{path}'\n")

        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(output_path),
        ]

        subprocess.run(cmd, check=True)
        return str(output_path)

    def merge_audio_segments(
        self,
        audio_paths: List[str],
        output_path: Path,
    ) -> str:
        """合并音频分段

        Args:
            audio_paths: 音频分段路径列表
            output_path: 输出路径

        Returns:
            合并后的音频路径
        """
        import subprocess

        list_file = self.cfg.paths.temp_dir / "audio_segments.txt"
        with open(list_file, "w") as f:
            for path in audio_paths:
                f.write(f"file '{path}'\n")

        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(output_path),
        ]

        subprocess.run(cmd, check=True)
        return str(output_path)


# =============================================================================
# 长视频生成器
# =============================================================================

class LongVideoGenerator:
    """
    长视频生成器 - 整合分段规划和合成

    工作流程：
    1. 分析剧本，规划分段
    2. 为每个分段生成视频
    3. 合并所有分段
    4. 生成并合并音频
    5. 音视频最终合成
    """

    def __init__(self, cfg: Config):
        """初始化长视频生成器

        Args:
            cfg: 配置对象
        """
        self.cfg = cfg
        self.planner = VideoSegmentPlanner(cfg)
        self.composer = VideoSegmentComposer(cfg)

    def generate_long_video(
        self,
        script: ScriptData,
        video_segments: List,
        audio_segments: List,
    ) -> str:
        """生成长视频

        Args:
            script: 剧本
            video_segments: 视频分段列表
            audio_segments: 音频分段列表

        Returns:
            最终视频路径
        """
        # 规划分段
        segments = self.planner.plan_segments(script)

        # 合并视频分段
        video_output = self.cfg.paths.work_dir / "final_video.mp4"
        self.composer.compose_segments(video_segments, video_output)

        # 合并音频分段
        audio_output = self.cfg.paths.work_dir / "final_audio.mp3"
        self.composer.merge_audio_segments(audio_segments, audio_output)

        # 音视频合成
        final_output = self.cfg.paths.work_dir / "output.mp4"
        self._merge_av(video_output, audio_output, final_output)

        return str(final_output)

    def _merge_av(
        self,
        video_path: Path,
        audio_path: Path,
        output_path: Path,
    ) -> None:
        """合并音视频

        Args:
            video_path: 视频文件路径
            audio_path: 音频文件路径
            output_path: 输出文件路径
        """
        import subprocess

        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            str(output_path),
        ]

        subprocess.run(cmd, check=True)


__all__ = [
    # 常量
    "DEFAULT_MAX_SEGMENT_DURATION",
    "DEFAULT_TRANSITION_DURATION",
    "BASE_SCENE_DURATION",
    "READING_SPEED",
    "AVG_DIALOGUE_DURATION",
    "RHYTHM_MULTIPLIERS",
    "VIDEO_CODEC",
    "VIDEO_PRESET",
    "VIDEO_CRF",
    "PIX_FMT",
    # 类
    "VideoSegmentPlanner",
    "VideoSegmentComposer",
    "LongVideoGenerator",
]
