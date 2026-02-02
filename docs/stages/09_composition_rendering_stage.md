# 阶段9：合成渲染阶段详细说明

## 1. 概述

合成渲染阶段是动态漫生成的最后环节，负责将所有视觉元素（动画帧、特效、文字）和音频元素（对白、音效、音乐）合成为最终的完整视频。本阶段确保各轨道同步、质量达标、格式正确。

---

## 2. 多轨道合成

### 2.1 视频轨道结构

#### 轨道层次设计

```
视频轨道层次（从下到上）：

┌─────────────────────────────────────────────┐
│ V5: 覆盖层（闪光、转场特效、标题）            │
├─────────────────────────────────────────────┤
│ V4: 文字/字幕层（对话气泡、字幕）             │
├─────────────────────────────────────────────┤
│ V3: 特效层（粒子、光效、漫画特效）           │
├─────────────────────────────────────────────┤
│ V2: 前景动画层（角色动画、前景元素）         │
├─────────────────────────────────────────────┤
│ V1: 主视频层（背景、主画面、运镜）           │
└─────────────────────────────────────────────┘
```

#### 轨道配置

```json
{
  "video_tracks": {
    "V1_main": {
      "name": "主视频轨道",
      "layer": 1,
      "content": ["animated_frames", "camera_movements"],
      "blending": "normal",
      "opacity": 1.0
    },
    "V2_foreground": {
      "name": "前景动画层",
      "layer": 2,
      "content": ["character_animations", "foreground_elements"],
      "blending": "normal",
      "opacity": 1.0
    },
    "V3_effects": {
      "name": "特效层",
      "layer": 3,
      "content": ["particles", "light_effects", "manga_effects"],
      "blending": "additive",
      "opacity": 0.8
    },
    "V4_text": {
      "name": "文字字幕层",
      "layer": 4,
      "content": ["speech_bubbles", "subtitles", "titles"],
      "blending": "normal",
      "opacity": 1.0
    },
    "V5_overlay": {
      "name": "覆盖层",
      "layer": 5,
      "content": ["flash_effects", "transitions", "vignette"],
      "blending": "screen",
      "opacity": "varies"
    }
  }
}
```

### 2.2 音频轨道结构

```
音频轨道层次：

┌─────────────────────────────────────────────┐
│ A3: BGM轨道（背景音乐，循环，低音量）        │
├─────────────────────────────────────────────┤
│ A2: 音效轨道（环境音、动作音效）             │
├─────────────────────────────────────────────┤
│ A1: 对白轨道（角色配音，最高优先级）         │
└─────────────────────────────────────────────┘
```

```json
{
  "audio_tracks": {
    "A1_dialogue": {
      "name": "对白轨道",
      "priority": 1,
      "default_volume": 1.0,
      "ducking": {
        "affects": ["A3_bgm"],
        "reduction": 0.5,
        "fade_time": 0.3
      }
    },
    "A2_sfx": {
      "name": "音效轨道",
      "priority": 2,
      "default_volume": 0.6,
      "ducking": null
    },
    "A3_bgm": {
      "name": "背景音乐轨道",
      "priority": 3,
      "default_volume": 0.3,
      "loop": true,
      "ducking": null
    }
  }
}
```

### 2.3 轨道混合模式

#### 混合模式定义

```json
{
  "blending_modes": {
    "normal": {
      "name": "正常",
      "formula": "result = foreground",
      "use_case": "标准叠加"
    },
    "additive": {
      "name": "叠加（加法）",
      "formula": "result = foreground + background",
      "use_case": ["光效", "粒子", "发光元素"],
      "note": "用于增加亮度"
    },
    "multiply": {
      "name": "正片叠底",
      "formula": "result = foreground * background",
      "use_case": ["阴影", "变暗效果"]
    },
    "screen": {
      "name": "滤色",
      "formula": "result = 1 - (1 - foreground) * (1 - background)",
      "use_case": ["高光", "闪光效果"]
    },
    "overlay": {
      "name": "覆盖",
      "formula": "混合multiply和screen",
      "use_case": ["对比度调整", "综合效果"]
    },
    "alpha_blend": {
      "name": "Alpha混合",
      "formula": "result = foreground * alpha + background * (1 - alpha)",
      "use_case": ["半透明元素", "淡入淡出"]
    }
  }
}
```

#### 混合模式应用

```python
def composite_layers(base_layer, overlay_layers):
    """合成多个图层"""

    result = base_layer.copy()

    for layer in overlay_layers:
        overlay = layer['image']
        mode = layer['blend_mode']
        opacity = layer.get('opacity', 1.0)

        # 应用混合模式
        if mode == 'normal':
            blended = alpha_blend(result, overlay, opacity)
        elif mode == 'additive':
            blended = additive_blend(result, overlay, opacity)
        elif mode == 'screen':
            blended = screen_blend(result, overlay, opacity)
        elif mode == 'multiply':
            blended = multiply_blend(result, overlay, opacity)
        else:
            blended = alpha_blend(result, overlay, opacity)

        result = blended

    return result

def alpha_blend(base, overlay, opacity):
    """Alpha混合"""
    return Image.blend(base, overlay, opacity)

def additive_blend(base, overlay, opacity):
    """加法混合（用于光效）"""
    base_array = np.array(base).astype(float)
    overlay_array = np.array(overlay).astype(float) * opacity

    result = base_array + overlay_array
    result = np.clip(result, 0, 255).astype(np.uint8)

    return Image.fromarray(result)

def screen_blend(base, overlay, opacity):
    """滤色混合"""
    base_array = np.array(base).astype(float) / 255
    overlay_array = np.array(overlay).astype(float) / 255 * opacity

    result = 1 - (1 - base_array) * (1 - overlay_array)
    result = (np.clip(result, 0, 1) * 255).astype(np.uint8)

    return Image.fromarray(result)
```

---

## 3. 转场渲染

### 3.1 转场实现

#### 淡入淡出

```python
def render_fade_transition(from_clip, to_clip, duration, fps=30):
    """渲染淡入淡出转场"""

    frames = []
    total_frames = int(duration * fps)

    # 淡出部分
    fade_out_frames = int(total_frames / 2)

    for i in range(fade_out_frames):
        progress = i / fade_out_frames
        alpha = 1 - progress

        frame = from_clip.get_frame(i)
        faded = apply_alpha(frame, alpha)

        frames.append(faded)

    # 淡入部分
    fade_in_frames = total_frames - fade_out_frames

    for i in range(fade_in_frames):
        progress = i / fade_in_frames
        alpha = progress

        frame = to_clip.get_frame(i)
        faded = apply_alpha(frame, alpha)

        frames.append(faded)

    return frames

def apply_alpha(frame, alpha):
    """应用透明度"""
    frame_array = np.array(frame).astype(float)
    result = frame_array * alpha
    return Image.fromarray(result.astype(np.uint8))
```

#### 擦除转场

```python
def render_wipe_transition(from_clip, to_clip, duration, direction="left_to_right", fps=30):
    """渲染擦除转场"""

    frames = []
    total_frames = int(duration * fps)

    for i in range(total_frames):
        progress = i / total_frames
        ease = ease_in_out(progress)

        if direction == "left_to_right":
            split_x = int(from_clip.width * ease)
        elif direction == "right_to_left":
            split_x = int(from_clip.width * (1 - ease))
        elif direction == "top_to_bottom":
            split_y = int(from_clip.height * ease)
        else:  # bottom_to_top
            split_y = int(from_clip.height * (1 - ease))

        # 获取两帧
        from_frame = from_clip.get_frame(i)
        to_frame = to_clip.get_frame(i)

        # 组合
        if direction in ["left_to_right", "right_to_left"]:
            # 左右擦除
            left = from_frame.crop((0, 0, split_x, from_frame.height))
            right = to_frame.crop((split_x, 0, from_frame.width, from_frame.height))

            combined = Image.new('RGB', from_frame.size)
            combined.paste(left, (0, 0))
            combined.paste(right, (split_x, 0))
        else:
            # 上下擦除
            top = from_frame.crop((0, 0, from_frame.width, split_y))
            bottom = to_frame.crop((0, split_y, from_frame.width, from_frame.height))

            combined = Image.new('RGB', from_frame.size)
            combined.paste(top, (0, 0))
            combined.paste(bottom, (0, split_y))

        frames.append(combined)

    return frames
```

#### 缩放转场

```python
def render_zoom_transition(from_clip, to_clip, duration, fps=30):
    """渲染缩放转场"""

    frames = []
    total_frames = int(duration * fps)

    for i in range(total_frames):
        progress = i / total_frames
        ease = ease_in_out(progress)

        # 从一个镜头放大到纯色
        scale1 = 1 + ease * 0.5
        frame1 = from_clip.get_frame(i)
        zoomed1 = zoom_image(frame1, scale1)

        # 从纯色缩小到下一个镜头
        scale2 = 1.5 - ease * 0.5
        frame2 = to_clip.get_frame(i)
        zoomed2 = zoom_image(frame2, scale2)

        # 混合
        if progress < 0.5:
            alpha = 1 - (progress * 2)
            combined = alpha_blend(zoomed1, zoomed2, 1 - alpha)
        else:
            alpha = (progress - 0.5) * 2
            combined = alpha_blend(zoomed1, zoomed2, alpha)

        frames.append(combined)

    return frames
```

### 3.2 转场时间轴

```python
def apply_transitions_to_timeline(timeline):
    """将转场应用到时间轴"""

    result_timeline = []

    for i, shot in enumerate(timeline['shots']):
        # 添加主镜头
        result_timeline.append({
            "type": "shot",
            "shot_id": shot['shot_id'],
            "frames": shot['frames']
        })

        # 检查是否有转场
        if i < len(timeline['shots']) - 1:
            transition = shot.get('transition')
            if transition:
                next_shot = timeline['shots'][i + 1]
                transition_frames = render_transition(
                    from_clip=shot,
                    to_clip=next_shot,
                    transition_type=transition['type'],
                    duration=transition['duration']
                )

                result_timeline.append({
                    "type": "transition",
                    "transition_type": transition['type'],
                    "frames": transition_frames
                })

    return result_timeline
```

---

## 4. 音视频同步

### 4.1 时间戳对齐

```python
def align_av_timeline(video_timeline, audio_timeline):
    """对齐音视频时间轴"""

    # 创建统一时间轴
    unified_timeline = []
    total_duration = max(
        video_timeline['total_duration'],
        audio_timeline['total_duration']
    )

    # 按帧处理
    fps = 30
    total_frames = int(total_duration * fps)

    for frame_num in range(total_frames):
        timestamp = frame_num / fps

        # 获取视频帧
        video_frame = get_frame_at_time(video_timeline, timestamp)

        # 获取音频状态
        audio_state = {
            "dialogue": get_active_audio(audio_timeline['dialogue'], timestamp),
            "sfx": get_active_audio(audio_timeline['sfx'], timestamp),
            "bgm": get_active_audio(audio_timeline['bgm'], timestamp)
        }

        unified_timeline.append({
            "frame_number": frame_num,
            "timestamp": timestamp,
            "video_frame": video_frame,
            "audio_state": audio_state
        })

    return unified_timeline
```

### 4.2 帧精确同步

```python
def ensure_frame_sync(video_frames, audio_segments, fps=30):
    """确保音视频帧级同步"""

    synced = []

    for i, frame in enumerate(video_frames):
        timestamp = i / fps

        # 查找当前有效的音频段
        active_audio = []

        for segment in audio_segments:
            if segment['start_time'] <= timestamp <= segment['end_time']:
                active_audio.append({
                    "type": segment['type'],
                    "audio": segment['audio'],
                    "offset_in_segment": timestamp - segment['start_time']
                })

        synced.append({
            "frame": frame,
            "timestamp": timestamp,
            "active_audio": active_audio
        })

    return synced
```

---

## 5. 最终渲染

### 5.1 编码配置

#### 视频编码参数

```json
{
  "video_encoding": {
    "codec_options": {
      "h264": {
        "name": "H.264/AVC",
        "compatibility": "excellent",
        "efficiency": "medium",
        "recommended_bitrates": {
          "1080p": "5000k",
          "720p": "3000k",
          "480p": "1500k"
        },
        "profiles": ["high", "main", "baseline"],
        "preset": "medium",
        "crf": 23
      },
      "h265": {
        "name": "H.265/HEVC",
        "compatibility": "good",
        "efficiency": "high",
        "recommended_bitrates": {
          "1080p": "3000k",
          "720p": "1800k",
          "480p": "900k"
        },
        "profiles": ["main", "main10"],
        "preset": "medium",
        "crf": 25
      },
      "vp9": {
        "name": "VP9",
        "compatibility": "web",
        "efficiency": "high",
        "recommended_bitrates": {
          "1080p": "3500k",
          "720p": "2000k",
          "480p": "1000k"
        },
        "speed": "2"
      },
      "av1": {
        "name": "AV1",
        "compatibility": "limited",
        "efficiency": "very_high",
        "recommended_bitrates": {
          "1080p": "2500k",
          "720p": "1500k",
          "480p": "800k"
        },
        "speed": "5"
      }
    }
  }
}
```

#### 音频编码参数

```json
{
  "audio_encoding": {
    "codec_options": {
      "aac": {
        "name": "AAC",
        "compatibility": "excellent",
        "bitrate": "192k",
        "sample_rate": 48000,
        "channels": 2
      },
      "opus": {
        "name": "Opus",
        "compatibility": "good",
        "bitrate": "128k",
        "sample_rate": 48000,
        "channels": 2
      },
      "mp3": {
        "name": "MP3",
        "compatibility": "excellent",
        "bitrate": "192k",
        "sample_rate": 48000,
        "channels": 2
      }
    }
  }
}
```

### 5.2 容器格式

```json
{
  "container_formats": {
    "mp4": {
      "name": "MP4",
      "video_codecs": ["h264", "h265", "av1"],
      "audio_codecs": ["aac", "mp3"],
      "compatibility": "universal",
      "best_for": ["general_distribution", "web", "mobile"],
      "metadata_support": "excellent"
    },
    "webm": {
      "name": "WebM",
      "video_codecs": ["vp8", "vp9", "av1"],
      "audio_codecs": ["opus", "vorbis"],
      "compatibility": "web_modern",
      "best_for": ["web_optimized", "size_efficient"],
      "metadata_support": "good"
    },
    "mov": {
      "name": "QuickTime/MOV",
      "video_codecs": ["h264", "prores", "dnxhd"],
      "audio_codecs": ["aac", "alac", "pcm"],
      "compatibility": "apple_devices",
      "best_for": ["apple_ecosystem", "editing"],
      "metadata_support": "excellent"
    },
    "mkv": {
      "name": "Matroska",
      "video_codecs": ["almost_any"],
      "audio_codecs": ["almost_any"],
      "compatibility": "media_players",
      "best_for": ["archival", "multiple_tracks"],
      "metadata_support": "excellent"
    }
  }
}
```

### 5.3 FFmpeg渲染命令

```python
def build_ffmpeg_command(render_config):
    """构建FFmpeg渲染命令"""

    cmd = ['ffmpeg']

    # 输入参数
    for input in render_config['inputs']:
        cmd.extend(['-i', input['file']])

    # 视频编码
    cmd.extend([
        '-c:v', render_config['video_codec'],
        '-b:v', render_config['video_bitrate'],
        '-preset', render_config.get('preset', 'medium'),
        '-crf', str(render_config.get('crf', 23))
    ])

    # 音频编码
    cmd.extend([
        '-c:a', render_config['audio_codec'],
        '-b:a', render_config['audio_bitrate'],
        '-ar', str(render_config.get('sample_rate', 48000))
    ])

    # 帧率
    cmd.extend(['-r', str(render_config['fps'])])

    # 像素格式
    cmd.extend(['-pix_fmt', 'yuv420p'])

    # 色彩空间
    if render_config.get('color_space'):
        cmd.extend(['-colorspace', render_config['color_space']])
        cmd.extend(['-color_primaries', 'bt709'])
        cmd.extend(['-color_trc', 'bt709'])

    # 元数据
    cmd.extend([
        '-metadata', f"title={render_config['title']}",
        '-metadata', f"comment={render_config.get('comment', '')}"
    ])

    # 输出文件
    cmd.append(render_config['output_file'])

    return cmd

# 使用示例
config = {
    "inputs": [
        {"file": "temp/video_stream.mp4"},
        {"file": "temp/audio_mix.wav"}
    ],
    "video_codec": "libx264",
    "video_bitrate": "5000k",
    "audio_codec": "aac",
    "audio_bitrate": "192k",
    "fps": 30,
    "preset": "medium",
    "crf": 23,
    "title": "动态漫标题",
    "output_file": "output/final.mp4"
}

cmd = build_ffmpeg_command(config)
subprocess.run(cmd)
```

---

## 6. 质量控制

### 6.1 渲染前检查

```python
def pre_render_check(render_config):
    """渲染前检查"""

    checks = {
        "status": "pass",
        "warnings": [],
        "errors": []
    }

    # 检查输入文件
    for input in render_config['inputs']:
        if not os.path.exists(input['file']):
            checks['errors'].append(f"输入文件不存在: {input['file']}")
            checks['status'] = 'fail'

    # 检查编码参数
    if render_config['video_bitrate']:
        bitrate_num = int(render_config['video_bitrate'].rstrip('k'))
        if bitrate_num < 1000:
            checks['warnings'].append("视频比特率较低，可能影响画质")

    # 检查时长匹配
    video_duration = get_video_duration(render_config['inputs'][0]['file'])
    audio_duration = get_audio_duration(render_config['inputs'][1]['file'])

    if abs(video_duration - audio_duration) > 0.5:
        checks['warnings'].append(f"音视频时长不匹配: 视频={video_duration}s, 音频={audio_duration}s")

    # 检查输出目录
    output_dir = os.path.dirname(render_config['output_file'])
    if not os.path.exists(output_dir):
        checks['errors'].append(f"输出目录不存在: {output_dir}")
        checks['status'] = 'fail'

    return checks
```

### 6.2 渲染后验证

```python
def post_render_validate(output_file, expected_duration, expected_resolution):
    """渲染后验证"""

    validation = {
        "status": "pass",
        "issues": []
    }

    # 检查文件存在
    if not os.path.exists(output_file):
        validation['status'] = 'fail'
        validation['issues'].append("输出文件未生成")
        return validation

    # 检查文件大小
    file_size = os.path.getsize(output_file)
    if file_size < 1000:  # 小于1KB
        validation['status'] = 'fail'
        validation['issues'].append("输出文件过小，可能渲染失败")

    # 检查视频信息
    probe = ffmpeg.probe(output_file)

    # 时长检查
    actual_duration = float(probe['streams'][0]['duration'])
    if abs(actual_duration - expected_duration) > 1.0:
        validation['issues'].append(f"时长不符: 预期{expected_duration}s, 实际{actual_duration}s")

    # 分辨率检查
    video_stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    actual_resolution = f"{video_stream['width']}x{video_stream['height']}"
    if actual_resolution != expected_resolution:
        validation['issues'].append(f"分辨率不符: 预期{expected_resolution}, 实际{actual_resolution}")

    # 帧率检查
    actual_fps = eval(video_stream['r_frame_rate'])
    if abs(actual_fps - 30) > 1:
        validation['issues'].append(f"帧率异常: {actual_fps}")

    # 播放测试
    try:
        # 尝试读取前10帧
        cap = cv2.VideoCapture(output_file)
        for _ in range(10):
            ret, frame = cap.read()
            if not ret:
                validation['issues'].append("视频读取失败")
                break
        cap.release()
    except Exception as e:
        validation['status'] = 'fail'
        validation['issues'].append(f"播放测试失败: {str(e)}")

    return validation
```

---

## 7. 输出与交付

### 7.1 文件输出

```json
{
  "output_package": {
    "primary": {
      "file": "output/final_dynamic_comic.mp4",
      "type": "final_video",
      "codec": "h264",
      "bitrate": "5000k",
      "resolution": "1920x1080",
      "duration": 180.5
    },
    "alternatives": [
      {
        "file": "output/final_720p.mp4",
        "type": "lower_resolution",
        "resolution": "1280x720",
        "bitrate": "3000k"
      },
      {
        "file": "output/final_web.webm",
        "type": "web_optimized",
        "codec": "vp9",
        "bitrate": "3500k"
      }
    ],
    "metadata": {
      "title": "雨夜的邂逅",
      "episode": 1,
      "author": "FrameLeap",
      "creation_date": "2026-02-02",
      "description": "一个孤独的少年在雨夜中遇到了神秘少女"
    }
  }
}
```

### 7.2 渲染日志

```json
{
  "render_log": {
    "start_time": "2026-02-02T10:30:00Z",
    "end_time": "2026-02-02T10:45:23Z",
    "total_duration": 923,
    "stages": [
      {
        "stage": "video_composition",
        "start": "10:30:00",
        "end": "10:38:45",
        "duration": 525,
        "status": "success"
      },
      {
        "stage": "audio_mixing",
        "start": "10:38:45",
        "end": "10:42:10",
        "duration": 205,
        "status": "success"
      },
      {
        "stage": "encoding",
        "start": "10:42:10",
        "end": "10:45:23",
        "duration": 193,
        "status": "success"
      }
    ],
    "statistics": {
      "total_frames": 5415,
      "audio_segments": 45,
      "transitions": 12,
      "effects_rendered": 89
    }
  }
}
```

---

*文档版本：1.0*
*所属阶段：阶段9 - 合成渲染*
*最后更新：2026-02-02*
