# 阶段8：文字与字幕阶段详细说明

## 1. 概述

文字与字幕阶段负责为动态漫添加对话气泡和字幕，确保文字内容清晰可读且不破坏画面美感。本阶段处理文字排版、样式设计和位置布局。

---

## 2. 对话气泡生成

### 2.1 气泡样式设计

#### 气泡形状库

```json
{
  "bubble_shapes": {
    "round": {
      "name": "圆形气泡",
      "css_class": "bubble-round",
      "border_radius": "50%",
      "padding": "15px 20px",
      "best_for": ["轻松对话", "可爱角色"],
      "reading_direction": "both"
    },
    "rounded_rect": {
      "name": "圆角矩形",
      "css_class": "bubble-rounded-rect",
      "border_radius": "15px",
      "padding": "12px 18px",
      "best_for": ["标准对话", "大多数场景"],
      "reading_direction": "both"
    },
    "cloud": {
      "name": "云形气泡",
      "css_class": "bubble-cloud",
      "border_radius": "20px",
      "has_bumps": true,
      "padding": "15px 20px",
      "best_for": ["思考", "内心独白", "梦境"],
      "reading_direction": "both"
    },
    "shout": {
      "name": "爆发形气泡",
      "css_class": "bubble-shout",
      "shape": "starburst",
      "padding": "15px 25px",
      "best_for": ["大喊", "惊讶", "强调"],
      "reading_direction": "both"
    },
    "rectangular": {
      "name": "矩形气泡",
      "css_class": "bubble-rect",
      "border_radius": "3px",
      "padding": "10px 15px",
      "best_for": ["严肃对话", "旁白"],
      "reading_direction": "both"
    },
    "japanese_traditional": {
      "name": "日式传统",
      "css_class": "bubble-jp-traditional",
      "shape": "irregular",
      "padding": "12px 18px",
      "best_for": ["日式漫画风格"],
      "reading_direction": "right_to_left"
    }
  }
}
```

#### 气泡边框样式

```json
{
  "bubble_borders": {
    "solid": {
      "name": "实线边框",
      "style": "solid",
      "width": "2px",
      "color": "#000000"
    },
    "double": {
      "name": "双重线",
      "style": "double",
      "width": "3px",
      "inner_width": "1px",
      "color": "#000000"
    },
    "dashed": {
      "name": "虚线边框",
      "style": "dashed",
      "width": "2px",
      "pattern": "5px 3px",
      "color": "#000000"
    },
    "none": {
      "name": "无边框",
      "style": "none",
      "use_shadow": true
    },
    "thick_cartoon": {
      "name": "粗卡通线",
      "style": "solid",
      "width": "4px",
      "color": "#000000",
      "has_shadow": true
    }
  }
}
```

#### 气泡填充样式

```json
{
  "bubble_fills": {
    "white_solid": {
      "name": "纯白填充",
      "type": "solid",
      "color": "#FFFFFF",
      "opacity": 1.0
    },
    "white_semi": {
      "name": "半透明白",
      "type": "solid",
      "color": "#FFFFFF",
      "opacity": 0.85
    },
    "gradient_soft": {
      "name": "柔和渐变",
      "type": "linear_gradient",
      "colors": ["#FFFFFF", "#F5F5F5"],
      "direction": "top_to_bottom",
      "opacity": 0.95
    },
    "tint_color": {
      "name": "色彩染色",
      "type": "solid",
      "base_color": "#FFFFFF",
      "tint": "#E6F3FF",
      "opacity": 0.9,
      "best_for": ["浪漫场景", "回忆场景"]
    }
  }
}
```

### 2.2 气泡尾巴（指向）设计

```json
{
  "bubble_tails": {
    "none": {
      "name": "无尾巴",
      "use_case": ["旁白", "内心独白", "画外音"]
    },
    "simple_round": {
      "name": "简单圆尾",
      "shape": "rounded_triangle",
      "length": "medium",
      "width_ratio": 0.4
    },
    "pointer": {
      "name": "指针型",
      "shape": "pointer",
      "length": "long",
      "best_for": ["明确指向角色"]
    },
    "multiple": {
      "name": "多个小尾巴",
      "shape": "small_circles",
      "count": 3,
      "best_for": ["思考", "犹豫"]
    },
    "japanese_style": {
      "name": "日式风格尾巴",
      "shape": "irregular_extension",
      "best_for": ["传统日式漫画"]
    }
  }
}
```

### 2.3 气泡自动排版

#### 位置算法

```python
def calculate_bubble_position(frame, character_position, text_length, other_bubbles):
    """计算对话气泡位置"""

    width, height = frame.size

    # 基础位置选择
    if character_position['x'] < width * 0.3:
        # 角色在左侧 → 气泡放右侧
        base_position = "right"
    elif character_position['x'] > width * 0.7:
        # 角色在右侧 → 气泡放左侧
        base_position = "left"
    else:
        # 角色在中间 → 气泡放上方
        base_position = "top"

    # 计算气泡尺寸
    bubble_width = estimate_bubble_width(text_length)
    bubble_height = estimate_bubble_height(text_length)

    # 计算具体坐标
    if base_position == "top":
        x = width / 2 - bubble_width / 2
        y = character_position['y'] - character_position['height'] - bubble_height - 20
    elif base_position == "left":
        x = character_position['x'] - bubble_width - 20
        y = character_position['y'] - bubble_height / 2
    else:  # right
        x = character_position['x'] + character_position['width'] + 20
        y = character_position['y'] - bubble_height / 2

    # 碰撞检测与调整
    final_position = adjust_for_collisions(
        (x, y, bubble_width, bubble_height),
        other_bubbles,
        frame.size
    )

    return final_position
```

#### 碰撞检测

```python
def adjust_for_collisions(new_bubble, existing_bubbles, frame_size):
    """检测并调整气泡位置避免重叠"""

    x, y, width, height = new_bubble
    max_attempts = 10

    for attempt in range(max_attempts):
        collision = False

        for existing in existing_bubbles:
            if rectangles_overlap(new_bubble, existing):
                collision = True
                break

        if not collision:
            break

        # 有碰撞，尝试调整位置
        if attempt == 0:
            # 第一次尝试：向上移动
            y -= 30
        elif attempt == 1:
            # 第二次尝试：向下移动
            y += 60
        elif attempt == 2:
            # 第三次尝试：向左/右移动
            if x > frame_size[0] / 2:
                x -= 40
            else:
                x += 40
        else:
            # 后续尝试：缩小气泡
            width *= 0.9
            height *= 0.9

        # 边界检查
        x = max(10, min(x, frame_size[0] - width - 10))
        y = max(10, min(y, frame_size[1] - height - 10))

        new_bubble = (x, y, width, height)

    return new_bubble
```

### 2.4 多行排版

```python
def format_bubble_text(text, max_width, font, reading_direction="left_to_right"):
    """格式化气泡内文字为多行"""

    lines = []
    current_line = ""
    current_width = 0

    # 分词
    if reading_direction == "right_to_left":
        # 从右到左（日式）
        words = list(text)  # 每个字符单独处理
    else:
        # 从左到右
        import re
        words = re.findall(r'(\S+|\s+)', text)

    for word in words:
        word_width = get_text_width(word, font)

        if current_width + word_width <= max_width:
            current_line += word
            current_width += word_width
        else:
            if current_line:
                lines.append(current_line.strip())
            current_line = word
            current_width = word_width

    if current_line:
        lines.append(current_line.strip())

    return lines
```

---

## 3. 字幕生成

### 3.1 字幕内容提取

```python
def extract_subtitle_content(script):
    """从剧本提取字幕内容"""

    subtitles = []

    for scene in script['scenes']:
        for shot in scene['shots']:
            # 对话
            if shot.get('dialogue'):
                subtitles.append({
                    "type": "dialogue",
                    "text": shot['dialogue']['text'],
                    "speaker": shot['dialogue']['speaker'],
                    "start_time": shot['time_range']['start'],
                    "end_time": shot['time_range']['end'],
                    "emotion": shot['dialogue'].get('emotion', 'neutral')
                })

            # 旁白
            if shot.get('narration'):
                subtitles.append({
                    "type": "narration",
                    "text": shot['narration']['text'],
                    "start_time": shot['time_range']['start'],
                    "end_time": shot['time_range']['end']
                })

    return subtitles
```

### 3.2 时间轴同步

```python
def sync_subtitle_timing(subtitles, audio_duration):
    """同步字幕时间轴与音频"""

    synced = []

    for sub in subtitles:
        # 获取对应音频的实际时长
        audio_segment = get_audio_segment(sub['start_time'])

        if audio_segment:
            actual_duration = len(audio_segment) / sample_rate

            # 调整字幕时长
            sub['end_time'] = sub['start_time'] + actual_duration

            # 添加缓冲时间
            sub['display_start'] = sub['start_time'] - 0.1
            sub['display_end'] = sub['end_time'] + 0.2

        synced.append(sub)

    return synced
```

### 3.3 字幕样式

#### 字幕样式库

```json
{
  "subtitle_styles": {
    "standard": {
      "name": "标准样式",
      "font": {
        "family": "Arial, sans-serif",
        "size": 24,
        "weight": "normal",
        "style": "normal"
      },
      "color": "#FFFFFF",
      "background": {
        "type": "none"
      },
      "stroke": {
        "width": 2,
        "color": "#000000"
      },
      "shadow": {
        "enabled": true,
        "offset_x": 2,
        "offset_y": 2,
        "blur": 3,
        "color": "#000000"
      },
      "position": "bottom_center",
      "alignment": "center"
    },
    "anime_style": {
      "name": "动漫风格",
      "font": {
        "family": "Anime Ace, sans-serif",
        "size": 28,
        "weight": "bold",
        "style": "normal"
      },
      "color": "#FFFFFF",
      "background": {
        "type": "semi_transparent_black",
        "opacity": 0.7
      },
      "stroke": {
        "width": 3,
        "color": "#000000"
      },
      "shadow": {
        "enabled": false
      },
      "position": "bottom_center",
      "alignment": "center"
    },
    "minimal": {
      "name": "极简风格",
      "font": {
        "family": "Helvetica, sans-serif",
        "size": 22,
        "weight": "light",
        "style": "normal"
      },
      "color": "#FFFFFF",
      "background": {
        "type": "none"
      },
      "stroke": {
        "width": 1,
        "color": "#000000"
      },
      "shadow": {
        "enabled": false
      },
      "position": "bottom_center",
      "alignment": "center"
    },
    "speaker_colored": {
      "name": "角色彩色",
      "font": {
        "family": "Arial, sans-serif",
        "size": 24,
        "weight": "normal"
      },
      "colors_by_speaker": {
        "char_001": "#FFD700",
        "char_002": "#87CEEB",
        "narrator": "#FFFFFF"
      },
      "background": {
        "type": "semi_transparent_black",
        "opacity": 0.6
      },
      "stroke": {
        "width": 2,
        "color": "#000000"
      },
      "position": "bottom_center"
    }
  }
}
```

### 3.4 字幕位置

#### 位置选项

```json
{
  "subtitle_positions": {
    "bottom_center": {
      "name": "底部居中",
      "x": "center",
      "y": "bottom - 50px",
      "max_width": "80%",
      "safe_area": true
    },
    "top_center": {
      "name": "顶部居中",
      "x": "center",
      "y": "top + 50px",
      "max_width": "80%",
      "safe_area": true
    },
    "follow_character": {
      "name": "跟随角色",
      "x": "dynamic",
      "y": "character_top - 100px",
      "max_width": "40%",
      "safe_area": false
    },
    "speaker_label": {
      "name": "说话者标签",
      "x": "left + 100px",
      "y": "bottom - 80px",
      "max_width": "70%",
      "has_speaker_name": true
    }
  }
}
```

---

## 4. 特效文字

### 4.1 拟声词（音效字）

```json
{
  "sfx_text_styles": {
    "impact": {
      "name": "冲击文字",
      "font": {
        "family": "Impact, sans-serif",
        "weight": "bold",
        "style": "italic"
      },
      "size": "large",
      "color": "#FF0000",
      "stroke": {
        "width": 3,
        "color": "#FFFF00"
      },
      "transform": {
        "rotation": "random_-15_to_15",
        "skew": "slight"
      },
      "animation": {
        "type": "scale_in",
        "duration": 0.2
      }
    },
    "speed_lines": {
      "name": "速度线文字",
      "font": {
        "family": "custom_comic_font",
        "weight": "bold"
      },
      "size": "extra_large",
      "color": "#FFFFFF",
      "has_speed_lines": true,
      "transform": {
        "rotation": "match_direction"
      }
    },
    "glow": {
      "name": "发光文字",
      "font": {
        "family": "Arial, sans-serif",
        "weight": "bold"
      },
      "color": "#FFFFFF",
      "glow": {
        "color": "#00BFFF",
        "strength": 20,
        "blur": 10
      },
      "animation": {
        "type": "pulse",
        "duration": 1.0
      }
    }
  }
}
```

### 4.2 标题/回目文字

```json
{
  "title_styles": {
    "chapter_title": {
      "name": "章节标题",
      "font": {
        "family": "serif",
        "size": 72,
        "weight": "bold"
      },
      "color": "#FFFFFF",
      "stroke": {
        "width": 4,
        "color": "#000000"
      },
      "shadow": {
        "enabled": true,
        "offset_y": 5,
        "blur": 10
      },
      "background": {
        "type": "gradient",
        "colors": ["#1a1a2e", "#16213e"],
        "opacity": 0.8
      },
      "position": "center",
      "animation": {
        "type": "fade_in_scale",
        "duration": 1.5
      }
    },
    "episode_number": {
      "name": "集数",
      "font": {
        "family": "sans-serif",
        "size": 36,
        "weight": "normal"
      },
      "color": "#AAAAAA",
      "position": "top_right"
    }
  }
}
```

---

## 5. 文字渲染

### 5.1 气泡渲染

```python
def render_speech_bubble(frame, text, position, style):
    """渲染对话气泡到帧"""

    # 创建气泡图层
    bubble_layer = Image.new('RGBA', frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(bubble_layer)

    # 绘制气泡形状
    x, y, width, height = position

    if style['shape'] == 'rounded_rect':
        draw_rounded_rectangle(
            draw,
            [x, y, x + width, y + height],
            radius=style['border_radius'],
            fill=style['fill_color'],
            outline=style['border_color'],
            width=style['border_width']
        )

    # 绘制尾巴
    if style.get('tail'):
        draw_bubble_tail(draw, position, style['tail'], style['fill_color'])

    # 绘制文字
    font = load_font(style['font_family'], style['font_size'])
    text_lines = format_bubble_text(text, width - style['padding'] * 2, font)

    text_y = y + style['padding']
    for line in text_lines:
        text_width = draw.textlength(line, font=font)
        text_x = x + (width - text_width) / 2

        # 描边
        if style.get('stroke_width', 0) > 0:
            draw_stroked_text(
                draw,
                (text_x, text_y),
                line,
                font=font,
                fill=style['text_color'],
                stroke_fill=style['stroke_color'],
                stroke_width=style['stroke_width']
            )
        else:
            draw.text((text_x, text_y), line, font=font, fill=style['text_color'])

        text_y += style['font_size'] + style['line_spacing']

    # 合成到帧
    result = Image.alpha_composite(frame.convert('RGBA'), bubble_layer)

    return result.convert('RGB')
```

### 5.2 字幕渲染

```python
def render_subtitle(frame, subtitle_text, style, position):
    """渲染字幕到帧"""

    # 创建字幕图层
    subtitle_layer = Image.new('RGBA', frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(subtitle_layer)

    # 加载字体
    font = load_font(style['font']['family'], style['font']['size'])

    # 测量文本尺寸
    bbox = draw.textbbox((0, 0), subtitle_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # 计算位置
    if position['x'] == 'center':
        x = (frame.size[0] - text_width) / 2
    else:
        x = position['x']

    if position['y'] == 'bottom':
        y = frame.size[1] - text_height - position['margin']
    elif position['y'] == 'top':
        y = position['margin']
    else:
        y = position['y']

    # 绘制背景（如果有）
    if style.get('background'):
        if style['background']['type'] == 'semi_transparent_black':
            bg_width = text_width + 20
            bg_height = text_height + 10
            bg_x = x - 10
            bg_y = y - 5

            draw.rectangle(
                [bg_x, bg_y, bg_x + bg_width, bg_y + bg_height],
                fill=(0, 0, 0, int(255 * style['background']['opacity']))
            )

    # 绘制阴影
    if style.get('shadow', {}).get('enabled'):
        shadow_x = x + style['shadow']['offset_x']
        shadow_y = y + style['shadow']['offset_y']
        draw.text(
            (shadow_x, shadow_y),
            subtitle_text,
            font=font,
            fill=style['shadow']['color']
        )

    # 绘制描边
    if style.get('stroke', {}).get('width', 0) > 0:
        for adj_x in range(-style['stroke']['width'], style['stroke']['width'] + 1):
            for adj_y in range(-style['stroke']['width'], style['stroke']['width'] + 1):
                if adj_x != 0 or adj_y != 0:
                    draw.text(
                        (x + adj_x, y + adj_y),
                        subtitle_text,
                        font=font,
                        fill=style['stroke']['color']
                    )

    # 绘制文字
    draw.text((x, y), subtitle_text, font=font, fill=style['color'])

    # 合成
    result = Image.alpha_composite(frame.convert('RGBA'), subtitle_layer)

    return result.convert('RGB')
```

---

## 6. 输出格式

### 6.1 字幕文件（SRT）

```srt
1
00:00:04,500 --> 00:00:06,800
你好，请问你是谁？

2
00:00:08,500 --> 00:00:11,200
我是新来的转校生。

3
00:00:12,000 --> 00:00:15,500
（内心）总觉得他身上有种神秘的气息...
```

### 6.2 气泡数据格式

```json
{
  "speech_bubbles": [
    {
      "bubble_id": "bubble_001",
      "shot_id": "shot_002",
      "character_id": "char_001",
      "text": "你好，请问你是谁？",
      "position": {
        "x": 1200,
        "y": 200,
        "width": 300,
        "height": 100
      },
      "style": {
        "shape": "rounded_rect",
        "fill": {
          "type": "solid",
          "color": "#FFFFFF",
          "opacity": 0.9
        },
        "border": {
          "type": "solid",
          "width": 2,
          "color": "#000000"
        },
        "tail": {
          "type": "simple_round",
          "direction": "bottom_left",
          "target_character": "char_001"
        },
        "font": {
          "family": "Arial",
          "size": 24,
          "color": "#000000"
        }
      },
      "timing": {
        "start_time": 4.5,
        "end_time": 6.8,
        "fade_in": 0.2,
        "fade_out": 0.2
      }
    }
  ]
}
```

---

*文档版本：1.0*
*所属阶段：阶段8 - 文字与字幕*
*最后更新：2026-02-02*
