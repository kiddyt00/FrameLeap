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

#### 提示词结构模板

**标准提示词结构**：


**示例拆解**：


#### 主体描述生成

**角色主体Prompt构建**：


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
