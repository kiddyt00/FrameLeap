# FrameLeap

AI驱动的动态漫自动生成系统。

FrameLeap 是一个端到端的动态漫生成解决方案，从用户的一句话或短文输入出发，自动完成剧本创作、角色设计、画面生成、分镜编排、动画制作、音频合成等全流程，最终输出高质量的动态漫视频作品。

## 核心特性

### 智能创作流程
- **AI剧本生成**：基于LLM的完整剧本创作，包含故事规划、角色设定、分镜脚本
- **角色一致性控制**：使用LoRA、IP-Adapter等技术确保角色跨场景一致
- **智能分镜编排**：自动应用专业影视语言，包括景别选择、运镜设计、节奏控制
- **高质量画面生成**：基于Stable Diffusion等文生图模型的静态图像生成
- **动态效果合成**：运镜动画、角色动画、环境特效、帧插值
- **专业音频制作**：TTS配音、音效生成、BGM匹配、多轨混音

### 视觉叙事专业支持
- **景别叙事功能**：大远景到特写的完整景别体系，配合叙事目的
- **运镜语言**：推进、拉远、平移、旋转等专业运镜实现
- **节奏控制**：快慢节奏、呼吸感设计、高潮处理
- **音画配合**：同步配合、先声后声、声音空间感等专业原则
- **光影叙事**：顺光、侧光、逆光等光影的情感暗示应用
- **色彩心理学**：暖色调、冷色调、高/低对比度的情感联想

## 项目结构

```
FrameLeap/
├── docs/                           # 文档目录
│   ├── README.md                   # 文档导航
│   ├── dynamic_comic_generation_process.md  # 主流程文档
│   └── stages/                     # 阶段详细文档
│       ├── 01_input_stage.md       # 输入阶段
│       ├── 02_script_generation_stage.md    # 剧本生成
│       ├── 03_scene_description_stage.md    # 画面描述
│       ├── 04_image_generation_stage.md     # 图像生成
│       ├── 05_storyboard_stage.md   # 分镜编排
│       ├── 06_animation_stage.md    # 动画化
│       ├── 07_audio_generation_stage.md     # 音频生成
│       ├── 08_text_subtitle_stage.md        # 文字字幕
│       ├── 09_composition_rendering_stage.md # 合成渲染
│       └── 10_output_delivery_stage.md      # 输出交付
├── src/                            # 源代码（待开发）
└── README.md                       # 本文件
```

## 快速开始

### 环境要求

- Python 3.8+
- CUDA 11.0+ (GPU加速)
- 8GB+ VRAM (图像生成)
- 12GB+ VRAM (动画生成)

### 安装

```bash
# 克隆项目
git clone https://github.com/yourusername/FrameLeap.git
cd FrameLeap

# 安装依赖
pip install -r requirements.txt
```

### 使用示例

```python
from frameleap import FrameLeapGenerator

# 初始化生成器
generator = FrameLeapGenerator()

# 一键生成动态漫
result = generator.generate(
    input_text="一个少年在雨夜中遇到了神秘少女",
    style="anime",           # 风格：anime, realistic, watercolor等
    duration=180,            # 目标时长（秒）
    resolution="1920x1080"   # 输出分辨率
)

# 获取结果
result.save("output.mp4")
```

## 文档导航

### 新手入门
1. 阅读 [主流程文档](docs/dynamic_comic_generation_process.md) 了解整体架构
2. 浏览 [阶段文档](docs/stages/) 深入了解各阶段细节

### 按角色查阅

| 角色 | 推荐文档 |
|-----|---------|
| 产品经理 | 主流程文档 + 阶段1 + 阶段10 |
| 后端开发 | 全部阶段文档 |
| AI工程师 | 阶段2 + 阶段3 + 阶段4 + 阶段6 + 阶段7 |
| 前端开发 | 主流程文档 + 阶段1 + 阶段10 |
| 导演/编辑 | 主流程文档 + 术语表 |
| 测试人员 | 各阶段的质量控制部分 |

## 技术栈

| 模块 | 技术选择 |
|-----|---------|
| 语言模型 | GPT-4 / Claude / 本地模型 |
| 图像生成 | Stable Diffusion XL / SD3 / Flux |
| 角色一致性 | LoRA / IP-Adapter / ControlNet |
| 超分辨率 | Real-ESRGAN / SwinIR |
| 动画化 | AnimateDiff / LivePortrait / 运镜算法 |
| 帧插值 | RIFE / DAIN / FILM |
| TTS | Azure TTS / GPT-SoVITS / VITS |
| 音效生成 | AudioLDM / 音效库 |
| 音乐生成 | Suno / Udio / MusicGen |
| 视频处理 | FFmpeg / OpenCV / MoviePy |

## 开发工作流

### 代码提交规范

**重要**：每次对项目进行修改或新增文件后，必须使用自动化提交脚本进行 git 提交。

```bash
# 提交所有更改
python git_auto_new.py "feat: 添加xxx功能"

# 只提交指定文件
python git_auto_new.py "docs: 更新README" -f README.md

# 不推送到远程（仅本地提交）
python git_auto_new.py "wip: 本地保存" --no-push

# 查看脚本帮助
python git_auto_new.py -h
```

### Commit Message 格式

| 类型 | 说明 | 示例 |
|-----|------|------|
| `feat:` | 新功能 | `feat: 添加角色一致性检查模块` |
| `fix:` | 修复bug | `fix: 修复音频同步问题` |
| `docs:` | 文档更新 | `docs: 完善视觉叙事术语表` |
| `refactor:` | 重构 | `refactor: 重构提示词生成器` |
| `opt:` | 优化 | `opt: 优化图像生成速度` |
| `test:` | 测试相关 | `test: 添加分镜编排单元测试` |
| `chore:` | 构建/工具 | `chore: 更新依赖版本` |

## 路线图

### v0.1.0 - 基础功能
- [ ] 基础框架搭建
- [ ] 简单剧本生成
- [ ] 单图像生成
- [ ] 基础分镜编排

### v0.2.0 - 核心功能
- [ ] 角色一致性控制
- [ ] 多图像批量生成
- [ ] 基础动画效果
- [ ] TTS配音

### v0.3.0 - 完整流程
- [ ] 完整10阶段流程
- [ ] 音效与BGM
- [ ] 字幕与对话气泡
- [ ] 视频合成输出

### v0.4.0 - 专业增强
- [ ] 视觉叙事规则引擎
- [ ] 高级运镜系统
- [ ] 节奏智能控制
- [ ] 音画配合优化

### v1.0.0 - 生产就绪
- [ ] 用户界面
- [ ] 批量处理
- [ ] 多平台适配
- [ ] 性能优化

## 贡献指南

欢迎贡献代码、文档或提出建议！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`python git_auto_new.py "feat: 添加xxx功能"`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

*最后更新：2026-02-03*
