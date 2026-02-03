# 阶段3：画面描述生成阶段详细说明

## 1. 概述

画面描述生成阶段负责将剧本中的抽象描述转化为具体的、可直接用于图像生成的视觉描述和提示词。本阶段是连接剧本文字与AI图像生成的关键桥梁。

---

## 2. 场景描述生成

### 2.1 环境描述

#### 环境要素分解

**环境描述模板**：


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


#### 构图自动选择


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


**空间分配计算**：


---

## 3. 提示词（Prompt）工程

### 3.1 图像生成提示词构建

#### 艺术风格库

| 风格 | 英文 | 提示词示例 |
|-----|------|----------|
| 日式漫画 | anime/manga | `anime style, cel shading, clean lines, vibrant colors, manga art` |
| 美式漫画 | comic book | `comic book style, bold lines, heavy shading, muscular, dynamic poses` |
| 韩漫风格 | manhwa | `manhwa style, webtoon format, colorful, delicate lines, digital art` |
| 国漫风格 | manhua | `chinese manhua style, ink wash elements, traditional clothing, elegant` |
| 水彩风 | watercolor | `watercolor painting, soft edges, wash effects, pastel colors, artistic` |
| 油画风 | oil painting | `oil painting, thick brushstrokes, rich colors, textured canvas, classical` |
| 厚涂 | impasto | `impasto technique, heavy texture, palette knife, raised paint surface` |
| 赛璐璐 | cel shading | `cel shading, flat colors, clean outlines, anime style, vibrant` |
| 柔和绘 | soft painting | `soft painting style, dreamy, gentle gradients, pastel colors, ethereal` |
| 像素风 | pixel art | `pixel art, 8-bit, 16-bit, retro game style, limited color palette` |
| 矢量扁平 | flat vector | `flat design, vector art, minimalist, solid colors, clean shapes` |
| 线稿风 | line art | `line art, monoline, sketch, clean lines, black and white` |

#### 渲染风格库

| 风格 | 提示词 |
|-----|--------|
| 2D手绘 | `2D, hand drawn, traditional art, paper texture, slight imperfections` |
| 2.5D轻立体 | `2.5D, semi-3D, subtle depth, layered, isometric elements` |
| 3D渲染 | `3D render, CGI, octane render, unreal engine, volumetric lighting` |
| 2D+3D混合 | `2D character, 3D background, mixed media, hybrid style` |

#### 时代风格库

| 风格 | 提示词 |
|-----|--------|
| 古风中国 | `ancient chinese style, hanfu, traditional architecture, ink elements, elegant` |
| 日式和风 | `japanese style, kimono, cherry blossom, shrine, torii gate, serene` |
| 欧式中世纪 | `medieval european, knight, castle, stone architecture, tavern, fantasy` |
| 赛博朋克 | `cyberpunk, neon lights, futuristic city, holograms, dark atmosphere, rain` |
| 蒸汽朋克 | `steampunk, brass gears, steam power, victorian clothing, goggles, machinery` |
| 废土末世 | `post-apocalyptic, wasteland, ruins, abandoned buildings, desert, survival gear` |
| 现代都市 | `modern city, skyscrapers, street fashion, urban life, contemporary` |

#### 提示词结构模板

**标准提示词结构**：


**示例拆解**：


#### 主体描述生成

**角色主体Prompt构建**：

| 属性 | 描述维度 | 常用选项 |
|-----|---------|---------|
| 年龄 | child, teenager, young adult, middle-aged, elderly | `16 year old`, `teenage girl`, `young man` |
| 性别 | male, female, androgynous | `anime girl`, `young woman`, `boy` |
| 发型 | short, long, messy, sleek, ponytail, twin tails, braided | `short messy black hair`, `long flowing silver hair` |
| 发色 | black, brown, blonde, red, blue, silver, white, pink, green | `silver hair`, `pink highlights`, `raven black` |
| 瞳色 | brown, blue, green, amber, red, heterochromia, golden | `amber eyes`, `heterochromia`, `golden eyes` |
| 瞳孔形状 | normal, cat-like, snake-like, star-shaped | `cat eyes`, `slit pupils` |
| 体型 | slim, athletic, muscular, petite, curvy | `slim build`, `athletic physique` |
| 身高 | tall, average, short | `tall`, `petite`, `average height` |
| 皮肤 | pale, fair, tan, dark | `fair skin`, `pale complexion`, `tan skin` |
| 服装 | school uniform, casual wear, armor, kimono, dress, suit | `black school uniform`, `white dress`, `battle armor` |
| 配饰 | glasses, hairpin, necklace, earrings, ribbon, scarf | `red ribbon`, `round glasses` |
| 表情 | happy, sad, angry, surprised, melancholic, smiling, serious | `melancholic expression`, `gentle smile` |
| 姿态 | standing, sitting, running, jumping, crouching, lying down | `standing pose`, `dynamic action pose` |

#### 主体描述要素库


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

```
环境描述 = [时间] + [天气] + [场景类型] + [场景细节] + [氛围词]
```

#### 场景类型关键词库

| 场景类型 | 关键词 |
|---------|--------|
| 教室 | `classroom, school, desks, chairs, blackboard, windows, chalkboard, school interior` |
| 卧室 | `bedroom, bed, pillow, blanket, wardrobe, desk, lamp, window, cozy, private room` |
| 咖啡馆 | `cafe, coffee shop, tables, chairs, warm lighting, menu, counter, cozy atmosphere` |
| 图书馆 | `library, bookshelves, books, reading tables, quiet, ladder, warm light, knowledge` |
| 医院 | `hospital, hospital room, bed, medical equipment, white walls, sterile, medical interior` |
| 实验室 | `laboratory, lab equipment, computers, screens, blue light, technology, research` |
| 街道 | `street, city street, buildings, sidewalk, streetlights, urban, road, pavement` |
| 公园 | `park, trees, grass, bench, sky, flowers, path, nature, green space` |
| 海边 | `beach, ocean, waves, sand, horizon, seaside, coast, shoreline, water` |
| 山林 | `forest, woods, mountains, trees, path, nature, wilderness, green, sunlight through trees` |
| 沙漠 | `desert, sand dunes, scorching sun, cactus, barren, arid, heat waves` |
| 魔法森林 | `magical forest, enchanted woods, glowing plants, mystical, fantasy forest, luminescent` |
| 天空之城 | `sky city, floating islands, clouds, aerial view, fantasy city, above clouds` |
| 龙之洞穴 | `dragon cave, lava, treasure, rock walls, dark, fiery, dungeon, cave interior` |
| 赛博都市 | `cyberpunk city, neon lights, futuristic, holograms, skyscrapers, dark alley, rain` |
| 太空船 | `spaceship interior, metal, control panel, stars visible through window, sci-fi, technology` |
| 废弃基地 | `abandoned base, ruins, rust, decay, broken structures, desolate, post-apocalyptic` |

#### 时间关键词库

| 时间 | 关键词 | 光影特征 |
|-----|--------|---------|
| 黎明 | `dawn, sunrise, early morning, golden hour, orange sky` | 橙红光线，长阴影 |
| 早晨 | `morning, bright, fresh sunlight, blue sky` | 明亮清新，高对比 |
| 正午 | `noon, midday, overhead sun, harsh shadows` | 顶光，强烈阴影 |
| 下午 | `afternoon, warm sunlight, golden light` | 温暖金色，斜射光 |
| 黄昏 | `dusk, sunset, twilight, orange and purple sky` | 橙紫渐变，柔和光 |
| 夜晚 | `night, nighttime, dark, moonlight, stars` | 暗色调，人工光 |
| 深夜 | `late night, midnight, darkness, silence` | 极暗，稀疏光源 |

#### 天气关键词库

| 天气 | 关键词 | 视觉效果 |
|-----|--------|---------|
| 晴朗 | `sunny, clear sky, bright sunlight, blue sky` | 明亮对比，清晰阴影 |
| 多云 | `cloudy, overcast, clouds covering sky` | 柔和光线，漫反射 |
| 阴天 | `gloomy, dark clouds, overcast sky, gray` | 低对比，灰暗 |
| 雨 | `rain, rainy, raindrops, wet surfaces, puddles` | 反光湿润，模糊 |
| 雪 | `snow, snowy, snowflakes, white ground, winter` | 白色柔和，散射光 |
| 雾 | `fog, mist, foggy, hazy, low visibility` | 朦胧层次，低对比 |
| 风暴 | `storm, thunderstorm, lightning, dark clouds` | 戏剧性，强对比 |

**环境Prompt构建函数**：


### 3.3 风格修饰词

#### 艺术风格库


#### 渲染风格库


### 3.4 质量词与修饰词

#### 质量词库


#### 负面提示词库


### 3.5 SD/MJ专用格式

#### Stable Diffusion格式

**权重标注语法**：


**参数设置**：


#### Midjourney格式

**Midjourney参数**：


### 3.6 提示词生成器

#### 完整Prompt构建


---

## 4. 提示词优化策略

### 4.1 自动优化

**优化检查项**：


### 4.2 提示词A/B测试

**多版本生成**：


---

## 5. 输出格式

### 5.1 图像生成任务格式


---

*文档版本：1.0*
*所属阶段：阶段3 - 画面描述生成*
*最后更新：2026-02-02*
