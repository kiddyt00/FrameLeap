"""
长视频生成策略 - 解决时长限制问题

策略：
1. 分段生成：将长视频切分为多个短视频段（每段5-10秒）
2. 平滑拼接：使用智能转场和淡入淡出连接各段
3. 一致性保持：角色、场景、风格跨段一致性
4. 音画同步：分段生成音频后与视频对齐拼接
"""

from typing import List, Tuple
import re
from pathlib import Path

from frameleap.config import Config
from frameleap.models import ScriptData, SceneData, CameraShot, TimeRange


class VideoSegmentPlanner:
    """
    视频分段规划器

    从导演角度：
    - 根据情节断点规划分段
    - 保持每个分段的叙事完整性
    - 在高潮点避免分段
    """

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.max_segment_duration = 8.0  # 每段最长8秒（适应10秒限制）

    def plan_segments(self, script: ScriptData) -> List[List[SceneData]]:
        """
        规划视频分段

        Args:
            script: 剧本数据

        Returns:
            分段列表，每个元素是一组场景
        """
        segments = []
        current_segment = []
        current_duration = 0.0

        for scene in script.scenes:
            # 估算场景时长
            scene_duration = self._estimate_scene_duration(scene)

            # 如果加上当前场景会超限
            if current_duration + scene_duration > self.max_segment_duration:
                # 检查是否可以在场景内分段
                if scene_duration > self.max_segment_duration:
                    # 需要在场景内部分段
                    sub_segments = self._split_scene(scene, self.max_segment_duration - current_duration)
                    if current_segment:
                        current_segment.append(sub_segments[0])
                        segments.append(current_segment)
                        current_segment = sub_segments[1:]
                    else:
                        current_segment = sub_segments
                    current_duration = sum(self._estimate_scene_duration(s) for s in current_segment)
                else:
                    # 完整场景开始新分段
                    current_segment.append(scene)
                    segments.append(current_segment)
                    current_segment = []
                    current_duration = 0.0
            else:
                # 加入当前分段
                current_segment.append(scene)
                current_duration += scene_duration

        # 处理最后一段
        if current_segment:
            segments.append(current_segment)

        return segments

    def _estimate_scene_duration(self, scene: SceneData) -> float:
        """
        估算场景时长

        从导演角度：
        - 对话场景：根据字数估算（约3字/秒）
        - 动作场景：固定时长
        - 情感场景：适当延长
        """
        # 获取场景文本
        text = scene.description or ""
        for elem in scene.elements:
            text += " " + elem.content

        # 计算字数
        char_count = len(text.strip())

        # 获取节奏信息
        rhythm = scene.metadata.get("rhythm", "medium")
        intensity = scene.metadata.get("intensity", 0.5)

        # 基础时长：每场景3-5秒
        base_duration = 3.0

        # 根据字数调整
        if char_count > 0:
            reading_time = char_count / 4.0  # 每秒4字
            base_duration = max(3.0, reading_time)

        # 根据节奏调整
        rhythm_multiplier = {
            "slow": 1.5,
            "medium": 1.0,
            "fast": 0.7,
        }
        base_duration *= rhythm_multiplier.get(rhythm, 1.0)

        # 根据强度调整（高强度=快节奏=短时长）
        base_duration *= (1.2 - intensity * 0.4)

        return min(base_duration, self.max_segment_duration)

    def _split_scene(self, scene: SceneData, max_duration: float) -> List[SceneData]:
        """
        分割场景

        Args:
            scene: 要分割的场景
            max_duration: 最大时长

        Returns:
            分割后的场景列表
        """
        # 如果场景有对话，按对话分割
        dialogues = [e for e in scene.elements if e.type == "dialogue"]

        if dialogues:
            return self._split_by_dialogue(scene, max_duration, dialogues)
        else:
            # 按描述内容分割
            return self._split_by_content(scene, max_duration)

    def _split_by_dialogue(self, scene: SceneData, max_duration: float, dialogues: list) -> List[SceneData]:
        """按对话分割场景"""
        import uuid

        segments = []
        current_elements = []
        current_text = ""

        # 估算每句对话的时长
        avg_dialogue_duration = 2.5  # 平均每句对话2.5秒
        max_dialogues_per_segment = int(max_duration / avg_dialogue_duration)

        for i, dialogue in enumerate(dialogues):
            current_elements.append(dialogue)
            current_text += " " + dialogue.content

            if len(current_elements) >= max_dialogues_per_segment:
                # 创建新的场景片段
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

        # 处理剩余内容
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

    def _split_by_content(self, scene: SceneData, max_duration: float) -> List[SceneData]:
        """按内容分割场景"""
        import uuid

        description = scene.description or ""

        # 按句子分割
        sentences = re.split(r'[。！？\n]', description)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) <= 1:
            return [scene]

        # 估算每句话的时长
        avg_sentence_duration = max_duration / len(sentences)

        segments = []
        current_content = ""
        current_duration = 0.0

        for sentence in sentences:
            sentence_duration = len(sentence) / 4.0  # 每秒4字

            if current_duration + sentence_duration > max_duration and current_content:
                # 创建新片段
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

        # 处理剩余内容
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


class VideoSegmentComposer:
    """
    视频分段合成器

    从剪辑师角度：
    - 平滑的淡入淡出转场
    - 音频跨段连续
    - 风格一致性检查
    """

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.transition_duration = 0.5  # 转场时长（秒）

    def compose_segments(self, segment_paths: List[str], output_path: Path) -> str:
        """
        合并视频分段

        Args:
            segment_paths: 视频分段路径列表
            output_path: 输出路径

        Returns:
            合并后的视频路径
        """
        if not segment_paths:
            raise ValueError("No segments to compose")

        if len(segment_paths) == 1:
            return segment_paths[0]

        # 使用FFmpeg合并
        import subprocess

        # 创建临时文件列表
        list_file = self.cfg.paths.temp_dir / "segments.txt"
        with open(list_file, "w") as f:
            for path in segment_paths:
                f.write(f"file '{path}'\n")

        # 使用concat过滤器合并，添加淡入淡出转场
        filter_complex = self._build_transition_filter(len(segment_paths))

        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-filter_complex", filter_complex,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            str(output_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            # 如果转场失败，尝试简单合并
            return self._simple_concat(segment_paths, output_path)

        return str(output_path)

    def _build_transition_filter(self, segment_count: int) -> str:
        """构建转场滤镜"""
        if segment_count <= 1:
            return ""

        # 简单的淡入淡出
        max_duration = 8.0  # 与VideoSegmentPlanner保持一致
        parts = []
        for i in range(segment_count):
            parts.append(f"[{i}:v]fade=t=in:st=0:d=0.5,fade=t=out:st={max_duration-0.5}:d=0.5[v{i}]")

        # 连接所有片段
        concat_inputs = "".join([f"[v{i}]" for i in range(segment_count)])
        parts.append(f"{concat_inputs}concat=n={segment_count}:v=1:a=0[outv]")

        return ";".join(parts)

    def _simple_concat(self, segment_paths: List[str], output_path: Path) -> str:
        """简单合并（无转场）"""
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

    def merge_audio_segments(self, audio_paths: List[str], output_path: Path) -> str:
        """合并音频分段"""
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
        self.cfg = cfg
        self.planner = VideoSegmentPlanner(cfg)
        self.composer = VideoSegmentComposer(cfg)

    def generate_long_video(self, script: ScriptData, video_segments: List, audio_segments: List) -> str:
        """
        生成长视频

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
        final_output = self.cfg.paths.output_dir / "output.mp4"
        self._merge_av(video_output, audio_output, final_output)

        return str(final_output)

    def _merge_av(self, video_path: Path, audio_path: Path, output_path: Path):
        """合并音视频"""
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
    "VideoSegmentPlanner",
    "VideoSegmentComposer",
    "LongVideoGenerator",
]
