# 阶段7：音频生成阶段详细说明

## 1. 概述

音频生成阶段负责为动态漫生成完整的音频轨道，包括角色配音（TTS）、音效和背景音乐。本阶段确保音画同步，营造沉浸式的视听体验。

---

## 2. 配音生成

### 2.1 语音合成（TTS）

#### TTS引擎选择

**主流TTS引擎对比**：

| 引擎 | 优点 | 缺点 | 适用场景 |
|-----|------|------|---------|
| Azure TTS | 质量高、音色丰富 | 成本较高 | 商业项目推荐 |
| Google TTS | 质量稳定、API简单 | 音色相对有限 | 通用场景 |
| VITS | 开源、可本地部署 | 需要自己训练 | 个人项目 |
| GPT-SoVITS | 克隆音色效果好 | 需要参考音频 | 角色音色一致性 |
| Fish Audio | 中文效果好、情感丰富 | 相对较新 | 中文内容 |
| ElevenLabs | 英语质量极高 | 中文支持一般 | 英文内容 |

#### 角色音色分配

```python
def assign_voice_to_character(character_info):
    """为角色分配音色"""

    voice_profile = {
        "character_id": character_info['id'],
        "character_name": character_info['name'],

        # 基础声音属性
        "voice_attributes": {
            "gender": character_info['gender'],
            "age_range": estimate_age_range(character_info['age']),
            "pitch": determine_pitch(character_info),
            "speed": determine_speaking_speed(character_info['personality']),
            "tone": determine_tone(character_info['personality'])
        },

        # TTS配置
        "tts_config": {
            "engine": "azure",  # 或其他引擎
            "voice_name": select_matching_voice(character_info),
            "style": determine speaking_style(character_info),
            "role_play": determine_role_play_style(character_info)
        },

        # 情感参数
        "emotion_parameters": {
            "neutral": {"style": "calm", "pitch": 0},
            "happy": {"style": "cheerful", "pitch": +0.2},
            "sad": {"style": "sad", "pitch": -0.1, "rate": 0.9},
            "angry": {"style": "angry", "pitch": +0.3, "volume": +0.2},
            "surprised": {"style": "excited", "pitch": +0.4, "rate": 1.1}
        }
    }

    return voice_profile
```

**音色匹配算法**：
```python
def select_matching_voice(character_info):
    """根据角色特征匹配最合适的音色"""

    # 获取可用音色列表
    available_voices = get_available_voices()

    # 评分标准
    scores = []

    for voice in available_voices:
        score = 0

        # 性别匹配
        if voice['gender'] == character_info['gender']:
            score += 30

        # 年龄匹配
        age_diff = abs(voice['age'] - character_info['age'])
        score += max(0, 20 - age_diff * 2)

        # 性格匹配
        personality_match = compare_personality(voice['tone'], character_info['personality'])
        score += personality_match * 30

        # 声音特质匹配
        if character_info.get('voice_traits'):
            for trait in character_info['voice_traits']:
                if trait in voice['traits']:
                    score += 10

        scores.append({
            "voice": voice,
            "score": score
        })

    # 返回最高分音色
    best_voice = max(scores, key=lambda x: x['score'])
    return best_voice['voice']['name']
```

### 2.2 情感语音合成

#### 情感标注解析

```python
def synthesize_emotional_speech(text, emotion, intensity, voice_profile):
    """合成带情感的语音"""

    # 解析情感参数
    emotion_config = voice_profile['emotion_parameters'].get(emotion, {})

    # 基础TTS参数
    params = {
        "text": text,
        "voice": voice_profile['tts_config']['voice_name'],
        "engine": voice_profile['tts_config']['engine']
    }

    # 应用情感参数
    if emotion_config:
        params['style'] = emotion_config.get('style', 'neutral')
        params['pitch'] = emotion_config.get('pitch', 0)
        params['rate'] = emotion_config.get('rate', 1.0)
        params['volume'] = emotion_config.get('volume', 0)

    # 应用强度
    if intensity != 1.0:
        params['pitch'] *= intensity
        params['volume'] = (params['volume'] + 1) * intensity - 1

    # 合成
    audio = tts_engine.synthesize(params)

    return audio
```

#### SSML格式

**SSML（Speech Synthesis Markup Language）示例**：
```xml
<speak>
    <!-- 正常语速 -->
    <prosody rate="1.0">
        今天天气真好。
    </prosody>

    <!-- 放慢语速，低沉声音 -->
    <prosody rate="0.8" pitch="-10%">
        可是...
    </prosody>

    <!-- 加快语速，升高音调 -->
    <prosody rate="1.2" pitch="+20%">
        等等！那是什么？！
    </prosody>

    <!-- 强调 -->
    <emphasis level="strong">
        绝对不能让它逃掉！
    </emphasis>

    <!-- 停顿 -->
    <break time="500ms"/>

    <!-- 轻声低语 -->
    <prosody volume="-20%" rate="0.9">
        一定会找到你的...
    </prosody>
</speak>
```

**SSML生成函数**：
```python
def text_to_ssml(text, emotion_data):
    """将文本转换为SSML格式"""

    ssml_parts = ["<speak>"]

    for segment in emotion_data:
        emotion = segment['emotion']
        intensity = segment.get('intensity', 0.5)

        # 构建情感参数
        prosody_attrs = []

        if emotion == "happy":
            prosody_attrs.append('pitch="+10%"')
            prosody_attrs.append('rate="1.1"')
        elif emotion == "sad":
            prosody_attrs.append('pitch="-10%"')
            prosody_attrs.append('rate="0.9"')
        elif emotion == "angry":
            prosody_attrs.append('pitch="+20%"')
            prosody_attrs.append('rate="1.2"')
        elif emotion == "surprised":
            prosody_attrs.append('pitch="+30%"')
            prosody_attrs.append('rate="1.3"')

        if prosody_attrs:
            ssml_parts.append(f'<prosody {" ".join(prosody_attrs)}>')
            ssml_parts.append(segment['text'])
            ssml_parts.append('</prosody>')
        else:
            ssml_parts.append(segment['text'])

        # 添加停顿
        if segment.get('pause'):
            ssml_parts.append(f'<break time="{segment["pause"]}"/>')

    ssml_parts.append("</speak>")

    return "".join(ssml_parts)
```

### 2.3 角色音色一致性

#### GPT-SoVITS音色克隆

```python
def clone_character_voice(character_name, reference_audio_path):
    """使用GPT-SoVITS克隆角色音色"""

    # 1. 准备参考音频
    reference_audio = load_audio(reference_audio_path)

    # 2. 提取音色特征
    speaker_embedding = extract_speaker_embedding(reference_audio)

    # 3. 训练/微调模型
    model = GPTSoVITS.fine_tune(
        base_model="base_model",
        speaker_embedding=speaker_embedding,
        reference_audio=reference_audio
    )

    # 4. 保存模型
    model_path = f"models/voices/{character_name}.pth"
    model.save(model_path)

    return model_path
```

#### 批量配音生成

```python
def generate_all_dialogue(script, character_voices):
    """生成剧本中所有对白的配音"""

    audio_segments = []

    for scene in script['scenes']:
        for shot in scene['shots']:
            if shot.get('dialogue'):
                # 获取角色音色配置
                character_id = shot['dialogue']['speaker']
                voice_config = character_voices[character_id]

                # 获取情感标注
                emotion = shot['dialogue'].get('emotion', 'neutral')
                intensity = shot['dialogue'].get('intensity', 0.5)

                # 转换为SSML
                ssml = text_to_ssml(shot['dialogue']['text'], [{
                    "text": shot['dialogue']['text'],
                    "emotion": emotion,
                    "intensity": intensity
                }])

                # 合成音频
                audio = tts_engine.synthesize(
                    ssml=ssml,
                    voice_config=voice_config
                )

                audio_segments.append({
                    "shot_id": shot['shot_id'],
                    "character_id": character_id,
                    "audio": audio,
                    "duration": len(audio) / sample_rate,
                    "start_time": shot['time_range']['start'],
                    "text": shot['dialogue']['text']
                })

    return audio_segments
```

---

## 3. 音效生成

### 3.1 环境音效

#### 音效类型库

```json
{
  "ambient_sounds": {
    "weather": {
      "rain": {
        "light": "rain_light.wav",
        "medium": "rain_medium.wav",
        "heavy": "rain_heavy.wav"
      },
      "wind": {
        "breeze": "wind_breeze.wav",
        "strong": "wind_strong.wav",
        "howling": "wind_howl.wav"
      },
      "thunder": {
        "distant": "thunder_distant.wav",
        "close": "thunder_close.wav",
        "rumble": "thunder_rumble.wav"
      }
    },
    "environment": {
      "city": {
        "day": "city_day_ambience.wav",
        "night": "city_night_ambience.wav"
      },
      "forest": {
        "day": "forest_day.wav",
        "night": "forest_night.wav",
        "with_birds": "forest_birds.wav"
      },
      "indoor": {
        "classroom": "classroom_ambience.wav",
        "cafe": "cafe_ambience.wav",
        "quiet_room": "room_silence.wav"
      }
    }
  }
}
```

#### 环境音匹配

```python
def match_ambient_sound(scene_info):
    """根据场景信息匹配环境音效"""

    ambient_tracks = []

    # 天气音效
    if scene_info.get('weather'):
        weather = scene_info['weather']['condition']
        intensity = scene_info['weather'].get('intensity', 'medium')

        if weather in ['雨', 'rain', '雨夜']:
            track = f"rain_{intensity}.wav"
            ambient_tracks.append({
                "type": "weather",
                "file": track,
                "volume": 0.4,
                "loop": True
            })

    # 场景环境音
    location_type = scene_info['location']['type']
    if location_type in ['街道', '城市街道', 'city_street']:
        time = scene_info.get('time', {}).get('time_of_day', 'day')
        track = f"city_{time}_ambience.wav"
        ambient_tracks.append({
            "type": "environment",
            "file": track,
            "volume": 0.3,
            "loop": True
        })

    return ambient_tracks
```

### 3.2 动作音效

#### 动作音效库

```json
{
  "action_sounds": {
    "footsteps": {
      "normal": {
        "concrete": "footstep_concrete.wav",
        "grass": "footstep_grass.wav",
        "wood": "footstep_wood.wav"
      },
      "running": {
        "concrete": "run_concrete.wav",
        "grass": "run_grass.wav"
      }
    },
    "impacts": {
      "punch": "punch_impact.wav",
      "kick": "kick_impact.wav",
      "fall": "body_fall.wav"
    },
    "objects": {
      "door_open": "door_open.wav",
      "door_close": "door_close.wav",
      "glass_break": "glass_break.wav",
      "sword_draw": "sword_draw.wav"
    },
    "magic": {
      "spell_cast": "magic_cast.wav",
      "explosion": "magic_explosion.wav",
      "energy_beam": "energy_beam.wav"
    }
  }
}
```

#### 音效同步

```python
def sync_sound_effects(action_timeline):
    """同步动作音效到时间轴"""

    synced_sounds = []

    for action in action_timeline:
        action_type = action['type']
        timestamp = action['timestamp']

        # 查找匹配的音效
        sound_file = find_sound_for_action(action_type, action.get('details'))

        if sound_file:
            synced_sounds.append({
                "file": sound_file,
                "start_time": timestamp,
                "duration": get_audio_duration(sound_file),
                "volume": action.get('volume', 1.0),
                "action_id": action['id']
            })

    return synced_sounds
```

### 3.3 AI音效生成

#### AudioLDM

```python
def generate_sound_with_audioldm(text_description, duration=2.0):
    """使用AudioLDM生成音效"""

    # 加载模型
    model = load_audioldm_model()

    # 生成参数
    params = {
        "prompt": text_description,
        "negative_prompt": "low quality, noisy, distorted",
        "duration": duration,
        "guidance_scale": 2.5,
        "num_inference_steps": 50
    }

    # 生成音频
    audio = model.generate(params)

    return audio
```

**音效描述示例**：
```python
sound_descriptions = {
    "magic_spell": "A magical whooshing sound with sparkling chimes",
    "sword_clash": "Metal swords clashing together with impact",
    "rain_heavy": "Heavy rain falling on pavement with thunder",
    "footsteps_grass": "Footsteps crunching on dry grass",
    "door_creak": "An old wooden door creaking open slowly",
    "explosion": "A powerful explosion with rumbling bass"
}
```

---

## 4. 背景音乐

### 4.1 BGM生成/选择

#### 情感标签匹配

```python
def select_background_music(scene_emotion, scene_intensity):
    """根据场景情感选择背景音乐"""

    # 音乐库
    music_library = load_music_library()

    # 匹配标准
    candidates = []

    for track in music_library:
        score = 0

        # 情感匹配
        if track['emotion'] == scene_emotion:
            score += 40
        elif scene_emotion in track['related_emotions']:
            score += 20

        # 强度匹配
        intensity_diff = abs(track['intensity'] - scene_intensity)
        score += max(0, 30 - intensity_diff * 10)

        # 节奏匹配
        if scene_intensity > 0.7:
            # 高强度场景偏好快节奏
            if track['tempo'] > 120:
                score += 15
        else:
            # 低强度场景偏好慢节奏
            if track['tempo'] < 100:
                score += 15

        candidates.append({
            "track": track,
            "score": score
        })

    # 返回最佳匹配
    if candidates:
        best_match = max(candidates, key=lambda x: x['score'])
        return best_match['track']

    return None
```

#### AI音乐生成（Suno/Udio）

```python
def generate_music_with_ai(mood, style, duration, tempo_preference="medium"):
    """使用AI生成背景音乐"""

    # 构建提示词
    prompt_parts = [
        mood,
        style,
        "instrumental",
        "background music"
    ]

    if tempo_preference == "fast":
        prompt_parts.append("fast tempo")
    elif tempo_preference == "slow":
        prompt_parts.append("slow tempo")

    prompt = ", ".join(prompt_parts)

    # 使用Suno API
    response = suno_api.generate(
        prompt=prompt,
        duration=duration,
        instrumental=True,
        model="chirp-v3-5"
    )

    # 下载生成的音乐
    audio_url = response['audio_url']
    audio = download_audio(audio_url)

    return audio
```

**音乐风格库**：
```json
{
  "music_styles": {
    "emotional": {
      "sad": {
        "instruments": ["piano", "strings"],
        "tempo": "slow",
        "keywords": ["melancholic", "sorrowful", "touching"]
      },
      "touching": {
        "instruments": ["piano", "violin", "cello"],
        "tempo": "slow_to_medium",
        "keywords": ["emotional", "beautiful", "heartwarming"]
      }
    },
    "tension": {
      "suspense": {
        "instruments": ["synth", "percussion", "low_strings"],
        "tempo": "slow",
        "keywords": ["suspenseful", "mysterious", "tense"]
      },
      "action": {
        "instruments": ["drums", "brass", "electric_guitar"],
        "tempo": "fast",
        "keywords": ["intense", "epic", "driving"]
      }
    },
    "peaceful": {
      "calm": {
        "instruments": ["piano", "acoustic_guitar", "flute"],
        "tempo": "slow",
        "keywords": ["peaceful", "calm", "serene"]
      },
      "happy": {
        "instruments": ["piano", "strings", "light_percussion"],
        "tempo": "medium",
        "keywords": ["uplifting", "cheerful", "bright"]
      }
    }
  }
}
```

### 4.2 音乐分段与循环

```python
def prepare_music_for_scene(music_track, scene_duration, fade_duration=2.0):
    """准备音乐以适配场景时长"""

    music_duration = get_audio_duration(music_track)

    if music_duration >= scene_duration:
        # 音乐足够长，裁剪
        trimmed = trim_audio(music_track, 0, scene_duration)

        # 添加淡出
        output = add_fade_out(trimmed, fade_duration)

    else:
        # 音乐不够长，循环
        num_loops = int(scene_duration / music_duration) + 1
        looped = loop_audio(music_track, num_loops)

        # 裁剪到精确长度
        trimmed = trim_audio(looped, 0, scene_duration)

        # 添加淡出
        output = add_fade_out(trimmed, fade_duration)

    return output
```

---

## 5. 音频混音

### 5.1 音轨平衡

```python
def mix_audio_tracks(dialogue_track, sfx_track, bgm_track):
    """混合多个音频轨道"""

    # 设置相对音量
    dialogue_volume = 1.0
    sfx_volume = 0.6
    bgm_volume = 0.3

    # 应用音量
    dialogue = apply_volume(dialogue_track, dialogue_volume)
    sfx = apply_volume(sfx_track, sfx_volume)
    bgm = apply_volume(bgm_track, bgm_volume)

    # 混合
    mixed = dialogue.overlay(sfx)
    mixed = mixed.overlay(bgm)

    return mixed
```

**动态音量调整**：
```python
def adjust_volume_dynamically(audio, dialogue_regions):
    """根据对白区域动态调整背景音乐音量"""

    result = audio.copy()

    for region in dialogue_regions:
        start_time = region['start_time']
        end_time = region['end_time']

        # 对白期间降低BGM音量（避让）
        # 淡出
        fade_out_start = start_time - 0.5
        result = decrease_volume(result, fade_out_start, start_time, 0.3, bgm_volume * 0.5)

        # 淡入恢复
        fade_in_start = end_time
        fade_in_end = end_time + 0.5
        result = increase_volume(result, fade_in_start, fade_in_end, bgm_volume * 0.5, bgm_volume)

    return result
```

### 5.2 音频同步

#### 音画对齐

```python
def align_audio_to_video(audio_segments, video_timeline):
    """将音频段对齐到视频时间轴"""

    aligned_segments = []

    for audio in audio_segments:
        shot_id = audio['shot_id']

        # 找到对应的镜头
        shot = find_shot_by_id(video_timeline, shot_id)

        if shot:
            # 计算时间偏移
            video_start = shot['time_range']['start']
            audio_offset = audio['start_time'] - video_start

            aligned_segments.append({
                "audio": audio['audio'],
                "start_time": video_start,
                "offset": audio_offset,
                "duration": audio['duration']
            })

    return aligned_segments
```

#### 口型同步

```python
def sync_lip_movement(audio, video_frames):
    """调整音频以匹配口型（简单时间对齐）"""

    # 检测语音起始点
    speech_onsets = detect_speech_onsets(audio)

    # 检测嘴部运动起始点
    mouth_movements = detect_mouth_movements(video_frames)

    # 计算时间偏移
    if speech_onsets and mouth_movements:
        offset = mouth_movements[0] - speech_onsets[0]

        # 应用偏移
        if abs(offset) > 0.1:  # 超过100ms则调整
            audio = shift_audio(audio, offset)

    return audio
```

---

## 6. 输出格式

### 6.1 音频轨道输出

```json
{
  "audio_output": {
    "format": "multi_track",
    "tracks": [
      {
        "track_id": "dialogue",
        "type": "dialogue",
        "file": "audio/dialogue.wav",
        "codec": "pcm_s16le",
        "sample_rate": 48000,
        "channels": 1,
        "segments": [
          {
            "character_id": "char_001",
            "start_time": 5.2,
            "end_time": 8.5,
            "text": "你好，请问你是谁？"
          }
        ]
      },
      {
        "track_id": "sfx",
        "type": "sound_effects",
        "file": "audio/sfx.wav",
        "codec": "pcm_s16le",
        "sample_rate": 48000,
        "channels": 2
      },
      {
        "track_id": "bgm",
        "type": "background_music",
        "file": "audio/bgm.wav",
        "codec": "pcm_s16le",
        "sample_rate": 48000,
        "channels": 2
      }
    ],
    "mixed": {
      "file": "audio/final_mix.wav",
      "codec": "pcm_s16le",
      "sample_rate": 48000,
      "channels": 2
    }
  }
}
```

### 6.2 时间轴格式

```json
{
  "audio_timeline": {
    "total_duration": 180.0,
    "events": [
      {
        "time": 0.0,
        "type": "music_start",
        "track": "bgm",
        "file": "music/sad_piano.mp3",
        "fade_in": 2.0,
        "volume": 0.3
      },
      {
        "time": 0.0,
        "type": "ambient_start",
        "track": "sfx",
        "file": "ambience/rain_heavy.wav",
        "volume": 0.4,
        "loop": true
      },
      {
        "time": 4.5,
        "type": "dialogue",
        "character": "char_001",
        "text": "你好，请问你是谁？",
        "file": "dialogue/char_001_001.wav",
        "duration": 2.3
      },
      {
        "time": 8.5,
        "type": "sfx",
        "file": "sfx/footstep_grass.wav",
        "volume": 0.5
      }
    ]
  }
}
```

---

*文档版本：1.0*
*所属阶段：阶段7 - 音频生成*
*最后更新：2026-02-02*
