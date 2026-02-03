"""
pytest配置和共享fixture
"""

import pytest
import tempfile
from pathlib import Path
from typing import Generator

from frameleap.config import Settings, VideoConfig, StyleConfig, LLMConfig


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """临时目录fixture"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_settings(temp_dir: Path) -> Settings:
    """测试配置fixture"""
    settings = Settings()

    # 使用临时目录
    from frameleap.config import PathConfig
    settings.paths = PathConfig(
        work_dir=temp_dir / "work",
        temp_dir=temp_dir / "temp",
        cache_dir=temp_dir / "cache",
        model_dir=temp_dir / "models",
        lora_dir=temp_dir / "models" / "loras",
        output_dir=temp_dir / "output",
    )

    # 降低并发，加快测试
    settings.max_workers = 2
    settings.batch_size = 2

    return settings


@pytest.fixture
def sample_input_text() -> str:
    """示例输入文本"""
    return "一个少年在雨夜中遇到了神秘少女，展开了一段奇幻的冒险旅程。"


@pytest.fixture
def sample_long_input() -> str:
    """示例长文本输入"""
    return """
    在一个被遗忘的古老王国里，年轻的冒险者艾琳发现了一张神秘的地图。
    这张地图指向传说中失落已久的龙之宝藏。然而，邪恶的黑骑士也在寻找同样的宝藏，
    他妄图利用宝藏的力量征服整个大陆。艾琳必须集结她的伙伴们，
    包括勇敢的战士凯尔、智慧的法师莉娜，以及机智的盗贼卢卡斯，
    在黑骑士之前找到宝藏，拯救王国于危难之中。
    这是一场关于勇气、友情和成长的冒险。
    """


# =============================================================================
# 数据模型fixture
# =============================================================================

@pytest.fixture
def sample_character():
    """示例角色数据"""
    from frameleap.models import CharacterData, CharacterAppearance, CharacterType

    return CharacterData(
        id="char_001",
        name="艾琳",
        character_type=CharacterType.PROTAGONIST,
        description="年轻勇敢的冒险者，寻找龙之宝藏",
        personality=["勇敢", "善良", "坚韧"],
        appearance=CharacterAppearance(
            age="16 year old",
            gender="female",
            hair_style="long",
            hair_color="brown",
            eye_color="green",
            outfit="adventurer outfit with cloak",
        ),
    )


@pytest.fixture
def sample_script():
    """示例剧本数据"""
    from frameleap.models import ScriptData, SceneData, SceneElement, StoryType

    script = ScriptData(
        id="script_001",
        title="龙之宝藏",
        story_type=StoryType.ADVENTURE,
        theme="冒险与成长",
        premise="年轻冒险者寻找龙之宝藏，拯救王国",
    )

    # 添加场景
    for i in range(3):
        scene = SceneData(
            id=f"scene_{i+1:03d}",
            order=i,
            title=f"场景{i+1}",
            location=f"地点{i+1}",
            elements=[
                SceneElement(
                    type="narration",
                    content=f"这是场景{i+1}的内容描述",
                )
            ],
        )
        script.scenes.append(scene)

    return script


# =============================================================================
# Mock fixture
# =============================================================================

@pytest.fixture
def mock_llm_response(monkeypatch):
    """Mock LLM响应"""
    def mock_generate(*args, **kwargs):
        return "Mocked LLM response"

    monkeypatch.setattr("frameleap.stages.llm_generate", mock_generate)
    return mock_generate


@pytest.fixture
def mock_image_gen(monkeypatch, temp_dir: Path):
    """Mock图像生成"""
    def mock_generate(*args, **kwargs):
        # 创建假图像文件
        img_path = temp_dir / "mock_image.png"
        img_path.write_bytes(b"fake image data")
        return str(img_path)

    monkeypatch.setattr("frameleap.stages.generate_image", mock_generate)
    return mock_generate
