# 阶段6：动画化阶段详细说明

## 1. 概述

动画化阶段负责将静态图像转换为动态视频。本阶段通过运镜、角色动画、环境动画和特效动画，赋予静态画面生命力，创造流畅的视觉体验。

---

## 2. 运镜生成

### 2.1 虚拟摄像机运动

#### 平移（Pan）

**实现原理**：
```python
def apply_pan_effect(image, direction, distance, duration, fps=30):
    """应用平移效果"""

    width, height = image.size

    # 计算移动向量
    if direction == "left":
        offset = (distance, 0)
    elif direction == "right":
        offset = (-distance, 0)
    elif direction == "up":
        offset = (0, distance)
    elif direction == "down":
        offset = (0, -distance)
    else:
        raise ValueError(f"Unknown direction: {direction}")

    # 计算裁剪框大小
    crop_width = width - abs(offset[0])
    crop_height = height - abs(offset[1])

    frames = []
    total_frames = int(duration * fps)

    for i in range(total_frames):
        progress = i / total_frames

        # 计算当前裁剪位置
        current_offset_x = int(offset[0] * progress)
        current_offset_y = int(offset[1] * progress)

        # 裁剪
        left = max(0, -current_offset_x)
        top = max(0, -current_offset_y)
        right = min(width, width - current_offset_x)
        bottom = min(height, height - current_offset_y)

        cropped = image.crop((left, top, right, bottom))

        # 调整到目标尺寸
        resized = cropped.resize((width, height))

        frames.append(resized)

    return frames
```

**平移类型**：
```json
{
  "pan_types": {
    "horizontal_pan": {
      "description": "水平移动",
      "directions": ["left", "right"],
      "typical_duration": "3-6秒",
      "use_case": "展示横向场景、跟随横向动作"
    },
    "vertical_pan": {
      "description": "垂直移动",
      "directions": ["up", "down"],
      "typical_duration": "3-6秒",
      "use_case": "展示纵向场景、建筑物、跟随垂直动作"
    },
    "diagonal_pan": {
      "description": "对角线移动",
      "directions": ["diagonal_left_up", "diagonal_right_down", etc.],
      "typical_duration": "4-8秒",
      "use_case": "动态构图、斜向场景"
    }
  }
}
```

#### 缩放（Zoom）

**实现原理**：
```python
def apply_zoom_effect(image, zoom_type, scale_factor, duration, fps=30):
    """应用缩放效果"""

    width, height = image.size
    frames = []
    total_frames = int(duration * fps)

    if zoom_type == "zoom_in":
        # 从原始尺寸放大
        start_scale = 1.0
        end_scale = scale_factor
    elif zoom_type == "zoom_out":
        # 从放大状态缩小
        start_scale = scale_factor
        end_scale = 1.0
    else:
        raise ValueError(f"Unknown zoom type: {zoom_type}")

    for i in range(total_frames):
        progress = i / total_frames
        ease = ease_in_out(progress)  # 使用缓动函数

        current_scale = start_scale + (end_scale - start_scale) * ease

        # 计算裁剪区域
        crop_width = int(width / current_scale)
        crop_height = int(height / current_scale)

        left = (width - crop_width) // 2
        top = (height - crop_height) // 2
        right = left + crop_width
        bottom = top + crop_height

        # 裁剪并调整大小
        cropped = image.crop((left, top, right, bottom))
        resized = cropped.resize((width, height))

        frames.append(resized)

    return frames
```

**缓动函数**：
```python
def ease_in_out(t):
    """平滑缓动函数"""
    return t * t * (3 - 2 * t)

def ease_in(t):
    """缓入"""
    return t * t

def ease_out(t):
    """缓出"""
    return t * (2 - t)
```

#### 旋转（Rotate）

**实现原理**：
```python
def apply_rotation_effect(image, angle, duration, fps=30):
    """应用旋转效果"""

    frames = []
    total_frames = int(duration * fps)

    for i in range(total_frames):
        progress = i / total_frames
        ease = ease_in_out(progress)

        current_angle = angle * ease

        # 旋转图像
        rotated = image.rotate(current_angle, expand=True, resample=Image.BICUBIC)

        # 裁剪到原始尺寸（居中）
        width, height = image.size
        rot_width, rot_height = rotated.size

        left = (rot_width - width) // 2
        top = (rot_height - height) // 2
        right = left + width
        bottom = top + height

        cropped = rotated.crop((left, top, right, bottom))

        frames.append(cropped)

    return frames
```

#### 复合运动

**组合运镜**：
```python
def apply_combined_movement(image, movements, duration, fps=30):
    """应用组合运镜效果"""

    frames = []
    total_frames = int(duration * fps)

    for i in range(total_frames):
        progress = i / total_frames
        ease = ease_in_out(progress)

        current_frame = image.copy()

        # 按顺序应用各种运动
        for movement in movements:
            move_type = movement['type']
            params = movement['params']

            if move_type == "pan":
                current_frame = apply_pan_single_frame(current_frame, params, progress, ease)
            elif move_type == "zoom":
                current_frame = apply_zoom_single_frame(current_frame, params, progress, ease)
            elif move_type == "rotate":
                current_frame = apply_rotate_single_frame(current_frame, params, progress, ease)

        frames.append(current_frame)

    return frames

# 示例：缓慢推近 + 同时轻微旋转
movements = [
    {"type": "zoom", "params": {"zoom_type": "zoom_in", "scale_factor": 1.3}},
    {"type": "rotate", "params": {"angle": 5}}
]
```

### 2.2 基于深度图的视差效果

#### 深度估计

```python
def estimate_depth(image):
    """估计图像深度"""

    # 使用MiDaS或其他深度估计模型
    depth_model = load_midas_model()

    depth_map = depth_model.estimate(image)

    # 归一化到0-1
    depth_map = (depth_map - depth_map.min()) / (depth_map.max() - depth_map.min())

    return depth_map
```

#### 视差动画

```python
def apply_parallax_effect(image, depth_map, movement, duration, fps=30):
    """基于深度图应用视差效果"""

    frames = []
    total_frames = int(duration * fps)

    # 分层处理
    layers = separate_by_depth(image, depth_map, num_layers=5)

    for i in range(total_frames):
        progress = i / total_frames
        ease = ease_in_out(progress)

        composited = Image.new('RGB', image.size)

        # 根据深度移动不同层级
        for layer_depth, layer_image in layers:
            # 深度越大（越远），移动越慢
            # 深度越小（越近），移动越快
            parallax_factor = 1.0 - layer_depth  # 近处移动快

            offset = int(movement['distance'] * parallax_factor * ease)

            # 移动层级
            if movement['direction'] == 'horizontal':
                shifted = ImageChops.offset(layer_image, offset, 0)
            else:
                shifted = ImageChops.offset(layer_image, 0, offset)

            # 合成
            composited = Image.alpha_composite(composited.convert('RGBA'), shifted.convert('RGBA'))

        frames.append(composited.convert('RGB'))

    return frames
```

---

## 3. 画面元素动画

### 3.1 角色动画

#### 呼吸效果

```python
def add_breathing_effect(image, character_mask, intensity=0.02, duration=3.0, fps=30):
    """添加呼吸效果（微小缩放）"""

    frames = []
    total_frames = int(duration * fps)
    width, height = image.size

    for i in range(total_frames):
        # 使用正弦波模拟呼吸节奏
        progress = i / total_frames
        scale = 1.0 + intensity * math.sin(2 * math.pi * progress)

        # 仅对角色区域应用
        scaled_width = int(width * scale)
        scaled_height = int(height * scale)

        # 缩放角色
        character = Image.composite(image, Image.new('RGB', image.size), character_mask)
        character_scaled = character.resize((scaled_width, scaled_height), Image.LANCZOS)

        # 居中放置
        paste_x = (width - scaled_width) // 2
        paste_y = (height - scaled_height) // 2

        # 创建新帧
        frame = image.copy()
        frame.paste(character_scaled, (paste_x, paste_y), character_mask.resize((scaled_width, scaled_height)))

        frames.append(frame)

    return frames
```

#### 头部摆动

```python
def add_head_movement(image, head_mask, movement_type="subtle", duration=5.0, fps=30):
    """添加头部微小摆动"""

    frames = []
    total_frames = int(duration * fps)

    # 运动参数
    if movement_type == "subtle":
        max_angle = 2
        max_shift = 3
    elif movement_type == "noticeable":
        max_angle = 5
        max_shift = 8
    else:
        max_angle = 1
        max_shift = 2

    for i in range(total_frames):
        progress = i / total_frames

        # 使用多个正弦波组合创建自然运动
        angle = max_angle * math.sin(2 * math.pi * progress * 0.5)
        shift_x = max_shift * math.sin(2 * math.pi * progress * 0.3)
        shift_y = max_shift * math.sin(2 * math.pi * progress * 0.4)

        # 提取头部
        head = extract_head_region(image, head_mask)

        # 变换
        head_transformed = transform_head(head, angle, shift_x, shift_y)

        # 合成
        frame = image.copy()
        frame = composite_head(frame, head_transformed, head_mask)

        frames.append(frame)

    return frames
```

#### 眼睛眨动

```python
def add_blinking_effect(image, eye_regions, blink_interval=4.0, fps=30):
    """添加眨眼效果"""

    frames = []
    total_frames = int(blink_interval * fps)
    blink_duration = 0.15  # 眨眼持续时间
    blink_frames = int(blink_duration * fps)

    for i in range(total_frames):
        frame = image.copy()

        # 检查是否应该眨眼
        time_to_blink = (i % total_frames) < blink_frames

        if time_to_blink:
            # 眨眼中 - 逐渐闭合再张开
            blink_progress = (i % blink_frames) / blink_frames
            if blink_progress < 0.5:
                # 闭合
                eye_openness = 1 - (blink_progress * 2)
            else:
                # 张开
                eye_openness = (blink_progress - 0.5) * 2

            # 调整眼睛高度
            for eye_region in eye_regions:
                frame = adjust_eye_openness(frame, eye_region, eye_openness)

        frames.append(frame)

    return frames
```

### 3.2 AI图像动画化

#### AnimateDiff

```python
def animate_with_animatediff(image, motion_module, prompt, duration=3.0, fps=24):
    """使用AnimateDiff生成动画"""

    # 加载AnimateDiff模型
    model = load_animatediff_model(motion_module)

    # 配置参数
    config = {
        "prompt": prompt,
        "negative_prompt": "blurry, distorted, low quality",
        "num_frames": int(duration * fps),
        "guidance_scale": 7.5,
        "seed": -1
    }

    # 生成动画
    frames = model.animate(image, config)

    return frames
```

#### LivePortrait

```python
def animate_with_liveportrait(source_image, driving_video):
    """使用LivePortrait使图像跟随视频运动"""

    # 加载LivePortrait模型
    model = load_liveportrait_model()

    # 提取驱动视频的关键点
    driving_keypoints = model.extract_keypoints(driving_video)

    # 提取源图像特征
    source_features = model.extract_features(source_image)

    # 生成动画
    animated_frames = []
    for kp in driving_keypoints:
        frame = model.generate_frame(source_features, kp)
        animated_frames.append(frame)

    return animated_frames
```

### 3.3 表情迁移

```python
def transfer_expression(source_image, target_expression):
    """迁移表情到源图像"""

    # 使用表情迁移模型
    model = load_expression_transfer_model()

    # 提取表情特征
    expression_features = model.extract_expression(target_expression)

    # 应用到源图像
    result = model.apply_expression(source_image, expression_features)

    return result
```

---

## 4. 环境动画

### 4.1 背景动态

#### 云层移动

```python
def add_cloud_movement(image, cloud_mask, speed="slow", duration=10.0, fps=30):
    """添加云层移动效果"""

    frames = []
    total_frames = int(duration * fps)

    speed_pixels = {
        "slow": 50,
        "medium": 100,
        "fast": 200
    }[speed]

    for i in range(total_frames):
        progress = i / total_frames

        # 计算移动量
        offset = int(speed_pixels * progress)

        # 移动云层
        moved_clouds = ImageChops.offset(
            image,
            offset,
            0
        )

        # 融合边缘（循环效果）
        blended = blend_edges_for_loop(moved_clouds, offset)

        frames.append(blended)

    return frames
```

#### 水面波动

```python
def add_water_ripple(image, water_mask, intensity="medium", duration=5.0, fps=30):
    """添加水面波动效果"""

    frames = []
    total_frames = int(duration * fps)

    for i in range(total_frames):
        progress = i / total_frames

        # 生成波动图
        wave_map = generate_wave_map(
            image.size,
            frequency=0.1,
            phase=progress * 2 * math.pi,
            amplitude=intensity
        )

        # 应用波动
        rippled = apply_displacement(image, wave_map, water_mask)

        frames.append(rippled)

    return frames
```

### 4.2 天气特效

#### 雨雪粒子

```python
def add_rain_effect(image, intensity="heavy", duration=5.0, fps=30):
    """添加下雨效果"""

    frames = []
    total_frames = int(duration * fps)

    # 粒子系统初始化
    num_drops = {
        "light": 100,
        "medium": 300,
        "heavy": 800
    }[intensity]

    drops = initialize_raindrops(num_drops, image.size)

    for i in range(total_frames):
        frame = image.copy()

        # 更新雨滴位置
        drops = update_raindrops(drops, image.size)

        # 绘制雨滴
        frame = draw_raindrops(frame, drops)

        frames.append(frame)

    return frames
```

#### 雾气效果

```python
def add_fog_effect(image, density="medium", movement_speed="slow", duration=10.0, fps=30):
    """添加雾气效果"""

    frames = []
    total_frames = int(duration * fps)

    # 生成雾气噪声
    fog_noise = generate_perlin_noise(image.size, scale=0.01)

    for i in range(total_frames):
        progress = i / total_frames

        # 移动雾气
        offset_x = int(50 * progress)
        offset_y = int(20 * math.sin(progress * math.pi))
        moved_fog = ImageChops.offset(fog_noise, offset_x, offset_y)

        # 混合
        density_alpha = {
            "light": 0.3,
            "medium": 0.5,
            "heavy": 0.7
        }[density]

        fogged = blend_fog(image, moved_fog, density_alpha)

        frames.append(fogged)

    return frames
```

---

## 5. 特效动画

### 5.1 漫画特效

#### 速度线

```python
def add_speed_lines(image, center_point, direction="radial", density="medium", duration=0.5, fps=30):
    """添加速度线效果"""

    frames = []
    total_frames = int(duration * fps)

    for i in range(total_frames):
        progress = i / total_frames
        alpha = int(255 * (1 - progress))  # 逐渐消失

        if direction == "radial":
            lines = generate_radial_lines(center_point, image.size)
        elif direction == "parallel":
            lines = generate_parallel_lines(image.size, angle=45)
        else:
            lines = generate_converging_lines(center_point, image.size)

        # 绘制到新图层
        effect_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(effect_layer)

        for line in lines:
            draw.line(line, fill=(255, 255, 255, alpha), width=2)

        # 合成
        frame = Image.alpha_composite(image.convert('RGBA'), effect_layer)
        frames.append(frame.convert('RGB'))

    return frames
```

#### 冲击波

```python
def add_shockwave(image, center_point, max_radius, duration=0.8, fps=30):
    """添加冲击波效果"""

    frames = []
    total_frames = int(duration * fps)

    for i in range(total_frames):
        progress = i / total_frames
        ease = ease_out(progress)

        current_radius = int(max_radius * ease)
        alpha = int(255 * (1 - ease))

        # 绘制冲击波
        effect_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(effect_layer)

        draw.ellipse(
            [
                center_point[0] - current_radius,
                center_point[1] - current_radius,
                center_point[0] + current_radius,
                center_point[1] + current_radius
            ],
            outline=(255, 255, 255, alpha),
            width=3
        )

        # 合成
        frame = Image.alpha_composite(image.convert('RGBA'), effect_layer)
        frames.append(frame.convert('RGB'))

    return frames
```

### 5.2 转场效果

#### 漫画格转场

```python
def manga_panel_transition(from_image, to_image, duration=1.0, fps=30):
    """漫画格转场效果"""

    frames = []
    total_frames = int(duration * fps)

    for i in range(total_frames):
        progress = i / total_frames

        # 绘制漫画格边框
        panel_size = int(max(from_image.size) * (1 - progress))
        panel_x = (from_image.width - panel_size) // 2
        panel_y = (from_image.height - panel_size) // 2

        # 创建合成图像
        frame = to_image.copy()

        # 绘制黑色背景
        draw = ImageDraw.Draw(frame)
        draw.rectangle([0, 0, frame.width, frame.height], fill=(0, 0, 0))

        # 绘制"旧"图像在漫画格中
        from_resized = from_image.resize((panel_size, panel_size))
        frame.paste(from_resized, (panel_x, panel_y))

        # 绘制漫画格边框
        border_width = 5
        draw.rectangle(
            [panel_x - border_width, panel_y - border_width,
             panel_x + panel_size + border_width, panel_y + panel_size + border_width],
            outline=(255, 255, 255),
            width=border_width
        )

        frames.append(frame)

    return frames
```

---

## 6. 帧插值

### 6.1 中间帧生成

```python
def interpolate_frames(frame_a, frame_b, num_intermediate_frames, method="rife"):
    """在两帧之间生成中间帧"""

    if method == "rife":
        model = load_rife_model()
    elif method == "dain":
        model = load_dain_model()
    elif method == "film":
        model = load_film_model()
    else:
        raise ValueError(f"Unknown interpolation method: {method}")

    intermediate_frames = []

    for i in range(1, num_intermediate_frames + 1):
        t = i / (num_intermediate_frames + 1)

        # 生成中间帧
        intermediate = model.interpolate(frame_a, frame_b, t)
        intermediate_frames.append(intermediate)

    return intermediate_frames
```

### 6.2 光流法

```python
def apply_optical_flow_warp(frame_a, frame_b, flow):
    """应用光流变形"""

    h, w = flow.shape[:2]

    # 创建网格
    grid_x, grid_y = np.meshgrid(np.arange(w), np.arange(h))

    # 应用光流
    warped_x = grid_x + flow[:, :, 0]
    warped_y = grid_y + flow[:, :, 1]

    # 重映射
    warped = cv2.remap(
        frame_a,
        warped_x.astype(np.float32),
        warped_y.astype(np.float32),
        cv2.INTER_LINEAR
    )

    return warped
```

---

## 7. 输出格式

### 7.1 帧序列输出

```json
{
  "animation_output": {
    "format": "frame_sequence",
    "fps": 30,
    "frames": [
      {
        "frame_number": 1,
        "file_path": "output/frames/shot_001_frame_0001.png",
        "timestamp": 0.0
      }
    ],
    "metadata": {
      "codec": "png",
      "color_space": "sRGB",
      "total_frames": 90,
      "duration": 3.0
    }
  }
}
```

### 7.2 视频输出

```json
{
  "animation_output": {
    "format": "video",
    "container": "mp4",
    "video_codec": "h264",
    "audio_codec": "aac",
    "fps": 30,
    "bitrate": "5000k",
    "file_path": "output/shot_001_animated.mp4",
    "metadata": {
      "duration": 3.0,
      "resolution": "1920x1080",
      "aspect_ratio": "16:9"
    }
  }
}
```

---

*文档版本：1.0*
*所属阶段：阶段6 - 动画化*
*最后更新：2026-02-02*
