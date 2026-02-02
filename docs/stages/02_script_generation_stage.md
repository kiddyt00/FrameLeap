# 阶段2：剧本生成阶段详细说明

## 1. 概述

剧本生成阶段是整个动态漫创作的核心环节，负责将用户的原始输入（一句话/短文）扩展为结构化的完整剧本。本阶段完全由AI语言模型驱动，生成角色设定、分镜脚本、对白台词等所有内容。

---

## 2. 故事分析与规划

### 2.1 输入理解模块

#### 核心信息提取

**提取要素**：

| 要素类型 | 说明 | 示例 |
|---------|------|------|
| 主题 | 故事的核心主题 | 成长、救赎、友情、复仇 |
| 类型 | 故事类型分类 | 冒险、恋爱、悬疑、恐怖 |
| 设定 | 故事世界观 | 现代、奇幻、科幻、历史 |
| 角色 | 识别或推断角色 | 少年、神秘少女 |
| 冲突 | 故事矛盾点 | 命运的抉择、力量的代价 |
| 情感 | 情感基调 | 温馨、悲伤、热血 |

**提取流程**：
```
输入文本 → 分词 → 实体识别 → 情感分析 → 主题分类 → 要素结构化
```

#### 故事结构分析

**经典故事结构**：

**三幕式结构**：
```
第一幕：铺垫（约占25%）
  - 建立世界观
  - 介绍主角
  - 激发事件

第二幕：发展（约占50%）
  - 角色成长
  - 试炼与挑战
  - 中点转折

第三幕：高潮与结局（约占25%）
  - 最终对决
  - 角色蜕变
  - 结局收尾
```

**英雄之旅结构**：
```
1. 平凡世界
2. 冒险召唤
3. 拒绝召唤
4. 遇见导师
5. 跨越第一道门槛
6. 试炼、盟友、敌人
7. 接近洞穴
8. 磨难
9. 奖赏
10. 返回之路
11. 复活
12. 满载而归
```

**短篇结构**（适用于短视频）：
```
起（5%）→ 承（25%）→ 转（50%）→ 合（20%）
```

### 2.2 剧本结构规划

#### 章节规划

**章节自动分配算法**：

```python
# 伪代码
def plan_scenes(input_length, target_duration):
    # 根据输入长度估算镜头数量
    estimated_shots = input_length // 50  # 每50字约1个镜头

    # 根据目标时长调整
    if target_duration < 120:  # 2分钟以内
        shots_per_minute = 8
    elif target_duration < 300:  # 5分钟以内
        shots_per_minute = 6
    else:
        shots_per_minute = 4

    total_shots = int(target_duration / 60 * shots_per_minute)

    # 分配章节
    if total_shots <= 10:
        scenes = ["开场", "发展", "高潮", "结局"]
    elif total_shots <= 20:
        scenes = ["开场", "发展1", "发展2", "高潮", "结局"]
    else:
        scenes = generate_detailed_scenes(estimated_shots)

    return scenes, total_shots
```

#### 节奏规划

**节奏曲线设计**：

```
紧张度
  ↑
高│     ╱╲    ╱━━━━╲    ╱━━━━━━╲
  │    ╱  ╲  ╱      ╲  ╱        ╲
中│   ╱    ╲╱        ╲╱          ╲
  │  ╱                          ╲╲
低│ ╱                            ╲╲___
  └────────────────────────────────────→ 时间
    开场    铺垫    冲突    高潮    结局
```

**节奏控制参数**：

| 阶段 | 镜头数量 | 平均时长 | 运镜速度 | 转场频率 |
|-----|---------|---------|---------|---------|
| 开场 | 少 | 中等 | 缓慢 | 低 |
| 铺垫 | 中等 | 中等 | 中等 | 中 |
| 冲突 | 多 | 短 | 快速 | 高 |
| 高潮 | 最多 | 最短 | 最快 | 最高 |
| 结局 | 少 | 长 | 缓慢 | 低 |

---

## 3. 剧本/脚本生成

### 3.1 详细剧本生成

#### 剧本模板

**标准剧本格式**：
```json
{
  "script_id": "script_001",
  "title": "雨夜的邂逅",
  "total_duration": 180,
  "summary": "一个孤独的少年在雨夜中遇到了改变命运的少女",
  "scenes": [
    {
      "scene_id": "scene_001",
      "scene_number": 1,
      "title": "雨夜街道",
      "location": "城市街道",
      "time": "夜晚",
      "weather": "大雨",
      "atmosphere": "孤独、忧郁",
      "duration": 15,
      "characters": ["少年"],
      "shots": [
        {
          "shot_id": "shot_001",
          "shot_number": 1,
          "shot_size": "远全景",
          "camera_movement": "缓慢推近",
          "description": "雨夜中的空旷街道，路灯昏暗，雨水如帘",
          "visual_notes": "冷色调，光影对比强烈",
          "audio": {
            "music": "忧伤钢琴曲，音量渐入",
            "sound_effects": ["雨声", "远处雷声"],
            "narration": null
          },
          "duration": 5
        },
        {
          "shot_id": "shot_002",
          "shot_number": 2,
          "shot_size": "中景",
          "camera_movement": "固定",
          "description": "少年独自走在雨中，没有打伞",
          "visual_notes": "少年全身湿透，表情麻木",
          "audio": {
            "music": "继续，音量保持",
            "sound_effects": ["雨声", "脚步声"],
            "dialogue": {
              "speaker": "少年（内心独白）",
              "line": "又是一个人的雨夜...",
              "emotion": "孤独、无奈"
            }
          },
          "duration": 4
        }
      ]
    }
  ],
  "characters": {
    "少年": {
      "name": "雨宫",
      "age": 16,
      "role": "主角",
      "personality": "孤独、敏感、善良"
    }
  }
}
```

#### 剧本生成Prompt模板

```markdown
# 角色设定
你是一位专业的动画编剧，擅长创作富有感染力的动态漫剧本。

# 任务
根据以下用户输入，创作一个完整的动态漫剧本。

# 用户输入
{user_input}

# 生成要求
1. 扩展为完整的剧本结构，包含开场、发展、高潮、结局
2. 每个场景需要详细描述：
   - 场景标题
   - 时间地点
   - 氛围描述
   - 角色动作和表情
   - 对话内容
   - 镜头建议
3. 总时长控制在 {target_duration} 秒
4. 风格：{style_preference}
5. 情感基调：{emotional_tone}

# 输出格式
请以JSON格式输出剧本，包含以下字段：
- title: 剧本标题
- summary: 故事简介
- scenes: 场景数组
- characters: 角色字典
- total_estimated_duration: 预计总时长
```

### 3.2 分镜脚本生成

#### 分镜拆分规则

**自动拆分算法**：

```python
def split_into_shots(scene_description):
    shots = []

    # 识别对话切换点
    dialogue_changes = find_dialogue_changes(scene_description)

    # 识别动作变化点
    action_changes = find_action_changes(scene_description)

    # 识别场景变化点
    location_changes = find_location_changes(scene_description)

    # 合并所有切换点并排序
    split_points = merge_and_sort([
        dialogue_changes,
        action_changes,
        location_changes
    ])

    # 生成镜头
    for i, point in enumerate(split_points):
        shot = {
            "shot_number": i + 1,
            "content": extract_content(scene_description, point),
            "shot_size": determine_shot_size(point),  # 自动推断景别
            "camera_movement": suggest_camera_movement(point),
            "duration": estimate_duration(point)
        }
        shots.append(shot)

    return shots
```

#### 景别自动选择

**景别选择规则**：

| 情况 | 推荐景别 | 理由 |
|-----|---------|------|
| 场景介绍/环境交代 | 远景/大远景 | 展示环境全貌 |
| 角色首次出场 | 全景/中景 | 展示全身造型 |
| 两人对话 | 中景/中近景 | 展示互动关系 |
| 情感表达 | 近景/特写 | 强调表情细节 |
| 某个细节/物品 | 特写/大特写 | 突出重要性 |
| 动作场景 | 中景跟随 | 保持动作连贯 |

### 3.3 台词与对白生成

#### 角色声音建模

**声音特征定义**：
```json
{
  "character_id": "char_001",
  "name": "雨宫",
  "voice_profile": {
    "age_range": "15-17岁",
    "gender": "男",
    "tone": "低沉、略带沙哑",
    "speaking_style": "简练、带有停顿",
    "vocabulary": "简单、直接",
    "catchphrase": ["...", "无所谓"],
    "emotional_range": {
      "neutral": "平静、冷淡",
      "happy": "轻微微笑",
      "sad": "沉默、低头",
      "angry": "皱眉、语速加快"
    }
  }
}
```

#### 对话生成策略

**对话生成考虑因素**：

1. **角色一致性**：每句台词符合角色性格
2. **情境适配**：对话符合当前场景
3. **推进剧情**：对话服务于故事发展
4. **自然流畅**：避免生硬和不自然的表达
5. **节奏控制**：对话长度与镜头时长匹配

**对话优化Prompt**：
```markdown
# 对话优化任务
优化以下对话，使其更自然、更符合角色性格。

# 当前对话
角色A：你好，请问你是谁？
角色B：我是新来的学生。

# 角色信息
角色A：活泼开朗的中学生，说话带点俏皮
角色B：神秘转校生，话少，给人一种距离感

# 优化要求
1. 保持原意
2. 符合角色性格
3. 加入语气词和停顿
4. 添加动作/表情描述

# 优化后的对话
角色A：（好奇地凑近）喂，你是新来的？以前没见过你呢。
角色B：（稍微侧身，避开目光）...转校生。

角色A：（不依不饶）转校生？哪个班的？
角色B：（沉默片刻，低声）...和你无关。
```

---

## 4. 角色设定生成

### 4.1 角色档案创建

#### 自动角色提取

**提取流程**：
```
剧本文本 → 命名实体识别 → 角色候选提取 → 重要性评分 → 主要角色确定
```

**角色重要性评分**：
```python
def calculate_character_importance(character, script):
    score = 0

    # 出场次数
    score += character.appearances * 10

    # 对话数量
    score += character.dialogue_count * 5

    # 关键情节参与度
    score += character.plot_involvement * 20

    # 与主角关系
    if character.is_protagonist:
        score += 100
    elif character.is_antagonist:
        score += 80
    elif character.is_mentor:
        score += 60

    return score
```

#### 角色档案模板

**完整角色设定**：
```json
{
  "character_id": "char_001",
  "name": "雨宫",
  "name_en": "Amemiya",
  "age": 16,
  "gender": "男",
  "role": "主角",
  "archetype": "孤独的少年",

  "appearance": {
    "height": "170cm",
    "build": "修长、略显单薄",
    "hair": {
      "color": "黑发",
      "style": "短发、略带凌乱",
      "features": "刘海遮住一边眼睛"
    },
    "eyes": {
      "color": "琥珀色",
      "shape": "狭长",
      "expression": "总是看起来很困倦"
    },
    "face": {
      "shape": "清秀",
      "skin": "苍白",
      "features": ["薄唇", "有淡淡黑眼圈"]
    },
    "outfit": {
      "default": "黑色立领校服，红色领结略微歪斜",
      "alternatives": ["简单的休闲装", "雨衣"]
    }
  },

  "personality": {
    "keywords": ["孤独", "敏感", "善良", "内向"],
    "traits": {
      "positive": ["善良", "观察力敏锐", "守承诺"],
      "negative": ["不善表达", "容易钻牛角尖", "自我封闭"],
      "quirks": ["习惯用手遮住脸", "说话时会停顿"]
    },
    "background": "父母离异后独自生活，习惯独来独往",
    "motivation": "渴望理解但又害怕被伤害",
    "fear": "建立关系后的失去"
  },

  "expressions": {
    "neutral": "面无表情，眼神放空",
    "happy": "嘴角微微上扬，很浅的笑",
    "sad": "低头，刘海遮住眼睛",
    "surprised": "稍微睁大眼睛",
    "angry": "皱眉，握紧拳头",
    "embarrassed": "看向别处，耳朵微红"
  },

  "voice_profile": {
    "age_range": "15-17岁",
    "tone": "低沉、略带沙哑",
    "speaking_style": "简练、带有停顿",
    "tts_voice_id": "teen_male_low_pitch_001"
  },

  "visual_reference": {
    "style_prompts": [
      "anime style male character, 16 years old",
      "black messy short hair, amber eyes",
      "pale skin, thin build",
      "black school uniform with red tie",
      "melancholic expression, looking down",
      "soft lighting, cool color tone"
    ],
    "negative_prompts": [
      "smiling, bright eyes, muscular, colorful"
    ]
  }
}
```

### 4.2 角色一致性确保

#### 角色Embedding生成

**流程**：
```
角色描述 → 生成参考图 → 训练Embedding → 验证一致性 → 应用
```

**生成参考图序列**：
```json
{
  "reference_shots": [
    {
      "type": "front_view",
      "description": "正面肖像，中性表情",
      "prompt": "front view portrait of {character_name}, {appearance_details}, neutral expression, anime style, simple background"
    },
    {
      "type": "side_view",
      "description": "侧面肖像",
      "prompt": "side view portrait of {character_name}, {appearance_details}, anime style, simple background"
    },
    {
      "type": "three_quarter",
      "description": "四分之三侧脸",
      "prompt": "three quarter view of {character_name}, {appearance_details}, anime style, simple background"
    },
    {
      "type": "full_body",
      "description": "全身立姿",
      "prompt": "full body shot of {character_name}, {appearance_details}, standing pose, anime style, simple background"
    },
    {
      "type": "expression_set",
      "description": "表情变化",
      "expressions": ["happy", "sad", "angry", "surprised"]
    }
  ]
}
```

#### LoRA训练流程

**训练参数**：
```python
lora_training_config = {
    "model": "Stable Diffusion XL",
    "training_images": 20,  # 每个角色20-30张参考图
    "resolution": 1024,
    "steps": 1000,
    "learning_rate": 0.0001,
    "network_dim": 32,
    "network_alpha": 16,
    "trigger_word": f"char_{character_name}",
    "output_dir": f"models/loras/{character_name}"
}
```

**一致性验证**：
```python
def verify_character_consistency(generated_images, reference_images):
    # 使用CLIP模型计算相似度
    similarities = []
    for gen_img in generated_images:
        for ref_img in reference_images:
            sim = clip_similarity(gen_img, ref_img)
            similarities.append(sim)

    avg_similarity = np.mean(similarities)

    # 相似度阈值
    if avg_similarity > 0.85:
        return "excellent"
    elif avg_similarity > 0.75:
        return "good"
    else:
        return "needs_improvement"
```

---

## 5. 输出数据结构

### 5.1 完整剧本输出

**剧本JSON结构**：
```json
{
  "script": {
    "meta": {
      "script_id": "script_20250202_001",
      "version": "1.0",
      "created_at": "2025-02-02T10:35:00Z",
      "user_input": "一个少年在雨夜中遇到了神秘少女",
      "target_duration": 180
    },
    "story_info": {
      "title": "雨夜的邂逅",
      "genre": ["青春", "奇幻"],
      "themes": ["孤独", "命运", "相遇"],
      "logline": "一个孤独的少年在雨夜中遇到了改变命运的少女，从此踏入了不为人知的世界",
      "summary": "详细的故事简介..."
    },
    "structure": {
      "act_1_setup": {
        "scenes": [1, 2],
        "duration": 45,
        "purpose": "建立少年孤独的生活状态"
      },
      "act_2_confrontation": {
        "scenes": [3, 4, 5],
        "duration": 90,
        "purpose": "少年遇到少女，世界观被打破"
      },
      "act_3_resolution": {
        "scenes": [6],
        "duration": 45,
        "purpose": "少年做出选择，新的开始"
      }
    },
    "characters": {
      /* 角色档案 */
    },
    "scenes": [
      /* 场景数组 */
    ]
  }
}
```

### 5.2 分镜序列输出

**分镜列表格式**：
```json
{
  "storyboard_sequence": [
    {
      "shot_id": "shot_001",
      "scene_number": 1,
      "shot_number": 1,
      "shot_size": "远全景",
      "camera": {
        "movement": "缓慢推近",
        "speed": "slow",
        "start_position": "wide",
        "end_position": "medium_wide"
      },
      "content": {
        "visual": "雨夜中的空旷街道，路灯昏暗",
        "characters": [],
        "action": "雨水如帘落下，远处有雷声",
        "atmosphere": "孤独、忧郁"
      },
      "technical": {
        "composition": "三分法，街道延伸线",
        "lighting": "路灯暖光与冷色调雨景对比",
        "color_palette": ["深蓝", "暖黄", "灰色"],
        "depth_of_field": "深景深，前后都清晰"
      },
      "audio": {
        "music": "忧伤钢琴曲渐入",
        "sfx": ["雨声", "远处雷声"],
        "dialogue": null
      },
      "duration": 5.0,
      "transition": {
        "type": "cut",
        "duration": 0.5
      },
      "prompt_ready": true
    }
  ]
}
```

---

## 6. 质量控制

### 6.1 剧本质量检查

**检查项**：
```python
def validate_script(script):
    checks = {
        "structure_complete": False,
        "character_consistency": False,
        "dialogue_natural": False,
        "pacing_appropriate": False,
        "duration_match": False
    }

    # 结构完整性
    if has_all_acts(script) and has_proper_ending(script):
        checks["structure_complete"] = True

    # 角色一致性
    if check_character_personality_consistency(script):
        checks["character_consistency"] = True

    # 对话自然度
    if check_dialogue_naturalness(script):
        checks["dialogue_natural"] = True

    # 节奏合理性
    if check_pacing(script):
        checks["pacing_appropriate"] = True

    # 时长匹配
    if estimate_duration(script) == target_duration:
        checks["duration_match"] = True

    return checks
```

### 6.2 剧本评分标准

| 维度 | 权重 | 评分标准 |
|-----|------|---------|
| 故事完整性 | 30% | 起承转合完整，逻辑自洽 |
| 角色塑造 | 25% | 角色鲜明，行为一致 |
| 对话质量 | 20% | 自然流畅，符合角色 |
| 节奏控制 | 15% | 张弛有度，不拖沓 |
| 视觉化程度 | 10% | 描述具体，易于转化 |

---

## 7. 优化与迭代

### 7.1 自动优化

**优化方向**：
1. **节奏优化**：调整镜头数量和时长
2. **对话优化**：使对话更自然
3. **描述优化**：增加视觉描述细节
4. **情感优化**：强化情感表达

### 7.2 用户反馈整合

**反馈类型**：
- 剧本太长/太短 → 调整内容密度
- 角色不讨喜 → 调整角色设定
- 对话不自然 → 重新生成对话
- 某部分不满意 → 针对性修改

---

*文档版本：1.0*
*所属阶段：阶段2 - 剧本生成*
*最后更新：2026-02-02*
