"""
数据模型单元测试
"""

import pytest

from frameleap.models import (
    # 枚举
    ShotSize,
    CameraMovement,
    TransitionType,
    Emotion,
    StoryType,
    CharacterType,
    # 基础类型
    Vector2,
    Vector3,
    Rect,
    TimeRange,
    # 角色相关
    CharacterAppearance,
    CharacterData,
    # 剧本相关
    Dialogue,
    Action,
    SceneElement,
    SceneData,
    ScriptData,
    # 分镜相关
    CameraShot,
    TimelineData,
    # 音频相关
    AudioTrack,
    AudioData,
    # 输出相关
    GenerationResult,
)


class TestEnums:
    """测试枚举类型"""

    def test_shot_size(self):
        """测试景别枚举"""
        assert ShotSize.MEDIUM == "medium"
        assert ShotSize.CLOSE == "close"
        assert ShotSize.EXTREME_CLOSE == "extreme_close"

    def test_camera_movement(self):
        """测试运镜枚举"""
        assert CameraMovement.STATIC == "static"
        assert CameraMovement.ZOOM_IN == "zoom_in"
        assert CameraMovement.PAN_LEFT == "pan_left"

    def test_emotion(self):
        """测试情感枚举"""
        assert Emotion.HAPPY == "happy"
        assert Emotion.MELANCHOLIC == "melancholic"

    def test_story_type(self):
        """测试故事类型枚举"""
        assert StoryType.ADVENTURE == "adventure"
        assert StoryType.ROMANCE == "romance"

    def test_character_type(self):
        """测试角色类型枚举"""
        assert CharacterType.PROTAGONIST == "protagonist"
        assert CharacterType.MENTOR == "mentor"


class TestBasicTypes:
    """测试基础数据类型"""

    def test_vector2(self):
        """测试二维向量"""
        v = Vector2(x=1.0, y=2.0)
        assert v.x == 1.0
        assert v.y == 2.0

    def test_vector3(self):
        """测试三维向量"""
        v = Vector3(x=1.0, y=2.0, z=3.0)
        assert v.x == 1.0
        assert v.y == 2.0
        assert v.z == 3.0

    def test_rect(self):
        """测试矩形"""
        r = Rect(x=10, y=20, width=100, height=50)
        assert r.x == 10
        assert r.y == 20
        assert r.width == 100
        assert r.height == 50
        assert r.left == 10
        assert r.right == 110
        assert r.top == 20
        assert r.bottom == 70

    def test_time_range(self):
        """测试时间范围"""
        tr = TimeRange(start=0.0, end=10.0)
        assert tr.start == 0.0
        assert tr.end == 10.0
        assert tr.duration == 10.0

    def test_time_range_overlaps(self):
        """测试时间范围重叠"""
        tr1 = TimeRange(start=0.0, end=10.0)
        tr2 = TimeRange(start=5.0, end=15.0)
        tr3 = TimeRange(start=15.0, end=20.0)

        assert tr1.overlaps(tr2) is True
        assert tr1.overlaps(tr3) is False


class TestCharacterModels:
    """测试角色相关模型"""

    def test_character_appearance(self):
        """测试角色外观"""
        appearance = CharacterAppearance(
            age="16 year old",
            gender="female",
            hair_style="long",
            hair_color="brown",
            eye_color="green",
        )
        assert appearance.age == "16 year old"
        assert appearance.gender == "female"

    def test_character_data(self):
        """测试角色数据"""
        char = CharacterData(
            id="char_001",
            name="艾琳",
            character_type=CharacterType.PROTAGONIST,
            description="年轻勇敢的冒险者",
            personality=["勇敢", "善良"],
        )
        assert char.id == "char_001"
        assert char.name == "艾琳"
        assert char.character_type == CharacterType.PROTAGONIST
        assert "勇敢" in char.personality


class TestScriptModels:
    """测试剧本相关模型"""

    def test_dialogue(self):
        """测试对话"""
        dialogue = Dialogue(
            character_id="char_001",
            text="你好，世界！",
            emotion=Emotion.HAPPY,
            pause_after=0.5,
        )
        assert dialogue.character_id == "char_001"
        assert dialogue.text == "你好，世界！"
        assert dialogue.emotion == Emotion.HAPPY
        assert dialogue.pause_after == 0.5

    def test_scene_element(self):
        """测试场景元素"""
        element = SceneElement(
            type="narration",
            content="这是旁白内容",
        )
        assert element.type == "narration"
        assert element.content == "这是旁白内容"

    def test_scene_data(self):
        """测试场景数据"""
        scene = SceneData(
            id="scene_001",
            order=0,
            title="开场",
            location="森林",
            time_of_day="早晨",
            weather="晴朗",
        )
        assert scene.id == "scene_001"
        assert scene.order == 0
        assert scene.location == "森林"

    def test_script_data(self, sample_character):
        """测试剧本数据"""
        script = ScriptData(
            id="script_001",
            title="测试剧本",
            story_type=StoryType.ADVENTURE,
            theme="冒险",
            premise="一个冒险故事",
        )

        # 添加场景
        scene = SceneData(
            id="scene_001",
            order=0,
            title="场景1",
        )
        script.scenes.append(scene)

        # 添加角色
        script.characters[sample_character.id] = sample_character

        assert len(script.scenes) == 1
        assert len(script.characters) == 1
        assert script.total_scenes == 1


class TestStoryboardModels:
    """测试分镜相关模型"""

    def test_camera_shot(self):
        """测试镜头数据"""
        shot = CameraShot(
            id="shot_001",
            scene_id="scene_001",
            order=0,
            time_range=TimeRange(start=0.0, end=3.0),
            duration=3.0,
            shot_size=ShotSize.MEDIUM,
            camera_movement=CameraMovement.STATIC,
        )
        assert shot.id == "shot_001"
        assert shot.duration == 3.0
        assert shot.shot_size == ShotSize.MEDIUM

    def test_timeline_data(self):
        """测试时间轴数据"""
        timeline = TimelineData()

        # 添加镜头
        shot1 = CameraShot(
            id="shot_001",
            scene_id="scene_001",
            order=0,
            time_range=TimeRange(start=0.0, end=3.0),
            duration=3.0,
            shot_size=ShotSize.MEDIUM,
        )
        shot2 = CameraShot(
            id="shot_002",
            scene_id="scene_001",
            order=1,
            time_range=TimeRange(start=3.0, end=6.0),
            duration=3.0,
            shot_size=ShotSize.CLOSE,
        )

        timeline.shots.extend([shot1, shot2])

        assert timeline.total_duration == 6.0
        assert timeline.get_shot_at_time(1.5) == shot1
        assert timeline.get_shot_at_time(4.5) == shot2
        assert timeline.get_shot_at_time(10.0) is None


class TestAudioModels:
    """测试音频相关模型"""

    def test_audio_track(self):
        """测试音轨"""
        track = AudioTrack(
            id="track_001",
            type="dialogue",
            time_range=TimeRange(start=0.0, end=3.0),
            text="你好",
            volume=0.8,
        )
        assert track.id == "track_001"
        assert track.type == "dialogue"
        assert track.volume == 0.8

    def test_audio_data(self):
        """测试音频数据"""
        audio = AudioData()

        track1 = AudioTrack(
            id="track_001",
            type="dialogue",
            time_range=TimeRange(start=0.0, end=3.0),
        )
        track2 = AudioTrack(
            id="track_002",
            type="bgm",
            time_range=TimeRange(start=0.0, end=30.0),
        )

        audio.tracks.extend([track1, track2])

        tracks_at_1s = audio.get_tracks_at_time(1.0)
        assert len(tracks_at_1s) == 2


class TestGenerationResult:
    """测试生成结果"""

    def test_success_result(self):
        """测试成功结果"""
        result = GenerationResult(
            success=True,
            video_path="/path/to/video.mp4",
            generation_time=60.0,
        )
        assert result.success is True
        assert result.video_path == "/path/to/video.mp4"
        assert result.error_message is None

    def test_failure_result(self):
        """测试失败结果"""
        result = GenerationResult(
            success=False,
            error_message="生成失败",
            generation_time=10.0,
        )
        assert result.success is False
        assert result.error_message == "生成失败"
        assert result.video_path is None
