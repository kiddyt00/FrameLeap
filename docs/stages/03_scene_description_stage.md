# 阶段3：画面描述生成阶段详细说明

## 1. 概述

画面描述生成阶段负责将剧本中的抽象描述转化为具体的、可直接用于图像生成的视觉描述和提示词。本阶段是连接剧本文字与AI图像生成的关键桥梁。

---

## 2. 场景描述生成

### 2.1 环境描述

#### 环境要素分解

**环境描述模板**：
```json
{
  "scene_description": {
    "scene_id": "scene_001",
    "location": {
      "type": "城市街道",
      "specific_features": [
        "湿漉漉的柏油路面",
        "昏暗的路灯",
        "老旧的建筑",
        "积水的路面反射灯光"
      ]
    },
    "time": {
      "time_of_day": "深夜",
      "lighting_condition": "昏暗、低对比度",
      "light_sources": [
        {
          "type": "路灯",
          "color": "暖黄色",
          "intensity": "弱",
          "position": "街道两侧"
        },
        {
          "type": "月光",
          "color": "冷蓝色",
          "intensity": "极弱",
          "position": "天空"
        }
      ]
    },
    "weather": {
      "condition": "大雨",
      "intensity": "强烈",
      "visual_effects": [
        "雨滴形成帘幕",
        "路面飞溅的水花",
        "雨雾弥漫"
      ]
    },
    "atmosphere": {
      "mood": "孤独、忧郁、神秘",
      "color_tone": "冷色调主导",
      "dominant_colors": ["深蓝", "黑色", "灰蓝"],
      "accent_colors": ["暖黄（路灯）", "银白（闪电）"]
    }
  }
}
```

#### 环境类型库

**预设环境类型**：

| 类型 | 子类型 | 特征描述 | 关键词 |
|-----|-------|---------|--------|
| 室内 | 教室 | 课桌椅、黑板、窗户 | classroom, desks, blackboard |
| | 卧室 | 床、衣柜、书桌 | bedroom, bed, wardrobe |
| | 咖啡馆 | 桌椅、吧台、灯光 | cafe, tables, warm lighting |
| 室外 | 街道 | 建筑、路面、路灯 | street, buildings, streetlights |
| | 公园 | 树木、长椅、天空 | park, trees, bench, sky |
| | 海边 | 海浪、沙滩、地平线 | beach, waves, horizon |
| 奇幻 | 魔法森林 | 发光植物、神秘氛围 | magical forest, glowing plants |
| | 天空之城 | 云端、浮空岛 | sky city, floating islands |
| | 龙之洞穴 | 岩石、火光、宝藏 | dragon cave, lava, treasure |
| 科幻 | 赛博都市 | 霓虹灯、高楼、全息投影 | cyberpunk city, neon, holograms |
| | 太空船 | 金属、控制台、星空 | spaceship, metal, control panel |
| | 实验室 | 设备、屏幕、冷光 | laboratory, equipment, screens |

### 2.2 构图描述

#### 构图规则

**基础构图类型**：

```json
{
  "composition_types": {
    "rule_of_thirds": {
      "name": "三分法",
      "description": "将画面分为9宫格，主体位于交叉点",
      "best_for": ["人物肖像", "风景"],
      "prompt_addition": "rule of thirds composition"
    },
    "center_composition": {
      "name": "中心构图",
      "description": "主体位于画面正中央",
      "best_for": ["特写", "对称场景"],
      "prompt_addition": "centered composition, symmetrical"
    },
    "golden_ratio": {
      "name": "黄金比例",
      "description": "按黄金螺旋排列元素",
      "best_for": ["艺术感画面"],
      "prompt_addition": "golden ratio composition"
    },
    "leading_lines": {
      "name": "引导线",
      "description": "利用线条引导视线",
      "best_for": ["街道", "走廊", "河流"],
      "prompt_addition": "leading lines, perspective"
    },
    "frame_within_frame": {
      "name": "框式构图",
      "description": "利用前景形成画框",
      "best_for": ["窗户", "门洞", "树枝"],
      "prompt_addition": "framed composition"
    }
  }
}
```

#### 构图自动选择

```python
def select_composition(shot_info, scene_info):
    """根据镜头信息选择合适的构图"""

    # 远景/大远景 → 三分法或中心构图
    if shot_info["shot_size"] in ["远全景", "大远景"]:
        if scene_info.get("symmetrical", False):
            return "center_composition"
        else:
            return "rule_of_thirds"

    # 特写 → 中心构图
    elif shot_info["shot_size"] in ["特写", "大特写"]:
        return "center_composition"

    # 街道/走廊场景 → 引导线
    elif scene_info["location"]["type"] in ["街道", "走廊", "桥梁"]:
        return "leading_lines"

    # 窗户/门洞场景 → 框式构图
    elif has_framing_elements(scene_info):
        return "frame_within_frame"

    # 默认
    else:
        return "rule_of_thirds"
```

#### 视角描述

**视角类型定义**：

| 视角 | 英文 | 效果 | 适用场景 |
|-----|------|------|---------|
| 平视 | eye level | 平和、客观 | 大多数对话场景 |
| 俯视 | high angle | 压迫、渺小 | 展示角色弱势地位 |
| 仰视 | low angle | 威严、强大 | 展示角色强势/英雄 |
| 荷兰角 | dutch angle | 不安、紧张 | 悬疑、冲突场景 |
| 鸟瞰 | bird's eye | 全局视角 | 战斗、大场面 |
| 虫视 | worm's eye | 巨大感 | 巨大物体、建筑 |

### 2.3 留白处理

#### 对话气泡区域预留

**预留规则**：
```json
{
  "speech_bubble_placement": {
    "strategy": "auto_reserve",
    "rules": [
      {
        "condition": "单人画面，角色偏左/右",
        "placement": "对侧空白区域",
        "size_ratio": "画面15-25%"
      },
      {
        "condition": "双人对话",
        "placement": "两人之间的上方或下方",
        "size_ratio": "画面20-30%"
      },
      {
        "condition": "多人群像",
        "placement": "画面顶部或底部统一区域",
        "size_ratio": "画面10-15%"
      }
    ],
    "prompt_modifications": {
      "reserve_top": "leave empty space at top for text",
      "reserve_bottom": "leave empty space at bottom for text",
      "reserve_side": "leave empty space on side for text"
    }
  }
}
```

**空间分配计算**：
```python
def calculate_speech_bubble_area(image_size, character_positions):
    """计算对话气泡预留区域"""

    width, height = image_size
    reserved_areas = []

    # 检测画面中的主要空白区域
    empty_regions = detect_empty_regions(character_positions)

    # 选择最合适的区域
    best_region = select_best_region(empty_regions, criteria=[
        "largest_area",
        "away_from_focal_point",
        "balanced_composition"
    ])

    # 计算预留框
    bubble_area = {
        "x": best_region["x"],
        "y": best_region["y"],
        "width": min(best_region["width"], width * 0.25),
        "height": min(best_region["height"], height * 0.25),
        "position": best_region["position"]  # top/bottom/left/right
    }

    return bubble_area
```

---

## 3. 提示词（Prompt）工程

### 3.1 图像生成提示词构建

#### 提示词结构模板

**标准提示词结构**：
```
[质量词] + [主体描述] + [动作/姿势] + [服装/外观] + [表情] + [环境] + [构图] + [风格] + [技术词] + [负面提示词]
```

**示例拆解**：
```
masterpiece, best quality, highly detailed
A 16-year-old anime boy with short messy black hair and amber eyes
standing alone in the rain at night
wearing a black school uniform with a red tie
melancholic expression, looking down
rainy city street at night, streetlights reflecting on wet pavement
eye level shot, rule of thirds
anime style, cel shading, cool color tone, soft lighting
cinematic lighting, 8k resolution, sharp focus
nsfw, low quality, blurry, deformed, watermark, text
```

#### 主体描述生成

**角色主体Prompt构建**：
```python
def build_character_prompt(character_info, current_action):
    """构建角色主体提示词"""

    prompt_parts = []

    # 基础信息
    prompt_parts.append(f"{character_info['age']} year old anime {character_info['gender']}")
    prompt_parts.append(character_info['appearance']['hair'])
    prompt_parts.append(f"{character_info['appearance']['eyes']['color']} eyes")
    prompt_parts.append(character_info['appearance']['body_type'])

    # 服装
    prompt_parts.append(f"wearing {character_info['outfit']['current']}")

    # 动作/姿势
    if current_action:
        prompt_parts.append(current_action['description'])
        prompt_parts.append(current_action['pose'])

    # 表情
    prompt_parts.append(current_action.get('expression', 'neutral'))

    # 性格特征（通过姿态/表情体现）
    if character_info.get('personality'):
        prompt_parts.append(character_info['personality']['vibe'])

    return ", ".join(prompt_parts)
```

**主体描述要素库**：

| 类别 | 要素 | 示例 |
|-----|------|------|
| 年龄 | child, teenager, young adult, middle-aged, elderly | 16 year old teenage boy |
| 性别 | male, female, androgynous | anime girl, young woman |
| 发型 | short, long, messy, sleek, ponytail, twin tails | short messy black hair |
| 发色 | black, brown, blonde, red, blue, silver, white | silver hair |
| 瞳色 | brown, blue, green, amber, red, heterochromia | amber eyes |
| 体型 | slim, athletic, muscular, petite | slim build, athletic |
| 服装 | school uniform, casual wear, armor, kimono | black school uniform |
| 表情 | happy, sad, angry, surprised, melancholic | melancholic expression |

### 3.2 环境描述生成

**环境Prompt构建函数**：
```python
def build_environment_prompt(scene_info):
    """构建环境提示词"""

    prompt_parts = []

    # 基础场景
    prompt_parts.append(scene_info['location']['type'])

    # 时间
    if 'time' in scene_info:
        prompt_parts.append(f"at {scene_info['time']['time_of_day']}")

    # 天气
    if 'weather' in scene_info:
        prompt_parts.append(scene_info['weather']['condition'])
        prompt_parts.append(f"{scene_info['weather']['intensity']} {scene_info['weather']['condition']}")

    # 光照
    if 'lighting' in scene_info:
        for light in scene_info['lighting']['sources']:
            prompt_parts.append(f"{light['intensity']} {light['type']} lighting")

    # 氛围
    prompt_parts.append(scene_info['atmosphere']['mood'])

    # 色调
    prompt_parts.append(f"{scene_info['atmosphere']['color_tone']} color tone")

    # 具体细节
    if 'details' in scene_info:
        prompt_parts.extend(scene_info['details'])

    return ", ".join(prompt_parts)
```

### 3.3 风格修饰词

#### 艺术风格库

```json
{
  "art_styles": {
    "japanese_manga": {
      "name": "日式漫画",
      "prompts": [
        "anime style",
        "manga style",
        "cel shading",
        "clean lineart",
        "flat colors"
      ]
    },
    "american_comics": {
      "name": "美式漫画",
      "prompts": [
        "comic book style",
        "bold lineart",
        "heavy shading",
        "dynamic composition"
      ]
    },
    "watercolor": {
      "name": "水彩风",
      "prompts": [
        "watercolor painting",
        "soft edges",
        "transparent colors",
        "artistic brushstrokes"
      ]
    },
    "semi_realistic": {
      "name": "半写实",
      "prompts": [
        "semi-realistic anime",
        "detailed features",
        "soft shading",
        "anatomically correct"
      ]
    },
    "chibi": {
      "name": "Q版",
      "prompts": [
        "chibi style",
        "cute",
        "deformed proportions",
        "large head"
      ]
    },
    "pixel_art": {
      "name": "像素风",
      "prompts": [
        "pixel art",
        "16-bit",
        "retro game style",
        "limited color palette"
      ]
    }
  }
}
```

#### 渲染风格库

```json
{
  "render_styles": {
    "lineart_strength": {
      "none": "no lineart, painting only",
      "weak": "subtle lineart",
      "medium": "clean lineart",
      "strong": "bold lineart, thick outlines"
    },
    "shading": {
      "flat": "flat colors, no shading",
      "basic": "basic cel shading",
      "detailed": "detailed shading, good contrast",
      "realistic": "realistic shading, ambient occlusion"
    },
    "lighting": {
      "flat": "flat lighting",
      "soft": "soft lighting, diffuse",
      "dramatic": "dramatic lighting, high contrast",
      "cinematic": "cinematic lighting, volumetric light"
    }
  }
}
```

### 3.4 质量词与修饰词

#### 质量词库

```json
{
  "quality_tags": {
    "basic": [
      "masterpiece",
      "best quality",
      "high quality",
      "highres"
    ],
    "detail": [
      "highly detailed",
      "intricate details",
      "fine details",
      "sharp focus"
    ],
    "aesthetic": [
      "beautiful",
      "aesthetically pleasing",
      "elegant",
      "harmonious"
    ],
    "composition": [
      "perfect composition",
      "well composed",
      "balanced",
      "professional"
    ]
  }
}
```

#### 负面提示词库

```json
{
  "negative_prompts": {
    "quality": [
      "low quality",
      "worst quality",
      "blurry",
      "out of focus",
      "jpeg artifacts"
    ],
    "anatomy": [
      "bad anatomy",
      "deformed",
      "disfigured",
      "poorly drawn face",
      "extra limbs",
      "missing limbs"
    ],
    "content": [
      "nsfw",
      "nude",
      "violence",
      "gore",
      "disturbing"
    ],
    "artifacts": [
      "watermark",
      "signature",
      "text",
      "logo",
      "border"
    ]
  }
}
```

### 3.5 SD/MJ专用格式

#### Stable Diffusion格式

**权重标注语法**：
```
# 提高权重（使用括号）
(red dress:1.2)        # 权重1.2倍
((blue eyes:1.4))      # 权重1.4倍（双重括号）

# 降低权重（使用方括号）
[background:0.8]       # 权重0.8倍

# 混合提示词（交替）
[sunny|rainy]          # 50% sunny + 50% rainy
[cat|dog:0.3]          # 70% cat + 30% dog

# 范围提示词（逐步变化）
[day:night:0.1]        # 从day渐变到night
```

**参数设置**：
```
Steps: 20-50（提示词步数）
Sampler: DPM++ 2M Karras 或 Euler a
CFG Scale: 7-12（提示词相关性）
Seed: -1（随机）或 固定数字
Size: 1024x1024 或 1024x1536（竖版）
```

#### Midjourney格式

**Midjourney参数**：
```
{prompt} --ar 16:9 --style raw --stylize 250 --chaos 10

--ar 16:9          # 宽高比
--style raw        # 原始风格，较少AI加工
--stylize 0-1000   # 风格化程度
--chaos 0-100      # 随机性/变化程度
--quality 1/2      # 质量（1=快，2=高）
--repeat 1-40      # 生成变体数量
```

### 3.6 提示词生成器

#### 完整Prompt构建

```python
def build_full_prompt(shot_info, style_config):
    """构建完整的图像生成提示词"""

    # ============ 正向提示词 ============
    positive_parts = []

    # 1. 质量词
    positive_parts.extend(style_config['quality_tags'])

    # 2. 主体（角色）
    if shot_info['characters']:
        char_prompts = []
        for char in shot_info['characters']:
            char_prompts.append(build_character_prompt(
                char,
                shot_info['action']
            ))
        positive_parts.append(", ".join(char_prompts))

    # 3. 环境
    positive_parts.append(build_environment_prompt(shot_info['scene']))

    # 4. 构图
    positive_parts.append(shot_info['composition']['type'])
    positive_parts.append(f"{shot_info['camera']['shot_size']} shot")

    # 5. 视角
    positive_parts.append(shot_info['camera']['angle'])

    # 6. 风格
    positive_parts.extend(style_config['art_style'])
    positive_parts.extend(style_config['render_style'])

    # 7. 光影
    positive_parts.append(shot_info['lighting']['type'])

    # 8. 技术词
    positive_parts.extend([
        "cinematic composition",
        "sharp focus",
        "detailed",
        "professional"
    ])

    # ============ 负面提示词 ============
    negative_parts = [
        "low quality",
        "worst quality",
        "blurry",
        "out of focus",
        "deformed",
        "disfigured",
        "bad anatomy",
        "extra limbs",
        "missing limbs",
        "nsfw",
        "nude",
        "watermark",
        "signature",
        "text",
        "logo",
        "border",
        "cropped"
    ]

    # ============ 组合 ============
    positive_prompt = ", ".join(positive_parts)
    negative_prompt = ", ".join(negative_parts)

    return {
        "positive": positive_prompt,
        "negative": negative_prompt,
        "params": {
            "steps": 30,
            "sampler": "DPM++ 2M Karras",
            "cfg_scale": 7.5,
            "seed": -1
        }
    }
```

---

## 4. 提示词优化策略

### 4.1 自动优化

**优化检查项**：
```python
def optimize_prompt(prompt):
    """自动优化提示词"""

    issues = []
    optimizations = []

    # 检查长度
    if len(prompt) < 50:
        issues.append("提示词过短")
        optimizations.append("增加细节描述")

    if len(prompt) > 500:
        issues.append("提示词过长")
        optimizations.append("精简描述，保留关键要素")

    # 检查冲突
    if has_conflicting_terms(prompt):
        issues.append("存在冲突描述")
        optimizations.append("移除冲突词汇")

    # 检查质量词
    if not has_quality_tags(prompt):
        issues.append("缺少质量词")
        optimizations.append("添加质量提升词")

    # 检查主体清晰度
    if not has_clear_subject(prompt):
        issues.append("主体不明确")
        optimizations.append("明确主体描述")

    return {
        "issues": issues,
        "optimizations": optimizations,
        "optimized_prompt": apply_optimizations(prompt, optimizations)
    }
```

### 4.2 提示词A/B测试

**多版本生成**：
```python
def generate_prompt_variations(base_prompt):
    """生成多个提示词变体用于对比"""

    variations = []

    # 原版
    variations.append({
        "version": "original",
        "prompt": base_prompt
    })

    # 强调风格版
    style_emphasized = base_prompt.copy()
    style_emphasized['style'].extend([
        "highly stylized",
        "artistic"
    ])
    variations.append({
        "version": "style_emphasized",
        "prompt": style_emphasized
    })

    # 强调细节版
    detail_emphasized = base_prompt.copy()
    detail_emphasized['quality'].extend([
        "ultra detailed",
        "intricate"
    ])
    variations.append({
        "version": "detail_emphasized",
        "prompt": detail_emphasized
    })

    # 简洁版
    simplified = base_prompt.copy()
    simplified['style'] = [s for s in simplified['style'] if 'basic' in s or 'simple' in s]
    variations.append({
        "version": "simplified",
        "prompt": simplified
    })

    return variations
```

---

## 5. 输出格式

### 5.1 图像生成任务格式

```json
{
  "generation_task": {
    "task_id": "gen_task_001",
    "shot_id": "shot_001",
    "priority": 1,

    "prompts": {
      "positive": "masterpiece, best quality, highly detailed, a 16 year old anime boy with short messy black hair and amber eyes, standing alone in rain, wearing black school uniform, melancholic expression, rainy city street at night, streetlights reflecting on wet pavement, eye level shot, rule of thirds, anime style, cel shading, cool color tone, soft lighting, cinematic lighting, sharp focus",
      "negative": "low quality, worst quality, blurry, out of focus, deformed, disfigured, bad anatomy, extra limbs, missing limbs, nsfw, nude, watermark, signature, text, logo, border"
    },

    "parameters": {
      "width": 1024,
      "height": 1536,
      "steps": 30,
      "sampler": "DPM++ 2M Karras",
      "cfg_scale": 7.5,
      "seed": -1
    },

    "controls": {
      "use_character_lora": true,
      "lora_path": "models/loras/character_amemiya.safetensors",
      "lora_weight": 0.8,

      "use_controlnet": false,
      "controlnet_type": null,

      "use_ip_adapter": true,
      "reference_image": "references/char_001_front.png",
      "ip_adapter_weight": 0.6
    },

    "post_processing": [
      "upscale",
      "enhance_face",
      "add_speech_bubble_area"
    ],

    "quality_control": {
      "min_aesthetic_score": 6.0,
      "generate_variants": 4,
      "auto_select_best": true
    }
  }
}
```

---

*文档版本：1.0*
*所属阶段：阶段3 - 画面描述生成*
*最后更新：2026-02-02*
