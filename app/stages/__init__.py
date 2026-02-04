"""
处理阶段模块 - 单用户简化版
"""

from abc import ABC, abstractmethod
from typing import Any
from pathlib import Path

from app.config import Config
from app.models import (
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
        print(f"[DEBUG] BaseStage.__init__ for {self.__class__.__name__}")
        self.cfg = cfg
        self.temp_dir = cfg.paths.temp_dir
        print(f"[DEBUG] BaseStage.__init__ done for {self.__class__.__name__}")

    # 暂时移除 @abstractmethod 来测试
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

    def __init__(self):
        self.text = ""
        self.style = None
        self.metadata = {}


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

print("[DEBUG] About to define ScriptGenerationStage class")

class ScriptGenerationStage(BaseStage):
    """剧本生成阶段 - 调用千问LLM"""

    def __init__(self, cfg: Config):
        super().__init__(cfg)
        self.llm_api = self._create_llm_api()

    def _create_llm_api(self):
        """创建LLM API实例"""
        provider = self.cfg.api.llm_provider  # 从配置读取，默认"qwen"
        api_key = self.cfg.api.llm_api_key

        if not api_key:
            print("[WARN] 未设置LLM API密钥，剧本生成将使用简化逻辑")
            return None

        try:
            from app.utils.domestic_apis import create_llm_api
            return create_llm_api(provider, api_key)
        except Exception as e:
            print(f"[ERROR] 创建LLM API失败: {e}")
            return None

    def generate(self, input_data: InputData) -> ScriptData:
        """生成剧本"""
        import uuid

        # 如果LLM API可用，调用LLM生成
        if self.llm_api:
            print(f"[DEBUG] 使用LLM生成剧本...")
            return self._generate_with_llm(input_data)
        else:
            print(f"[DEBUG] 使用简化逻辑生成剧本...")
            return self._generate_fallback(input_data)

    def _generate_with_llm(self, input_data: InputData) -> ScriptData:
        """使用千问LLM生成剧本"""
        import uuid
        import json

        # 构建提示词
        prompt = self._build_prompt(input_data)

        try:
            # 调用千问API
            response = self.llm_api.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=4000
            )
            print(f"[DEBUG] LLM响应长度: {len(response)} 字符")

            # 尝试解析LLM返回的JSON
            try:
                script_data = json.loads(response)
            except json.JSONDecodeError:
                print("[WARN] LLM返回的不是有效JSON，尝试提取JSON片段")
                # 尝试提取JSON片段
                import re
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    script_data = json.loads(json_match.group(0))
                else:
                    raise ValueError("无法从LLM响应中提取JSON")

            # 创建ScriptData对象
            script = ScriptData(
                id=str(uuid.uuid4()),
                title=script_data.get("title", "生成的剧本"),
                story_type=self._parse_story_type(script_data.get("story_type", "adventure")),
                theme=script_data.get("theme", "冒险"),
                premise=input_data.text[:200],
            )

            # 解析场景
            for scene_data in script_data.get("scenes", []):
                scene = SceneData(
                    id=f"scene_{uuid.uuid4().hex[:8]}",
                    order=scene_data.get("order", 0),
                    title=scene_data.get("title", "场景"),
                    description=scene_data.get("description", ""),
                    atmosphere=scene_data.get("atmosphere", "normal"),
                    elements=[
                        SceneElement(
                            type="narration",
                            content=scene_data.get("description", "")
                        )
                    ]
                )
                script.scenes.append(scene)

            # 解析角色
            for char_data in script_data.get("characters", []):
                char = CharacterData(
                    id=f"char_{uuid.uuid4().hex[:8]}",
                    name=char_data.get("name", "角色"),
                    character_type=self._parse_character_type(char_data.get("type", "supporting")),
                    description=char_data.get("description", ""),
                    personality=char_data.get("personality", []),
                    appearance=CharacterAppearance(
                        age=char_data.get("age", "young adult"),
                        gender=char_data.get("gender", "androgynous"),
                    )
                )
                script.characters[char.id] = char

            print(f"[DEBUG] LLM生成成功: {len(script.scenes)} 场景, {len(script.characters)} 角色")
            return script

        except Exception as e:
            import traceback
            print(f"[ERROR] LLM生成失败，回退到简化逻辑")
            print(f"[ERROR] 错误类型: {type(e).__name__}")
            print(f"[ERROR] 错误信息: {str(e)}")
            traceback.print_exc()
            return self._generate_fallback(input_data)

    def _build_prompt(self, input_data: InputData) -> str:
        """构建LLM提示词"""
        return f"""你是一个专业的编剧。请根据用户的输入，生成一个完整的剧本。

用户输入：{input_data.text}

请严格按照以下JSON格式返回剧本（不要有任何其他文字）：
{{
    "title": "简短的剧本标题",
    "story_type": "adventure",
    "theme": "主题关键词",
    "scenes": [
        {{
            "order": 0,
            "title": "场景1标题",
            "description": "场景的详细描述，100-200字",
            "atmosphere": "场景氛围"
        }}
    ],
    "characters": [
        {{
            "name": "角色名称",
            "type": "protagonist",
            "description": "角色描述",
            "personality": ["性格特点1", "性格特点2"],
            "age": "年龄描述",
            "gender": "性别描述"
        }}
    ]
}}

要求：
1. 生成3-6个场景
2. 每个场景描述100-200字
3. 识别1-3个主要角色
4. story_type只能从这些选择：adventure, romance, mystery, comedy, action, fantasy
5. 只返回JSON，不要有任何其他文字"""

    def _generate_fallback(self, input_data: InputData) -> ScriptData:
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

    def _parse_story_type(self, type_str: str) -> StoryType:
        """解析故事类型字符串为枚举"""
        type_map = {
            "adventure": StoryType.ADVENTURE,
            "romance": StoryType.ROMANCE,
            "mystery": StoryType.MYSTERY,
            "comedy": StoryType.COMEDY,
            "action": StoryType.ACTION,
            "fantasy": StoryType.FANTASY,
        }
        return type_map.get(type_str.lower(), StoryType.ADVENTURE)

    def _parse_character_type(self, type_str: str) -> CharacterType:
        """解析角色类型字符串为枚举"""
        type_map = {
            "protagonist": CharacterType.PROTAGONIST,
            "supporting": CharacterType.SUPPORTING,
        }
        return type_map.get(type_str.lower(), CharacterType.SUPPORTING)


# =============================================================================
# 阶段3：画面描述生成阶段
# =============================================================================

class SceneDescriptionData:
    """场景描述数据"""
    scene_id: str
    description: str
    prompt: str
    negative_prompt: str = ""

    def __init__(self):
        self.scene_id = ""
        self.description = ""
        self.prompt = ""
        self.negative_prompt = ""


class SceneDescriptionStage(BaseStage):
    """画面描述生成阶段 - 使用LLM生成高质量AI绘画提示词"""

    def __init__(self, cfg: Config):
        super().__init__(cfg)
        self.llm_api = self._create_llm_api()

    def _create_llm_api(self):
        """创建LLM API实例用于生成提示词"""
        provider = self.cfg.api.llm_provider
        api_key = self.cfg.api.llm_api_key

        if not api_key:
            print("[WARN] 未设置LLM API密钥，提示词生成将使用简化逻辑")
            return None

        try:
            from app.utils.domestic_apis import create_llm_api
            return create_llm_api(provider, api_key)
        except Exception as e:
            print(f"[ERROR] 创建LLM API失败: {e}")
            return None

    def generate(self, script: ScriptData) -> list[SceneDescriptionData]:
        """生成场景描述和高质量AI绘画提示词"""
        descriptions = []

        for i, scene in enumerate(script.scenes):
            print(f"[DEBUG] 生成场景 {i+1}/{len(script.scenes)} 的提示词: {scene.title}")

            desc = SceneDescriptionData()
            desc.scene_id = scene.id
            desc.description = scene.description or scene.title

            # 如果LLM可用，使用LLM生成详细提示词
            if self.llm_api:
                desc.prompt = self._generate_prompt_with_llm(scene, script)
                desc.negative_prompt = self._build_negative()
            else:
                # 回退到简单提示词
                desc.prompt = self._build_simple_prompt(scene)
                desc.negative_prompt = self._build_negative()

            print(f"[DEBUG] 提示词长度: {len(desc.prompt)} 字符")
            descriptions.append(desc)

        return descriptions

    def _generate_prompt_with_llm(self, scene: SceneData, script: ScriptData) -> str:
        """使用LLM生成详细的AI绘画提示词"""
        import json

        # 构建提示词生成请求
        style = self.cfg.style.art_style
        style_desc = self._get_style_description(style)

        prompt = f"""你是一个专业的AI绘画提示词专家。请根据以下场景信息，生成一个高质量的AI绘画提示词。

**场景信息：**
- 场景标题：{scene.title}
- 场景描述：{scene.description or '无详细描述'}
- 场景氛围：{scene.atmosphere or '普通'}
- 艺术风格：{style}（{style_desc}）
- 故事主题：{script.theme}

**提示词要求：**
1. 详细的视觉描述（主体、动作、表情、服装等）
2. 环境和背景细节
3. 构图和景别
4. 光影效果
5. 色彩方案
6. 质量标签（masterpiece, best quality等）
7. 风格相关的关键词

**输出格式：**
请直接返回提示词文本，不要有任何解释或其他文字。提示词应该用英文，用逗号分隔不同的元素。

示例格式：
masterpiece, best quality, highly detailed, 主体描述, 动作姿态, 服装细节, 表情神态, 环境背景, 构图描述, 光影效果, 色彩描述, 风格关键词

注意：直接描述具体的视觉效果，使用英文关键词。
"""

        try:
            print(f"[DEBUG] 调用LLM生成提示词...")
            response = self.llm_api.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=500
            )
            print(f"[DEBUG] LLM生成的提示词长度: {{len(response)}} 字符")
            return response.strip()
        except Exception as e:
            print(f"[ERROR] LLM生成提示词失败: {{e}}，使用简化逻辑")
            return self._build_simple_prompt(scene)

    def _build_simple_prompt(self, scene: SceneData) -> str:
        """构建简单的提示词（回退方案）"""
        from app.utils import build_prompt

        style = self.cfg.style.art_style
        subject = scene.description or scene.title

        return build_prompt(subject=subject, style=style)

    def _build_negative(self) -> str:
        """构建负面提示词"""
        from app.utils import build_negative_prompt
        return build_negative_prompt()

    def _get_style_description(self, style: str) -> str:
        """获取风格的详细描述"""
        style_map = {
            "anime": "日式动漫风格，扁平色彩，简洁线条",
            "manhwa": "韩漫风格，色彩鲜艳，细节丰富",
            "manhua": "国漫风格，传统绘画元素",
            "watercolor": "水彩风格，柔和透明",
            "oil": "油画风格，厚重质感",
            "sketch": "素描风格，线条为主",
            "flat": "扁平化设计，简洁明了",
        }
        return style_map.get(style, "通用风格")


# =============================================================================
# 阶段4：图像生成阶段
# =============================================================================

class ImageGenerationStage(BaseStage):
    """图像生成阶段"""

    def __init__(self, cfg: Config):
        super().__init__(cfg)
        self.api = self._create_api()

    def generate(self, descriptions: list[SceneDescriptionData]) -> list[str]:
        """生成图像"""
        import time
        image_paths = []

        print(f"[DEBUG] ImageGenerationStage.generate: 开始生成 {len(descriptions)} 张图像")
        print(f"[DEBUG] API可用: {self.api is not None}")
        print(f"[DEBUG] API密钥: {bool(self.cfg.api.image_api_key)}")

        for i, desc in enumerate(descriptions):
            path = self.temp_dir / f"scene_{desc.scene_id}.png"
            print(f"[DEBUG] 生成场景 {i+1}/{len(descriptions)}: {desc.scene_id}")

            # 如果API可用，调用生成
            if self.api and self.cfg.api.image_api_key:
                print(f"[DEBUG] 调用API生成图像: {path}")
                self._generate_image(desc.prompt, desc.negative_prompt, path)
                print(f"[DEBUG] 图像生成完成: {path.exists()}")

                # 添加延迟避免速率限制（通义万相有QPS限制）
                if i < len(descriptions) - 1:  # 最后一个不需要延迟
                    print(f"[DEBUG] 等待2秒避免速率限制...")
                    time.sleep(2)
            else:
                print(f"[WARN] API不可用，创建占位文件: {path}")
                # 创建占位文件
                path.touch()

            # 只返回文件名，不返回完整路径（便于前端构造URL）
            image_paths.append(path.name)

        print(f"[DEBUG] 图像生成完成，共 {len(image_paths)} 张")
        print(f"[DEBUG] 返回文件名列表: {image_paths}")
        return image_paths

    def _create_api(self):
        """创建API实例"""
        from app.utils.domestic_apis import create_image_api

        provider = self.cfg.api.image_provider
        api_key = self.cfg.api.image_api_key

        if not api_key and provider not in ["local"]:
            print(f"[WARN] 图像API密钥未配置，provider={provider}")
            return None

        try:
            print(f"[DEBUG] 创建图像API: provider={provider}")
            kwargs = {"api_key": api_key}
            if provider == "local":
                kwargs = {"base_url": self.cfg.api.image_base_url or "http://127.0.0.1:7860"}
            api = create_image_api(provider, **kwargs)
            print(f"[DEBUG] 图像API创建成功")
            return api
        except Exception as e:
            print(f"[ERROR] 创建图像API失败: {e}")
            return None

    def _generate_image(self, prompt: str, negative: str, output_path: Path):
        """生成单张图像"""
        try:
            print(f"[DEBUG] 调用API.generate, prompt长度: {len(prompt)}")
            print(f"[DEBUG] 尺寸: {self.cfg.video.width}x{self.cfg.video.height}")
            print(f"[DEBUG] 输出路径: {output_path}")
            print(f"[DEBUG] 输出路径(绝对): {output_path.absolute()}")

            image_data = self.api.generate(
                prompt=prompt,
                negative=negative,
                width=self.cfg.video.width,
                height=self.cfg.video.height,
            )

            print(f"[DEBUG] API返回数据长度: {len(image_data)} 字节")

            # 确保父目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)

            output_path.write_bytes(image_data)
            print(f"[DEBUG] 图像已保存: {output_path}")
            print(f"[DEBUG] 图像文件存在: {output_path.exists()}")
            print(f"[DEBUG] 图像文件大小: {output_path.stat().st_size if output_path.exists() else 0} 字节")
        except Exception as e:
            import traceback
            print(f"[ERROR] 图像生成失败: {e}")
            traceback.print_exc()
            output_path.touch()


# =============================================================================
# 阶段5：分镜编排阶段
# =============================================================================

class StoryboardData:
    """分镜数据"""
    timeline: TimelineData

    def __init__(self, timeline: TimelineData = None):
        self.timeline = timeline or TimelineData()


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

    def __init__(self):
        self.frames = []


class AnimationStage(BaseStage):
    """动画化阶段"""
    def animate(self, storyboard: StoryboardData) -> AnimationData:
        return AnimationData()


class TextLayerData:
    """文字层数据"""
    subtitles: list[dict] = []
    bubbles: list[dict] = []

    def __init__(self):
        self.subtitles = []
        self.bubbles = []


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

    def __init__(self):
        self.path = None


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
