"""
阶段2：剧本生成 - 专业版

从编剧和导演角度完善剧本生成逻辑
"""

from typing import List, Optional
import re
import uuid

from app.config import Config
from app.stages import BaseStage, InputData
from app.models import (
    ScriptData, SceneData, SceneElement, StoryType, CharacterData,
    CharacterAppearance, CharacterType, Emotion, Dialogue,
    ShotSize, CameraShot, TimeRange, TimelineData,
    AudioTrack, AudioData,
)
from app.utils import get_hash


class ScriptGenerationStage(BaseStage):
    """
    剧本生成阶段

    从编剧角度：
    - 三幕式结构分析
    - 角色弧光设计
    - 对白节奏控制
    - 视觉化程度评估

    从导演角度：
    - 场景张力设计
    - 情绪曲线规划
    - 节奏呼吸点设置
    """

    # 故事类型关键词映射（扩展版）
    TYPE_KEYWORDS = {
        StoryType.ROMANCE: ["恋爱", "爱情", "喜欢", "爱", "告白", "表白", "心动", "暗恋"],
        StoryType.ADVENTURE: ["冒险", "旅程", "探险", "冒险者", "踏上", "出发", "寻找"],
        StoryType.MYSTERY: ["悬疑", "谜", "推理", "真相", "秘密", "破解", "疑点"],
        StoryType.COMEDY: ["搞笑", "喜剧", "幽默", "有趣", "好笑", "滑稽", "轻松"],
        StoryType.ACTION: ["战斗", "动作", "战争", "剑", "打斗", "对决", "战斗"],
        StoryType.FANTASY: ["魔法", "龙", "精灵", "奇幻", "魔", "咒", "异世界"],
        StoryType.HORROR: ["恐怖", "恐惧", "惊", "鬼", "怪", "吓", "诡异"],
        StoryType.HEALING: ["治愈", "温暖", "温馨", "感动", "成长", "陪伴"],
        StoryType.HOT_BLOODED: ["热血", "燃", "突破", "极限", "信念", "坚持"],
        StoryType.TRAGEDY: ["悲剧", "悲伤", "痛苦", "失去", "牺牲", "绝望"],
    }

    # 三幕式结构模板
    THREE_ACT_TEMPLATE = {
        "act1": {
            "ratio": 0.25,  # 第一幕占25%
            "elements": ["建立世界观", "介绍角色", "激励事件"],
            "pacing": "渐进",
        },
        "act2": {
            "ratio": 0.50,  # 第二幕占50%
            "elements": ["发展冲突", "角色成长", "中点转折", "危机加深"],
            "pacing": "波动上升",
        },
        "act3": {
            "ratio": 0.25,  # 第三幕占25%
            "elements": ["高潮对决", "情感释放", "故事收尾"],
            "pacing": "爆发后平缓",
        },
    }

    def generate(self, input_data: InputData) -> ScriptData:
        """生成完整剧本"""
        # 分析输入文本
        analysis = self._analyze_input(input_data.text)

        # 创建剧本
        script = ScriptData(
            id=str(uuid.uuid4()),
            title=self._generate_title(input_data.text),
            story_type=analysis["type"],
            theme=analysis["theme"],
            premise=input_data.text[:200],
            structure_type="three_act",
            metadata={
                "input_hash": get_hash(input_data.text),
                "analysis": analysis,
            }
        )

        # 解析场景（按三幕式结构组织）
        scenes = self._parse_scenes_with_structure(input_data.text, analysis)
        script.scenes.extend(scenes)

        # 解析角色
        characters = self._parse_characters_advanced(input_data.text, analysis)
        for char in characters:
            script.characters[char.id] = char

        # 计算节奏点
        self._calculate_rhythm_points(script)

        return script

    def _analyze_input(self, text: str) -> dict:
        """深度分析输入文本"""
        analysis = {
            "type": self._infer_type_advanced(text),
            "theme": self._extract_theme(text),
            "tone": self._extract_tone(text),
            "estimated_scenes": self._estimate_scene_count(text),
            "has_dialogue": self._has_dialogue(text),
            "complexity": self._assess_complexity(text),
        }
        return analysis

    def _infer_type_advanced(self, text: str) -> StoryType:
        """高级故事类型推断（带权重评分）"""
        scores = {}
        text_lower = text.lower()

        for story_type, keywords in self.TYPE_KEYWORDS.items():
            score = sum(2 if text_lower.count(k) > 1 else 1 for k in keywords if k in text_lower)
            scores[story_type] = score

        # 返回得分最高的类型
        if not scores or max(scores.values()) == 0:
            return StoryType.ADVENTURE

        return max(scores, key=scores.get)

    def _extract_theme(self, text: str) -> str:
        """提取主题关键词"""
        themes = {
            "成长": ["成长", "长大", "变化", "成熟", "进步"],
            "友情": ["朋友", "伙伴", "友情", "陪伴", "信任"],
            "爱情": ["爱", "喜欢", "恋", "情", "心动"],
            "正义": ["正义", "邪恶", "对", "错", "审判"],
            "救赎": ["救赎", "原谅", "过错", "弥补", "赎罪"],
            "勇气": ["勇气", "勇敢", "无畏", "面对", "挑战"],
            "牺牲": ["牺牲", "奉献", "付出", "舍弃"],
            "自由": ["自由", "解放", "束缚", "逃离"],
        }

        text_lower = text.lower()
        max_count = 0
        main_theme = "冒险"

        for theme, keywords in themes.items():
            count = sum(text_lower.count(k) for k in keywords)
            if count > max_count:
                max_count = count
                main_theme = theme

        return main_theme

    def _extract_tone(self, text: str) -> str:
        """提取情感基调"""
        positive_words = ["开心", "快乐", "幸福", "喜悦", "成功", "胜利", "希望"]
        negative_words = ["悲伤", "痛苦", "绝望", "失败", "死亡", "恐惧", "黑暗"]

        text_lower = text.lower()
        pos_score = sum(text_lower.count(w) for w in positive_words)
        neg_score = sum(text_lower.count(w) for w in negative_words)

        if pos_score > neg_score:
            return "积极"
        elif neg_score > pos_score:
            return "消极"
        else:
            return "中性"

    def _estimate_scene_count(self, text: str) -> int:
        """估算场景数量"""
        # 按段落估算
        paragraphs = re.split(r"\n\s*\n", text.strip())
        valid_paragraphs = [p for p in paragraphs if len(p.strip()) >= 10]

        # 每200字约1个场景
        estimated_by_length = max(3, len(text) // 200)

        # 取两者较大值
        return max(len(valid_paragraphs), estimated_by_length)

    def _has_dialogue(self, text: str) -> bool:
        """检测是否包含对话"""
        dialogue_patterns = [
            r'"[^"]+"\s*(说|道|问|答|喊)',
            r'"[^"]+"\s*：',
            r'「[^」]+」',
            r'【[^】]+】',
        ]
        return any(re.search(p, text) for p in dialogue_patterns)

    def _assess_complexity(self, text: str) -> str:
        """评估故事复杂度"""
        # 多维度评估
        length_score = min(len(text) / 1000, 1)  # 长度得分
        dialogue_score = 1 if self._has_dialogue(text) else 0.5
        scene_count = len(re.split(r"\n\s*\n", text.strip()))
        structure_score = min(scene_count / 5, 1)

        total_score = (length_score + dialogue_score + structure_score) / 3

        if total_score < 0.3:
            return "简单"
        elif total_score < 0.7:
            return "中等"
        else:
            return "复杂"

    def _generate_title(self, text: str) -> str:
        """生成故事标题"""
        # 提取关键词作为标题
        words = re.findall(r"[\u4e00-\u9fff]{2,4}", text)
        if words:
            # 取第一个有意义的词组
            return f"《{words[0]}》"
        return f"故事_{uuid.uuid4().hex[:6]}"

    def _parse_scenes_with_structure(self, text: str, analysis: dict) -> List[SceneData]:
        """按三幕式结构解析场景"""
        paragraphs = re.split(r"\n\s*\n", text.strip())
        valid_paragraphs = [p.strip() for p in paragraphs if len(p.strip()) >= 10]

        if not valid_paragraphs:
            valid_paragraphs = [text.strip()]

        total_scenes = len(valid_paragraphs)
        scenes = []

        # 计算三幕的分界点
        act1_end = max(1, int(total_scenes * self.THREE_ACT_TEMPLATE["act1"]["ratio"]))
        act2_end = int(total_scenes * (self.THREE_ACT_TEMPLATE["act1"]["ratio"] +
                                     self.THREE_ACT_TEMPLATE["act2"]["ratio"]))

        for i, para in enumerate(valid_paragraphs):
            # 确定幕次
            if i < act1_end:
                act = "第一幕（铺垫）"
                mood = "渐进"
            elif i < act2_end:
                act = "第二幕（冲突）"
                mood = "波动上升"
            else:
                act = "第三幕（高潮）"
                mood = i == total_scenes - 1 ? "平缓" : "爆发"

            scene = SceneData(
                id=f"scene_{uuid.uuid4().hex[:8]}",
                order=i,
                title=f"{act} - 场景{i+1}",
                description=para,
                atmosphere=mood,
                elements=[
                    SceneElement(
                        type="narration",
                        content=para,
                        metadata={"act": act, "mood": mood}
                    )
                ],
            )
            scenes.append(scene)

        return scenes

    def _parse_characters_advanced(self, text: str, analysis: dict) -> List[CharacterData]:
        """高级角色解析"""
        characters = []

        # 对话模式识别（更精确）
        dialogue_patterns = [
            r'([A-Za-z\u4e00-\u9fff]{2,4})[：:]["「]',
            r'([A-Za-z\u4e00-\u9fff]{2,4})说[：:]"',
            r'([A-Za-z\u4e00-\u9fff]{2,4})道[：:]"',
            r'([A-Za-z\u4e00-\u9fff]{2,4})问[：:]"',
            r'([A-Za-z\u4e00-\u9fff]{2,4})答[：:]"',
        ]

        found_chars = set()
        for pattern in dialogue_patterns:
            matches = re.findall(pattern, text)
            found_chars.update(matches)

        # 如果没有找到对话角色，尝试其他方式
        if not found_chars:
            # 寻找可能的人名（大写字母开头的连续汉字）
            possible_names = re.findall(r'([A-Z][a-z]+)|([\u4e00-\u9fff]{2,3}(?:说|想|看|听|走))', text)
            found_chars.update([n[0] or n[1] for n in possible_names])

        # 如果还是没找到，创建默认角色
        if not found_chars:
            char = CharacterData(
                id=f"char_{uuid.uuid4().hex[:8]}",
                name="主角",
                character_type=CharacterType.PROTAGONIST,
                description=analysis.get("theme", "故事") + "的主角",
                personality=self._infer_personality(text),
                appearance=CharacterAppearance(
                    age=self._infer_age(text),
                    gender="androgynous",  # 默认中性
                    hair_style="average",
                    hair_color="black",
                ),
                voice_description=self._infer_voice(text),
            )
            characters.append(char)
        else:
            # 为找到的角色创建数据
            for i, name in enumerate(found_chars):
                if i == 0:
                    char_type = CharacterType.PROTAGONIST
                    desc = "故事的主要角色"
                elif i == 1:
                    char_type = CharacterType.SUPPORTING
                    desc = "重要配角"
                else:
                    char_type = CharacterType.SUPPORTING
                    desc = "其他角色"

                char = CharacterData(
                    id=f"char_{uuid.uuid4().hex[:8]}",
                    name=name,
                    character_type=char_type,
                    description=desc,
                    personality=self._infer_personality_from_name(name),
                    appearance=CharacterAppearance(
                        age=self._infer_age(text),
                        gender="androgynous",
                    ),
                )
                characters.append(char)

        return characters

    def _infer_personality(self, text: str) -> List[str]:
        """从文本推断性格"""
        personality_keywords = {
            "勇敢": ["勇敢", "无畏", "敢于", "冲", "面对"],
            "善良": ["善良", "温柔", "帮助", "保护", "关怀"],
            "聪明": ["聪明", "智慧", "机智", "想", "计划"],
            "内向": ["安静", "沉默", "害羞", "独处"],
            "外向": ["开朗", "活泼", "热情", "朋友"],
            "冷酷": ["冷酷", "冷漠", "无情", "冰"],
            "热血": ["热血", "激情", "燃烧", "信念"],
        }

        text_lower = text.lower()
        personalities = []
        for personality, keywords in personality_keywords.items():
            if any(k in text_lower for k in keywords):
                personalities.append(personality)

        return personalities[:3] if personalities else ["未知"]

    def _infer_personality_from_name(self, name: str) -> List[str]:
        """从名字推断性格（简化版）"""
        # 这里可以扩展更复杂的逻辑
        return ["待定"]

    def _infer_age(self, text: str) -> str:
        """推断角色年龄"""
        age_keywords = {
            "child": ["儿童", "小孩", "孩子", "幼"],
            "teenager": ["少年", "少女", "青少年", "学生"],
            "young adult": ["青年", "年轻人", "成"],
            "middle-aged": ["中年", "大叔", "阿姨"],
            "elderly": ["老人", "老", "祖父", "祖母"],
        }

        text_lower = text.lower()
        for age, keywords in age_keywords.items():
            if any(k in text_lower for k in keywords):
                return age
        return "young adult"

    def _infer_voice(self, text: str) -> str:
        """推断声音特征"""
        tone = self._extract_tone(text)
        if tone == "积极":
            return "明亮、充满活力"
        elif tone == "消极":
            return "低沉、略带沙哑"
        else:
            return "温和、平静"

    def _calculate_rhythm_points(self, script: ScriptData):
        """计算节奏点（导演视角）"""
        if not script.scenes:
            return

        total = len(script.scenes)
        for i, scene in enumerate(script.scenes):
            # 计算当前场景在故事中的位置比例
            position = i / total if total > 0 else 0

            # 根据位置确定节奏类型
            if position < 0.25:
                # 开场 - 舒缓引入
                scene.metadata["rhythm"] = "slow"
                scene.metadata["intensity"] = 0.3
            elif position < 0.5:
                # 发展 - 逐渐加快
                scene.metadata["rhythm"] = "medium"
                scene.metadata["intensity"] = 0.5
            elif position < 0.75:
                # 冲突加剧 - 快节奏
                scene.metadata["rhythm"] = "fast"
                scene.metadata["intensity"] = 0.8
            else:
                # 高潮与结局 - 波动
                if i == total - 1:
                    scene.metadata["rhythm"] = "slow"  # 结尾平缓
                    scene.metadata["intensity"] = 0.4
                else:
                    scene.metadata["rhythm"] = "fast"  # 高潮
                    scene.metadata["intensity"] = 1.0


# 保持向后兼容的别名
InputData = InputData
