# 阶段5：分镜编排阶段详细说明

## 1. 概述

分镜编排阶段负责将生成的图像按照剧本和视觉叙事规则组织成完整的镜头序列。本阶段确定每个镜头的时长、顺序、转场方式，确保整体节奏和叙事流畅性。

---

## 2. 镜头序列规划

### 2.1 时间轴编排

#### 镜头时长计算

**基于内容的时长计算**：
```python
def calculate_shot_duration(shot_info):
    """计算镜头时长"""

    base_duration = 3.0  # 基础时长3秒

    # 1. 根据对话长度调整
    if shot_info.get('dialogue'):
        word_count = len(shot_info['dialogue'].split())
        dialogue_duration = word_count * 0.4  # 每词0.4秒
        dialogue_duration += 1.0  # 停顿时间
        base_duration = max(base_duration, dialogue_duration)

    # 2. 根据景别调整
    shot_size_multiplier = {
        "大特写": 0.7,
        "特写": 1.0,
        "近景": 1.2,
        "中景": 1.5,
        "全景": 2.0,
        "远全景": 2.5
    }
    multiplier = shot_size_multiplier.get(shot_info['shot_size'], 1.0)
    base_duration *= multiplier

    # 3. 根据内容复杂度调整
    if shot_info.get('complex_action'):
        base_duration *= 1.3

    # 4. 情感镜头延长
    if shot_info.get('emotional_intensity', 0) > 0.7:
        base_duration *= 1.2

    # 5. 限制范围
    duration = max(1.5, min(base_duration, 10.0))

    return duration
```

**时长类型规划**：

| 镜头类型 | 时长范围 | 说明 |
|---------|---------|------|
| 快速反应 | 0.5-1秒 | 惊讶、快速切换 |
| 短镜头 | 1-2秒 | 动作场景、快速剪辑 |
| 标准镜头 | 3-5秒 | 大多数对话和场景 |
| 长镜头 | 5-8秒 | 情感表达、环境展示 |
| 超长镜头 | 8秒以上 | 特殊强调、慢镜头 |

#### 时间轴构建

```python
def build_timeline(shots):
    """构建时间轴"""

    timeline = []
    current_time = 0.0

    for shot in shots:
        duration = calculate_shot_duration(shot)

        timeline_entry = {
            "shot_id": shot['shot_id'],
            "start_time": current_time,
            "end_time": current_time + duration,
            "duration": duration,
            "shot": shot
        }

        timeline.append(timeline_entry)
        current_time += duration

    return timeline
```

**时间轴数据结构**：
```json
{
  "timeline": {
    "total_duration": 180.5,
    "shots": [
      {
        "shot_id": "shot_001",
        "time_range": {
          "start": 0.0,
          "end": 4.5,
          "duration": 4.5
        },
        "layer": "video_main"
      },
      {
        "shot_id": "shot_002",
        "time_range": {
          "start": 4.5,
          "end": 9.0,
          "duration": 4.5
        },
        "transition": {
          "type": "fade",
          "duration": 0.5,
          "start_offset": 4.0
        },
        "layer": "video_main"
      }
    ]
  }
}
```

### 2.2 镜头类型分配

#### 建立镜头（Establishing Shot）

**用途与特征**：
```json
{
  "shot_type": "establishing",
  "purpose": "交代环境、场景定位",
  "typical_duration": "4-8秒",
  "shot_sizes": ["全景", "远全景"],
  "camera_movement": ["缓慢推近", "缓慢横移", "固定"],
  "position_in_scene": "first_shot",
  "examples": [
    "城市远景展示故事发生的地点",
    "学校外观建立校园场景",
    "室内全景展示房间布局"
  ]
}
```

**生成规则**：
```python
def is_establishing_shot_needed(scene_info, previous_scene):
    """判断是否需要建立镜头"""

    # 场景切换时需要
    if previous_scene and scene_info['location'] != previous_scene['location']:
        return True

    # 时间跨度大时需要
    if scene_info.get('time_jump', False):
        return True

    # 场景开始位置
    if scene_info.get('is_first_scene_of_act', False):
        return True

    return False
```

#### 对话镜头（Dialogue Shot）

**对话镜头编排模式**：

| 模式 | 描述 | 镜头安排 |
|-----|------|---------|
| 单人镜头 | 每个角色单独拍摄 | A说话→A镜头，B说话→B镜头 |
| 过肩镜头 | 经典对话方式 | A说话→越过B看A |
| 双人镜头 | 两人同框 | 中景展示两人互动 |
| 反应镜头 | 展示听者反应 | A说话→B的反应特写 |

**对话镜头生成逻辑**：
```python
def plan_dialogue_shots(dialogue_sequence):
    """规划对话镜头序列"""

    shots = []

    for line in dialogue_sequence:
        speaker = line['speaker']

        # 说话者镜头
        shots.append({
            "type": "dialogue",
            "focus": speaker,
            "shot_size": "近景" if line.get('emotional') else "中景",
            "duration": calculate_dialogue_duration(line['text']),
            "dialogue": line
        })

        # 如果是重要对话，添加听者反应
        if line.get('important', False):
            shots.append({
                "type": "reaction",
                "focus": get_listener(dialogue_sequence, speaker),
                "shot_size": "特写",
                "duration": 1.5,
                "purpose": "reaction_to_dialogue"
            })

    return shots
```

#### 情绪特写（Emotional Close-up）

**特写使用规则**：
```python
def should_use_close_up(shot_info):
    """判断是否应该使用特写"""

    triggers = [
        shot_info.get('emotional_intensity', 0) > 0.7,
        shot_info.get('revelation', False),
        shot_info.get('character_realization', False),
        shot_info.get('intense_emotion', False),
        '眼泪' in shot_info.get('description', ''),
        '微笑' in shot_info.get('description', '')
    ]

    return any(triggers)
```

**特写类型**：
```json
{
  "close_up_types": {
    "face": {
      "frame": "额头到下巴",
      "purpose": "展示面部表情细节",
      "emotion_keywords": ["悲伤", "喜悦", "愤怒", "惊讶"]
    },
    "eyes": {
      "frame": "眼部区域",
      "purpose": "强调眼神情感",
      "emotion_keywords": ["坚定", "含泪", "震惊"]
    },
    "mouth": {
      "frame": "嘴部区域",
      "purpose": "强调台词或微小表情",
      "use_case": "重要对话、微笑、咬唇"
    },
    "detail": {
      "frame": "特定细节",
      "purpose": "强调物品或手势",
      "examples": ["握紧的手", "飘落的花瓣", "破碎的物品"]
    }
  }
}
```

#### 动作镜头（Action Shot）

**动作镜头编排**：
```python
def plan_action_shots(action_description):
    """规划动作镜头序列"""

    shots = []

    # 1. 动作前准备
    shots.append({
        "type": "anticipation",
        "duration": 1.0,
        "shot_size": "中景",
        "description": "角色准备动作的姿势"
    })

    # 2. 动作进行中（多角度）
    shots.extend([
        {
            "type": "action_main",
            "shot_size": "全景",
            "duration": 2.0,
            "camera": "跟随动作"
        },
        {
            "type": "action_detail",
            "shot_size": "近景",
            "duration": 0.8,
            "description": "动作关键帧"
        }
    ])

    # 3. 动作结果/冲击
    shots.append({
        "type": "impact",
        "shot_size": "中景",
        "duration": 1.5,
        "description": "动作完成后的状态"
    })

    return shots
```

### 2.3 镜头顺序优化

#### 视觉连贯性检查

```python
def check_visual_continuity(shot_a, shot_b):
    """检查两个镜头之间的视觉连贯性"""

    issues = []

    # 1. 检查180度规则
    if violates_180_rule(shot_a, shot_b):
        issues.append("180度规则违反")

    # 2. 检查视线方向
    if eye_direction_mismatch(shot_a, shot_b):
        issues.append("视线方向不匹配")

    # 3. 检查空间关系
    if spatial_relationship_confused(shot_a, shot_b):
        issues.append("空间关系混乱")

    # 4. 检查色彩跳跃
    if color_jump_too_abrupt(shot_a, shot_b):
        issues.append("色彩跳跃明显")

    return {
        "continuous": len(issues) == 0,
        "issues": issues
    }
```

#### 自动镜头重排

```python
def optimize_shot_order(shots):
    """优化镜头顺序"""

    # 使用旅行商问题算法寻找最优顺序
    # 目标：最小化视觉跳跃，最大化叙事连贯性

    similarity_matrix = calculate_shot_similarity_matrix(shots)

    optimal_order = solve_tsp(
        shots,
        distance_matrix=similarity_matrix,
        constraints=[narrative_order_constraint]
    )

    return optimal_order
```

---

## 3. 节奏控制

### 3.1 整体节奏规划

#### 节奏曲线生成

```python
def generate_pacing_curve(story_structure):
    """生成节奏曲线"""

    curve = []

    # 分析每个段落的紧张度
    for section in story_structure:
        tension = calculate_section_tension(section)

        # 根据紧张度确定剪辑速度
        if tension > 0.8:
            # 高紧张度 → 快速剪辑
            pace = "fast"
            avg_shot_duration = 2.0
        elif tension > 0.5:
            # 中等紧张度 → 正常剪辑
            pace = "normal"
            avg_shot_duration = 3.5
        else:
            # 低紧张度 → 慢速剪辑
            pace = "slow"
            avg_shot_duration = 5.0

        curve.append({
            "section": section['name'],
            "tension": tension,
            "pace": pace,
            "avg_duration": avg_shot_duration
        })

    return curve
```

**节奏曲线示例**：
```
紧张度    高潮
          ↑
  高│         ╱━━━━━━━━╲
    │        ╱          ╲
  中│   ╱╲  ╱            ╲
    │  ╱  ╲╱              ╲╲
  低│ ╱                      ╲╱___
    │
    └────────────────────────────────→ 时间
      开场  铺垫  冲突升级  高潮  结局
      慢    中    快       最快  慢
```

### 3.2 段落节奏调整

#### 快节奏段落

**特征与技巧**：
```json
{
  "fast_pacing": {
    "characteristics": {
      "shot_duration": "1-2秒",
      "transition_frequency": "高",
      "camera_movement": "快速、动感",
      "music_tempo": "快"
    },
    "techniques": [
      "短镜头快速切换",
      "动作匹配剪辑",
      "快速推拉镜头",
      "手持镜头晃动感"
    ],
    "use_cases": [
      "动作场景",
      "追逐戏",
      "冲突高潮",
      "紧张时刻"
    ]
  }
}
```

#### 慢节奏段落

**特征与技巧**：
```json
{
  "slow_pacing": {
    "characteristics": {
      "shot_duration": "5-8秒",
      "transition_frequency": "低",
      "camera_movement": "缓慢、平滑",
      "music_tempo": "慢"
    },
    "techniques": [
      "长镜头停留",
      "缓慢推近/拉远",
      "固定镜头",
      "横摇扫描"
    ],
    "use_cases": [
      "情感表达",
      "环境展示",
      "沉思时刻",
      "浪漫场景"
    ]
  }
}
```

### 3.3 高潮处理

#### 高潮镜头密度

```python
def plan_climax_sequence(climax_section):
    """规划高潮段落的镜头密度"""

    shots = []

    # 逐渐增加镜头数量
    buildup_duration = climax_section['buildup_duration']
    climax_duration = climax_section['climax_duration']
    resolution_duration = climax_section['resolution_duration']

    # 1. 铺垫阶段 - 镜头逐渐变短
    buildup_shots = generate_shots_with_increasing_density(
        duration=buildup_duration,
        start_duration=4.0,
        end_duration=2.0
    )

    # 2. 高潮阶段 - 最密集
    climax_shots = generate_rapid_shots(
        duration=climax_duration,
        avg_duration=1.5
    )

    # 3. 解决阶段 - 逐渐放慢
    resolution_shots = generate_shots_with_decreasing_density(
        duration=resolution_duration,
        start_duration=2.0,
        end_duration=5.0
    )

    shots = buildup_shots + climax_shots + resolution_shots

    return shots
```

**高潮节奏示意图**：
```
镜头时长
  ↑
  │    ╲
  │     ╲
  │      ╲╱╲    ╱━━━━╲
  │         ╲  ╱      ╲
  │          ╲╱        ╲___
  │
  └─────────────────────────→ 时间
    铺垫    高潮      解决
```

---

## 4. 转场设计

### 4.1 转场类型

#### 基础转场

| 转场类型 | 持续时间 | 使用场景 | 效果 |
|---------|---------|---------|------|
| 切换（Cut） | 0秒 | 动作连贯、快速剪辑 | 直接、干脆 |
| 淡入淡出（Fade） | 0.5-2秒 | 场景转换、时间流逝 | 柔和、过渡 |
| 擦除（Wipe） | 0.5-1秒 | 平行叙事、场景切换 | 清晰分隔 |
| 溶解（Dissolve） | 1-2秒 | 回忆、梦境 | 融合、模糊 |

#### 动态转场

```json
{
  "dynamic_transitions": {
    "zoom_transition": {
      "description": "通过缩放进行转场",
      "technique": "前一个镜头放大 → 画面纯色 → 从纯色缩小出下一个镜头",
      "duration": "1.5-2秒"
    },
    "spin_transition": {
      "description": "旋转转场",
      "technique": "前一个镜头旋转消失 → 后一个镜头旋转出现",
      "duration": "1秒"
    },
    "pan_transition": {
      "description": "通过快速平移转场",
      "technique": "快速横向移动到下一个场景",
      "duration": "0.5-1秒"
    }
  }
}
```

#### 漫画风格转场

```json
{
  "manga_transitions": {
    "panel_transition": {
      "description": "模拟漫画格子的转场",
      "effect": "出现漫画格边框 → 新镜头从格子中展开",
      "style": "日式漫画风格"
    },
    "speed_lines_transition": {
      "description": "速度线转场",
      "effect": "放射状速度线 → 切换到下一个镜头",
      "style": "动作场景"
    },
    "ink_splash_transition": {
      "description": "墨水溅开转场",
      "effect": "墨水溅开 → 形成下一个场景",
      "style": "艺术性转场"
    }
  }
}
```

### 4.2 转场时机

#### 自动转场选择

```python
def select_transition(shot_a, shot_b, context):
    """自动选择合适的转场"""

    # 1. 同场景连续镜头 → 直接切换
    if shot_a['scene_id'] == shot_b['scene_id']:
        return {"type": "cut", "duration": 0}

    # 2. 时间跳跃 → 淡入淡出
    if context.get('time_jump', False):
        return {"type": "fade", "duration": 1.5}

    # 3. 回忆/梦境 → 溶解
    if context.get('is_memory', False):
        return {"type": "dissolve", "duration": 2.0}

    # 4. 动作场景 → 快速切换
    if context.get('is_action', False):
        return {"type": "cut", "duration": 0}

    # 5. 默认 → 快速淡入淡出
    return {"type": "fade", "duration": 0.5}
```

---

## 5. 多轨道编排

### 5.1 视频轨道结构

```
轨道结构示例：

V1: 主视频轨道
    ├── [镜头1] ──── [镜头2] ──── [镜头3] ────
V2: 特效图层
    ├──      [特效A]      [特效B]
V3: 文字/对话气泡
    ├──  [气泡1]     [气泡2]     [气泡3]
V4: 覆盖层
    └──           [闪光效果]

A1: 对白轨道
    ├── [对白1] ──── [对白2] ────
A2: 音效轨道
    ├── [音效] [音效] [音效]
A3: BGM轨道
    └─────────── [背景音乐] ──────────
```

### 5.2 轨道同步

```python
def synchronize_tracks(video_timeline, audio_timeline):
    """同步视频和音频轨道"""

    synchronized = {
        "video_tracks": [],
        "audio_tracks": []
    }

    # 对齐对白时间轴
    for dialogue in audio_timeline['dialogue']:
        # 找到对应的视频镜头
        matching_shot = find_shot_at_time(
            video_timeline,
            dialogue['start_time']
        )

        if matching_shot:
            # 确保镜头时长足够覆盖对白
            if matching_shot['duration'] < dialogue['duration']:
                extend_shot_duration(matching_shot, dialogue['duration'])

    return synchronized
```

---

## 6. 输出格式

### 6.1 分镜表格式

```json
{
  "storyboard": {
    "project_id": "proj_001",
    "total_duration": 180.0,
    "total_shots": 45,
    "shots": [
      {
        "shot_number": 1,
        "scene_number": 1,
        "shot_id": "shot_001",
        "time_range": {
          "start": 0.0,
          "end": 4.5,
          "duration": 4.5
        },
        "visual": {
          "image_path": "generated/scene_01/shot_01.png",
          "shot_size": "远全景",
          "camera_movement": "缓慢推近",
          "camera_angle": "水平视角"
        },
        "audio": {
          "dialogue": null,
          "music": {
            "track": "melancholic_piano.mp3",
            "volume": 0.6,
            "fade_in": 1.0
          },
          "sfx": ["rain_heavy.wav", "thunder_distant.wav"]
        },
        "transition": {
          "to_next": {
            "type": "fade",
            "duration": 0.5
          }
        },
        "notes": "建立雨夜氛围"
      }
    ]
  }
}
```

### 6.2 时间轴EDL格式

```json
{
  "edl": {
    "format": "EDL",
    "version": "1.0",
    "events": [
      {
        "event_number": 1,
        "shot_id": "shot_001",
        "source": {
          "file": "scene_01_shot_01.png",
          "start": 0.0,
          "duration": 4.5
        },
        "timeline": {
          "start": 0.0,
          "duration": 4.5
        },
        "transition": {
          "type": "fade",
          "cut_point": 4.0,
          "duration": 0.5
        }
      }
    ]
  }
}
```

---

*文档版本：1.0*
*所属阶段：阶段5 - 分镜编排*
*最后更新：2026-02-02*
