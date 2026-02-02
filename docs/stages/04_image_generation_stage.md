# 阶段4：图像生成阶段详细说明

## 1. 概述

图像生成阶段负责将画面描述和提示词转换为实际的静态图像。本阶段使用文生图模型（如Stable Diffusion、Midjourney等）生成高质量的角色和场景图像，并进行后处理以确保角色一致性和画面质量。

---

## 2. 静态图像生成

### 2.1 文生图（Text-to-Image）

#### 模型选择

**主流文生图模型对比**：

| 模型 | 优点 | 缺点 | 适用场景 |
|-----|------|------|---------|
| Stable Diffusion XL | 开源、可控性强、可本地部署 | 需要较强硬件 | 通用推荐 |
| Stable Diffusion 3 | 最新、质量高、文字理解强 | 资源需求大 | 高质量输出 |
| Flux | 快速、质量好 | 闭源 | 快速生成 |
| Midjourney | 质量最高、艺术感强 | API受限、成本高 | 艺术风格 |
| DALL-E 3 | 文字理解最好 | 成本高、限制多 | 复杂描述 |

#### 生成流程

```
提示词 → 模型加载 → 潜空间生成 → 解码 → 后处理 → 质量检查 → 输出
```

#### 批量生成策略

**候选图生成**：
```python
def generate_candidate_images(prompt, num_variants=4):
    """生成多个候选图供选择"""

    candidates = []

    for i in range(num_variants):
        # 使用不同种子
        seed = random.randint(0, 2**32)

        # 略微调整提示词权重
        variant_prompt = adjust_prompt_weights(prompt, variance=0.1)

        # 生成
        image = model.generate(
            prompt=variant_prompt['positive'],
            negative_prompt=variant_prompt['negative'],
            seed=seed,
            **prompt['parameters']
        )

        candidates.append({
            "image": image,
            "seed": seed,
            "variant_id": i
        })

    return candidates
```

### 2.2 角色一致性控制

#### LoRA应用

**LoRA加载与应用**：
```python
def apply_character_lora(model, character_id, weight=0.8):
    """应用角色LoRA以保持角色一致性"""

    lora_path = f"models/loras/character_{character_id}.safetensors"

    # 加载LoRA
    lora = load_lora(model, lora_path)

    # 应用权重
    model = apply_lora_weights(model, lora, weight=weight)

    return model
```

**LoRA权重调优**：
```python
lora_weights = {
    "character_main": 0.8,      # 主角
    "character_supporting": 0.6, # 配角
    "style_manga": 0.5,          # 风格LoRA
    "concept_rain": 0.3          # 特定概念（如雨景）
}
```

#### ControlNet控制

**ControlNet类型与应用**：

| ControlNet类型 | 用途 | 权重建议 |
|---------------|------|---------|
| OpenPose | 控制角色姿态 | 0.8-1.0 |
| Depth | 控制深度/空间关系 | 0.5-0.8 |
| Canny | 控制线条/轮廓 | 0.3-0.6 |
| IP-Adapter | 保持角色特征 | 0.6-0.8 |

**多ControlNet组合**：
```python
def apply_multiple_controlnets(model, controls):
    """应用多个ControlNet"""

    for control in controls:
        cn_type = control['type']
        cn_image = control['image']
        cn_weight = control['weight']

        model = model.apply_controlnet(
            type=cn_type,
            image=cn_image,
            weight=cn_weight
        )

    return model

# 使用示例
controls = [
    {"type": "openpose", "image": pose_reference, "weight": 0.9},
    {"type": "depth", "image": depth_map, "weight": 0.5}
]
```

#### IP-Adapter应用

**IP-Adapter配置**：
```python
def apply_ip_adapter(model, reference_images, weight=0.6):
    """应用IP-Adapter保持角色一致性"""

    # IP-Adapter SDXL
    ip_adapter = load_ip_adapter_model("ip-adapter-sdxl.bin")

    # 处理参考图
    ref_features = extract_clip_features(reference_images)

    # 应用
    model = model.apply_ip_adapter(
        adapter=ip_adapter,
        reference_features=ref_features,
        weight=weight
    )

    return model
```

**多参考图策略**：
```json
{
  "ip_adapter_strategy": {
    "character_consistency": {
      "reference_type": "multi_image",
      "images": [
        "char_front.png",
        "char_side.png",
        "char_expression_1.png"
      ],
      "weight": 0.7
    },
    "style_consistency": {
      "reference_type": "single_image",
      "image": "style_reference.jpg",
      "weight": 0.5
    }
  }
}
```

#### Reference-only模式

**Reference实现**：
```python
def generate_with_reference(model, prompt, reference_image):
    """使用参考图模式生成"""

    # 提取参考图特征
    ref_features = model.extract_features(reference_image)

    # 生成时注入参考特征
    output = model.generate(
        prompt=prompt['positive'],
        negative_prompt=prompt['negative'],
        reference_features=ref_features,
        reference_weight=0.8
    )

    return output
```

### 2.3 多视角生成

#### 视角规划

**视角序列规划**：
```json
{
  "character_shot_sequence": [
    {
      "view": "front",
      "angle": "eye_level",
      "purpose": "establish_character",
      "prompt_mod": "front view portrait, neutral expression"
    },
    {
      "view": "side",
      "angle": "slightly_low",
      "purpose": "character_profile",
      "prompt_mod": "side view, profile"
    },
    {
      "view": "three_quarter",
      "angle": "eye_level",
      "purpose": "dynamic_shot",
      "prompt_mod": "three quarter view, slight smile"
    }
  ]
}
```

#### 连续动作生成

**动作序列生成**：
```python
def generate_action_sequence(character_id, action_description, num_frames=5):
    """生成连续动作图像序列"""

    frames = []

    # 使用OpenPose生成动作序列
    pose_sequence = generate_pose_sequence(action_description, num_frames)

    for i, pose in enumerate(pose_sequence):
        # 构建提示词
        prompt = build_prompt_with_pose(
            character=character_id,
            pose=pose,
            frame_index=i,
            total_frames=num_frames
        )

        # 使用ControlNet生成
        image = model.generate(
            prompt=prompt['positive'],
            negative_prompt=prompt['negative'],
            controlnet={"type": "openpose", "image": pose}
        )

        frames.append(image)

    return frames
```

#### 表情变化序列

**表情序列生成**：
```python
expression_sequence = [
    {"emotion": "neutral", "intensity": 0.0, "duration": 1.0},
    {"emotion": "surprise", "intensity": 0.5, "duration": 0.5},
    {"emotion": "happy", "intensity": 0.8, "duration": 1.5},
    {"emotion": "neutral", "intensity": 0.0, "duration": 1.0}
]

def generate_expression_sequence(character_id, expressions):
    """生成表情变化序列"""

    sequence = []

    for expr in expressions:
        prompt = build_character_prompt(
            character_id,
            expression=expr['emotion'],
            intensity=expr['intensity']
        )

        image = generate_with_consistency(
            prompt=prompt,
            character_lora=character_id,
            ip_adapter_weight=0.7
        )

        sequence.append({
            "image": image,
            "expression": expr['emotion'],
            "duration": expr['duration']
        })

    return sequence
```

---

## 3. 图像后处理

### 3.1 画面增强

#### 超分辨率放大

**超分模型选择**：

| 模型 | 放大倍数 | 特点 | 速度 |
|-----|---------|------|------|
| Real-ESRGAN | 4x | 通用性好 | 快 |
| Real-ESRGAN Anime | 4x | 专门优化动漫 | 快 |
| SwinIR | 4x | 质量高 | 慢 |
| STLVFR | 2-4x | 细节丰富 | 中等 |

**超分处理流程**：
```python
def upscale_image(image, scale_factor=4, model="Real-ESRGAN-Anime"):
    """图像超分辨率放大"""

    # 加载模型
    upsampler = load_upscale_model(model)

    # 执行放大
    upscaled = upsampler.upscale(image, scale=scale_factor)

    return upscaled
```

#### 降噪处理

**降噪策略**：
```python
def denoise_image(image, strength=0.3):
    """图像降噪"""

    # 使用去噪模型或传统方法
    denoised = cv2.fastNlMeansDenoisingColored(
        image,
        None,
        strength*10,
        strength*10,
        7,
        21
    )

    return denoised
```

#### 锐化增强

**锐化处理**：
```python
def sharpen_image(image, amount=1.2):
    """图像锐化"""

    kernel = np.array([
        [-1, -1, -1],
        [-1, 9, -1],
        [-1, -1, -1]
    ]) * amount

    sharpened = cv2.filter2D(image, -1, kernel)

    return sharpened
```

#### 色彩校正

**色彩调整**：
```python
def color_correction(image, target_style="cool"):
    """色彩校正"""

    # 转换到LAB色彩空间
    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)

    # 根据风格调整
    if target_style == "cool":
        lab[:, :, 2] = lab[:, :, 2] * 0.95  # 降低蓝色通道
    elif target_style == "warm":
        lab[:, :, 1] = lab[:, :, 1] * 1.05  # 提高黄色通道

    # 转回RGB
    corrected = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

    return corrected
```

### 3.2 风格统一

#### 滤镜应用

**风格滤镜**：
```python
def apply_style_filter(image, style_config):
    """应用风格滤镜"""

    result = image.copy()

    # 线稿强化
    if style_config.get('strengthen_lines', False):
        result = strengthen_lineart(result, strength=style_config['line_strength'])

    # 色彩调整
    if 'color_adjustment' in style_config:
        result = adjust_colors(result, **style_config['color_adjustment'])

    # 纹理添加
    if 'texture' in style_config:
        result = add_texture(result, style_config['texture'])

    return result
```

#### 色调一致性

**色调映射**：
```python
def unify_color_tone(images, target_tone):
    """统一多张图像的色调"""

    # 计算目标色调统计
    target_stats = calculate_color_stats(target_tone)

    unified_images = []

    for img in images:
        # 调整每张图匹配目标色调
        adjusted = match_color_statistics(img, target_stats)
        unified_images.append(adjusted)

    return unified_images
```

### 3.3 对话气泡预留处理

#### 空白区域检测

**检测算法**：
```python
def find_speech_bubble_area(image, character_position):
    """检测对话气泡可放置区域"""

    # 转换为灰度图
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # 边缘检测
    edges = cv2.Canny(gray, 50, 150)

    # 查找轮廓
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 识别大面积空白区域
    empty_areas = find_empty_regions(contours, min_area=image.size * 0.1)

    # 选择最佳位置（远离角色，构图平衡）
    best_area = select_best_speech_area(empty_areas, character_position)

    return best_area
```

#### 预留框生成

**预留框可视化**：
```python
def create_speech_bubble_placeholder(image, area, opacity=0.3):
    """创建对话气泡预留区域"""

    placeholder = image.copy()

    # 创建半透明白色区域
    overlay = placeholder[area['y']:area['y']+area['height'],
                         area['x']:area['x']+area['width']]
    overlay[:] = (overlay * (1 - opacity) + np.array([255, 255, 255]) * opacity).astype(np.uint8)

    # 添加虚线边框
    cv2.rectangle(placeholder,
                  (area['x'], area['y']),
                  (area['x']+area['width'], area['y']+area['height']),
                  (200, 200, 200), 2, cv2.LINE_AA)

    return placeholder
```

---

## 4. 质量检查与选择

### 4.1 自动质量评分

#### 美学评分模型

**评分维度**：
```python
def calculate_aesthetic_score(image):
    """计算图像美学评分"""

    scores = {}

    # 使用美学评分模型（如LAION Aesthetic Predictor）
    aesthetic_model = load_model("aesthetic_predictor")

    # 1. 整体美学质量 (0-10)
    scores['overall'] = aesthetic_model.predict(image) * 10

    # 2. 构图评分
    scores['composition'] = evaluate_composition(image)

    # 3. 色彩和谐度
    scores['color_harmony'] = evaluate_color_harmony(image)

    # 4. 清晰度
    scores['sharpness'] = evaluate_sharpness(image)

    # 5. 角色相似度（如果有参考）
    if has_reference(image):
        scores['character_similarity'] = compare_with_reference(image)

    # 综合评分
    weights = {
        'overall': 0.4,
        'composition': 0.2,
        'color_harmony': 0.15,
        'sharpness': 0.15,
        'character_similarity': 0.1
    }

    final_score = sum(scores[k] * weights[k] for k in scores)

    return {
        "final_score": final_score,
        "detail_scores": scores
    }
```

#### 构图评估

```python
def evaluate_composition(image):
    """评估构图质量"""

    # 三分法检查
    rule_of_thirds_score = check_rule_of_thirds(image)

    # 焦点位置检查
    focal_point_score = check_focal_point(image)

    # 平衡性检查
    balance_score = check_balance(image)

    return (rule_of_thirds_score + focal_point_score + balance_score) / 3
```

### 4.2 图像筛选

#### 自动筛选流程

```python
def select_best_images(candidates, top_k=1):
    """从候选图中选择最佳图像"""

    # 评分
    scored_candidates = []
    for candidate in candidates:
        scores = calculate_aesthetic_score(candidate['image'])
        candidate['scores'] = scores
        scored_candidates.append(candidate)

    # 排序
    scored_candidates.sort(key=lambda x: x['scores']['final_score'], reverse=True)

    # 返回top-k
    return scored_candidates[:top_k]
```

#### 人工确认模式

```json
{
  "confirmation_mode": "manual",
  "display_options": {
    "layout": "grid",
    "show_scores": true,
    "allow_edit": true,
    "allow_regenerate": true
  },
  "actions": [
    "select",
    "edit_prompt",
    "regenerate",
    "adjust"
  ]
}
```

---

## 5. 输出与存储

### 5.1 图像输出格式

**输出配置**：
```json
{
  "output": {
    "format": "PNG",
    "quality": 100,
    "color_space": "sRGB",
    "metadata": {
      "include_prompt": true,
      "include_parameters": true,
      "include_character_id": true,
      "include_shot_info": true
    }
  }
}
```

### 5.2 文件组织结构

```
output/
├── project_name/
│   ├── 01_characters/
│   │   ├── char_001_amemiya/
│   │   │   ├── reference/
│   │   │   │   ├── front.png
│   │   │   │   ├── side.png
│   │   │   │   └── expressions/
│   │   │   ├── lora/
│   │   │   │   └── char_001_amemiya.safetensors
│   │   │   └── generated/
│   │   │       ├── scene_01_shot_01.png
│   │   │       └── scene_01_shot_02.png
│   │   └── char_002_mystery_girl/
│   ├── 02_backgrounds/
│   │   ├── bg_001_rainy_street.png
│   │   └── bg_002_school_rooftop.png
│   ├── 03_composited/
│   │   ├── scene_01/
│   │   │   ├── shot_01.png
│   │   │   └── shot_02.png
│   │   └── scene_02/
│   └── metadata/
│       ├── characters.json
│       └── generation_log.json
```

---

## 6. 错误处理与重试

### 6.1 常见问题处理

**问题检测与解决方案**：

| 问题 | 检测方法 | 解决方案 |
|-----|---------|---------|
| 角色变形 | 检测身体比例异常 | 重新生成，增加负面提示词 |
| 颜色不一致 | 色彩统计对比 | 调整色彩参数 |
| 多余肢体 | 人体检测模型 | 重新生成，增加bad anatomy权重 |
| 质量低 | 分数低于阈值 | 调整采样参数重新生成 |
| 风格不符 | CLIP相似度检查 | 调整风格LoRA权重 |

### 6.2 自动重试机制

```python
def generate_with_retry(prompt, max_retries=3):
    """带重试的图像生成"""

    for attempt in range(max_retries):
        try:
            # 生成图像
            image = model.generate(**prompt)

            # 质量检查
            score = calculate_aesthetic_score(image)

            if score['final_score'] >= QUALITY_THRESHOLD:
                return {
                    "success": True,
                    "image": image,
                    "score": score,
                    "attempts": attempt + 1
                }
            else:
                # 质量不够，调整参数重试
                prompt = adjust_prompt_for_retry(prompt, attempt)

        except Exception as e:
            log_error(e)
            continue

    return {
        "success": False,
        "error": "Max retries exceeded",
        "best_attempt": best_image_so_far
    }
```

---

*文档版本：1.0*
*所属阶段：阶段4 - 图像生成*
*最后更新：2026-02-02*
