# 阶段10：输出交付阶段详细说明

## 1. 概述

输出交付阶段是动态漫生成流程的最后环节，负责将渲染完成的视频按照用户需求进行格式化、打包和交付。本阶段提供预览、调整、多版本导出等功能。

---

## 2. 文件输出

### 2.1 输出选项

#### 完整视频输出

```json
{
  "full_video_output": {
    "description": "输出完整的动态漫视频",
    "options": {
      "single_file": {
        "format": "mp4",
        "include_intro": true,
        "include_credits": true,
        "chapter_markers": true
      },
      "segmented": {
        "split_by_chapter": true,
        "split_by_duration": 600,
        "naming_pattern": "title_part{number}.mp4"
      }
    }
  }
}
```

#### 分章节输出

```python
def split_video_by_chapters(full_video, chapter_markers, output_dir):
    """按章节分割视频"""

    segments = []

    for i, chapter in enumerate(chapter_markers):
        start_time = chapter['start_time']
        end_time = chapter['end_time']

        output_file = os.path.join(
            output_dir,
            f"{chapter['title']}.mp4"
        )

        # 使用FFmpeg分割
        cmd = [
            'ffmpeg',
            '-i', full_video,
            '-ss', str(start_time),
            '-t', str(end_time - start_time),
            '-c', 'copy',
            output_file
        ]

        subprocess.run(cmd)

        segments.append({
            "chapter_number": i + 1,
            "title": chapter['title'],
            "file": output_file,
            "duration": end_time - start_time
        })

    return segments
```

#### 多分辨率版本

```json
{
  "resolution_variants": {
    "4k": {
      "resolution": "3840x2160",
      "bitrate": "15000k",
      "use_case": "高质量存档、4K播放器"
    },
    "1080p": {
      "resolution": "1920x1080",
      "bitrate": "5000k",
      "use_case": "标准输出、网络播放"
    },
    "720p": {
      "resolution": "1280x720",
      "bitrate": "3000k",
      "use_case": "移动设备、带宽受限"
    },
    "480p": {
      "resolution": "854x480",
      "bitrate": "1500k",
      "use_case": "低带宽环境"
    },
    "mobile_vertical": {
      "resolution": "1080x1920",
      "bitrate": "4000k",
      "use_case": "短视频平台（抖音、快手）"
    }
  }
}
```

#### 纯视频版/带字幕版

```python
def generate_subtitle_variants(final_video, subtitle_data):
    """生成带字幕和不带字幕版本"""

    variants = []

    # 纯视频版（无硬字幕）
    variants.append({
        "type": "video_only",
        "file": "output/final_no_subtitles.mp4",
        "has_hard_subtitles": False,
        "has_soft_subtitles": False
    })

    # 软字幕版本（字幕可开关）
    soft_subtitle_file = create_srt_file(subtitle_data)
    video_with_soft_subs = embed_soft_subtitles(final_video, soft_subtitle_file)

    variants.append({
        "type": "soft_subtitles",
        "file": video_with_soft_subs,
        "has_hard_subtitles": False,
        "has_soft_subtitles": True,
        "subtitle_languages": ["zh-CN"]
    })

    # 硬字幕版本（字幕烧录到视频）
    video_with_hard_subs = burn_subtitles(final_video, subtitle_data)

    variants.append({
        "type": "hard_subtitles",
        "file": video_with_hard_subs,
        "has_hard_subtitles": True,
        "has_soft_subtitles": False,
        "note": "字幕不可移除"
    })

    return variants
```

### 2.2 元数据添加

```python
def add_metadata_to_video(video_file, metadata):
    """为视频添加元数据"""

    output_file = video_file.replace('.mp4', '_with_meta.mp4')

    cmd = [
        'ffmpeg',
        '-i', video_file,
        '-metadata', f"title={metadata['title']}",
        '-metadata', f"artist={metadata.get('author', 'FrameLeap')}",
        '-metadata', f"comment={metadata.get('description', '')}",
        '-metadata', f"episode={metadata.get('episode', 1)}",
        '-metadata', f"genre={metadata.get('genre', 'Animation')}",
        '-metadata', f"year={metadata.get('year', 2026)}",
        '-c', 'copy',
        output_file
    ]

    subprocess.run(cmd)

    return output_file
```

#### 章节标记

```json
{
  "chapter_markers": [
    {
      "number": 1,
      "title": "序幕：雨夜",
      "start_time": 0.0,
      "end_time": 30.5,
      "thumbnail": "thumbnails/chapter_01.jpg"
    },
    {
      "number": 2,
      "title": "相遇",
      "start_time": 30.5,
      "end_time": 120.0,
      "thumbnail": "thumbnails/chapter_02.jpg"
    },
    {
      "number": 3,
      "title": "命运的开始",
      "start_time": 120.0,
      "end_time": 180.5,
      "thumbnail": "thumbnails/chapter_03.jpg"
    }
  ]
}
```

#### 封面缩略图

```python
def generate_thumbnails(video_file, timestamps):
    """生成视频缩略图"""

    thumbnails = []

    for i, timestamp in enumerate(timestamps):
        output_file = f"thumbnails/thumb_{i+1}.jpg"

        cmd = [
            'ffmpeg',
            '-i', video_file,
            '-ss', str(timestamp),
            '-vframes', '1',
            '-q:v', '2',
            output_file
        ]

        subprocess.run(cmd)

        thumbnails.append({
            "index": i + 1,
            "timestamp": timestamp,
            "file": output_file
        })

    # 生成封面图（最佳画面）
    cover = select_best_thumbnail(thumbnails)
    shutil.copy(cover['file'], "thumbnails/cover.jpg")

    return thumbnails
```

---

## 3. 预览与调整

### 3.1 实时预览

#### 时间轴预览

```json
{
  "timeline_preview": {
    "interface": {
      "timeline": {
        "total_duration": 180.5,
        "zoom_levels": ["fit", "100%", "200%", "frame_level"],
        "show_waveforms": true,
        "show_thumbnails": true
      },
      "tracks": {
        "video": ["V1", "V2", "V3", "V4", "V5"],
        "audio": ["A1", "A2", "A3"],
        "markers": ["chapter", "effect", "note"]
      }
    },
    "controls": {
      "playback": ["play", "pause", "stop", "loop"],
      "navigation": ["skip_to_start", "skip_to_end", "prev_frame", "next_frame"],
      "marking": ["set_in", "set_out", "clear_markers"]
    }
  }
}
```

#### 预览播放器

```python
class PreviewPlayer:
    """预览播放器"""

    def __init__(self, video_file, subtitle_file=None):
        self.video_file = video_file
        self.subtitle_file = subtitle_file
        self.current_position = 0.0
        self.playing = False

    def play(self):
        """播放预览"""
        self.playing = True

    def pause(self):
        """暂停"""
        self.playing = False

    def seek(self, timestamp):
        """跳转到指定时间"""
        self.current_position = timestamp

    def get_frame(self, timestamp):
        """获取指定时间的帧"""
        cap = cv2.VideoCapture(self.video_file)
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
        ret, frame = cap.read()
        cap.release()

        if ret:
            return frame
        return None

    def get_subtitles(self, timestamp):
        """获取指定时间的字幕"""
        if self.subtitle_file:
            # 解析SRT文件并返回当前字幕
            return parse_srt_at_time(self.subtitle_file, timestamp)
        return None
```

### 3.2 逐帧检查

```python
def frame_by_frame_inspection(video_file):
    """逐帧检查视频"""

    cap = cv2.VideoCapture(video_file)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    frames_data = []

    for frame_num in range(total_frames):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()

        if ret:
            timestamp = frame_num / cap.get(cv2.CAP_PROP_FPS)

            # 分析帧
            analysis = analyze_frame(frame)

            frames_data.append({
                "frame_number": frame_num,
                "timestamp": timestamp,
                "analysis": analysis
            })

    cap.release()

    return frames_data

def analyze_frame(frame):
    """分析单帧质量"""

    analysis = {
        "brightness": np.mean(frame),
        "contrast": np.std(frame),
        "blur_score": calculate_blur_score(frame),
        "faces": detect_faces(frame),
        "text_regions": detect_text_regions(frame)
    }

    return analysis
```

### 3.3 音画同步检查

```python
def check_av_sync(video_file, tolerance=0.1):
    """检查音画同步"""

    # 提取关键音频事件（如拍手、重音）
    audio_events = detect_audio_events(video_file)

    # 提取对应视觉事件
    video_events = detect_visual_events(video_file)

    # 比较时间差
    sync_issues = []

    for audio_event in audio_events:
        closest_video = find_closest_event(audio_event['time'], video_events)

        if closest_video:
            time_diff = abs(audio_event['time'] - closest_video['time'])

            if time_diff > tolerance:
                sync_issues.append({
                    "timestamp": audio_event['time'],
                    "offset": time_diff,
                    "type": "audio_early" if audio_event['time'] < closest_video['time'] else "audio_late"
                })

    return {
        "is_synced": len(sync_issues) == 0,
        "issues": sync_issues,
        "max_offset": max([i['offset'] for i in sync_issues]) if sync_issues else 0
    }
```

### 3.4 修正机制

#### 重新生成问题镜头

```python
def regenerate_problematic_shots(shot_ids, regenerate_config):
    """重新生成有问题的镜头"""

    regenerated = []

    for shot_id in shot_ids:
        # 获取原始配置
        original_config = get_shot_config(shot_id)

        # 应用修正
        fixed_config = apply_fixes(original_config, regenerate_config)

        # 重新生成图像
        new_images = regenerate_shot_images(fixed_config)

        # 重新动画化
        new_animation = reanimate_shot(new_images, fixed_config)

        regenerated.append({
            "shot_id": shot_id,
            "new_images": new_images,
            "new_animation": new_animation
        })

    return regenerated
```

#### 调整音频平衡

```python
def adjust_audio_mix(video_file, adjustments):
    """调整音频混合"""

    # 提取音频
    audio = extract_audio(video_file)

    for adjustment in adjustments:
        track = adjustment['track']
        change_db = adjustment['db_change']

        # 应用音量调整
        audio = adjust_track_volume(audio, track, change_db)

    # 重新混合
    mixed_audio = remix_audio(audio)

    # 重新合并到视频
    output_file = video_file.replace('.mp4', '_adjusted_audio.mp4')
    merge_audio_to_video(video_file, mixed_audio, output_file)

    return output_file
```

#### 修改文字内容

```python
def modify_text_content(video_file, text_modifications):
    """修改视频中的文字内容"""

    # 解析视频为帧序列
    frames = extract_frames(video_file)

    modified_frames = []

    for frame_info in frames:
        frame = frame_info['frame']
        timestamp = frame_info['timestamp']

        # 检查当前时间戳是否有需要修改的文字
        for mod in text_modifications:
            if mod['start_time'] <= timestamp <= mod['end_time']:
                # 移除旧文字
                frame_without_text = remove_text_from_frame(frame, mod['region'])

                # 添加新文字
                frame_with_new_text = add_text_to_frame(
                    frame_without_text,
                    mod['new_text'],
                    mod['position'],
                    mod['style']
                )

                frame = frame_with_new_text

        modified_frames.append(frame)

    # 重新编码为视频
    output_file = video_file.replace('.mp4', '_modified_text.mp4')
    encode_frames_to_video(modified_frames, output_file)

    return output_file
```

---

## 4. 批量处理

### 4.1 批量导出

```python
def batch_export(project_configs, output_base_dir):
    """批量导出多个项目"""

    results = []

    for i, config in enumerate(project_configs):
        print(f"处理项目 {i+1}/{len(project_configs)}: {config['name']}")

        try:
            # 创建输出目录
            project_output_dir = os.path.join(output_base_dir, config['name'])
            os.makedirs(project_output_dir, exist_ok=True)

            # 导出
            output_file = os.path.join(project_output_dir, "final.mp4")

            render_result = render_project(config, output_file)

            results.append({
                "project": config['name'],
                "status": "success",
                "output_file": output_file,
                "duration": render_result['duration']
            })

        except Exception as e:
            results.append({
                "project": config['name'],
                "status": "failed",
                "error": str(e)
            })

    # 生成报告
    generate_batch_report(results, output_base_dir)

    return results
```

### 4.2 队列管理

```python
class RenderQueue:
    """渲染队列管理器"""

    def __init__(self, max_concurrent=2):
        self.queue = []
        self.running = []
        self.completed = []
        self.max_concurrent = max_concurrent

    def add_job(self, job_config):
        """添加渲染任务到队列"""
        self.queue.append({
            "id": str(uuid.uuid4()),
            "config": job_config,
            "status": "pending",
            "added_at": datetime.now()
        })

    def process_queue(self):
        """处理队列"""
        while self.queue or self.running:
            # 启动新任务
            while len(self.running) < self.max_concurrent and self.queue:
                job = self.queue.pop(0)
                self.start_job(job)

            # 检查完成的任务
            self.check_completed_jobs()

            # 等待
            time.sleep(1)

    def start_job(self, job):
        """启动单个任务"""
        job['status'] = 'running'
        job['started_at'] = datetime.now()
        self.running.append(job)

        # 在新线程中执行
        thread = threading.Thread(target=self.execute_job, args=(job,))
        thread.start()

    def execute_job(self, job):
        """执行任务"""
        try:
            result = render_project(job['config'], job['config']['output_file'])
            job['result'] = result
            job['status'] = 'completed'
        except Exception as e:
            job['error'] = str(e)
            job['status'] = 'failed'

        # 移动到完成列表
        self.running.remove(job)
        self.completed.append(job)
```

---

## 5. 交付格式

### 5.1 标准交付包

```
delivery_package/
├── video/
│   ├── final_1080p.mp4          # 主视频
│   ├── final_720p.mp4           # 移动版
│   └── final_vertical.mp4       # 短视频版
├── audio/
│   ├── dialogue_only.wav        # 纯对白
│   ├── bgm_only.wav             # 纯BGM
│   └── full_mix.wav             # 完整混音
├── subtitles/
│   ├── chinese.srt              # 中文字幕
│   └── english.srt              # 英文字幕
├── thumbnails/
│   ├── cover.jpg                # 封面
│   ├── thumb_01.jpg
│   ├── thumb_02.jpg
│   └── ...
├── metadata/
│   ├── info.json                # 元数据
│   └── credits.txt              # 制作名单
├── project_files/
│   ├── script.json              # 剧本
│   └── assets/                  # 资源文件
└── README.md                    # 说明文档
```

### 5.2 元数据格式

```json
{
  "package_info": {
    "title": "雨夜的邂逅",
    "episode": 1,
    "total_episodes": 1,
    "duration": "3:00",
    "format": "mp4",
    "resolution": "1920x1080",
    "aspect_ratio": "16:9",
    "fps": 30,
    "audio": "stereo",
    "created_by": "FrameLeap",
    "created_date": "2026-02-02",
    "version": "1.0"
  },
  "contents": {
    "video_files": [
      {
        "file": "video/final_1080p.mp4",
        "type": "main",
        "resolution": "1920x1080",
        "bitrate": "5000k",
        "size_mb": 150
      },
      {
        "file": "video/final_720p.mp4",
        "type": "alternative",
        "resolution": "1280x720",
        "bitrate": "3000k",
        "size_mb": 90
      }
    ],
    "subtitle_files": [
      {
        "language": "zh-CN",
        "file": "subtitles/chinese.srt",
        "format": "srt",
        "type": "dialogue"
      }
    ]
  },
  "credits": {
    "story": "AI Generated",
    "visuals": "FrameLeap AI Engine",
    "voices": "AI Text-to-Speech",
    "music": "AI Music Generation",
    "production": "FrameLeap"
  }
}
```

---

## 6. 分享与分发

### 6.1 平台适配

```json
{
  "platform_presets": {
    "bilibili": {
      "resolution": "1920x1080",
      "codec": "h264",
      "bitrate": "5000k",
      "container": "mp4",
      "max_file_size": "4GB",
      "subtitle_support": "external_srt"
    },
    "youtube": {
      "resolution": "1920x1080",
      "codec": "h264",
      "bitrate": "8000k",
      "container": "mp4",
      "max_file_size": "128GB",
      "subtitle_support": "closed_caption"
    },
    "douyin": {
      "resolution": "1080x1920",
      "codec": "h264",
      "bitrate": "4000k",
      "container": "mp4",
      "max_duration": 300,
      "aspect_ratio": "9:16"
    },
    "weibo": {
      "resolution": "1280x720",
      "codec": "h264",
      "bitrate": "3000k",
      "container": "mp4",
      "max_duration": 600,
      "max_file_size": "500MB"
    }
  }
}
```

### 6.2 自动上传

```python
def upload_to_platform(video_file, platform, credentials, metadata):
    """自动上传到平台"""

    if platform == "bilibili":
        return upload_to_bilibili(video_file, credentials, metadata)
    elif platform == "youtube":
        return upload_to_youtube(video_file, credentials, metadata)
    elif platform == "douyin":
        return upload_to_douyin(video_file, credentials, metadata)
    else:
        raise ValueError(f"不支持的平台: {platform}")
```

---

## 7. 质量报告

### 7.1 生成质量报告

```python
def generate_quality_report(project_data):
    """生成质量报告"""

    report = {
        "project_id": project_data['id'],
        "generated_at": datetime.now().isoformat(),

        "video_metrics": {
            "resolution": project_data['output']['resolution'],
            "duration": project_data['output']['duration'],
            "fps": project_data['output']['fps'],
            "bitrate": project_data['output']['bitrate'],
            "file_size_mb": project_data['output']['file_size'] / (1024 * 1024)
        },

        "generation_metrics": {
            "total_frames": project_data['stats']['total_frames'],
            "ai_generated_frames": project_data['stats']['ai_frames'],
            "total_shots": project_data['stats']['total_shots'],
            "regenerated_shots": project_data['stats']['regenerated'],
            "rendering_time": project_data['stats']['rendering_time']
        },

        "quality_scores": {
            "visual_consistency": project_data['quality']['visual_consistency'],
            "character_consistency": project_data['quality']['character_consistency'],
            "audio_sync": project_data['quality']['audio_sync'],
          "overall": project_data['quality']['overall_score']
        }
    }

    return report
```

---

*文档版本：1.0*
*所属阶段：阶段10 - 输出交付*
*最后更新：2026-02-02*
