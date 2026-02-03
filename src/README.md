# FrameLeap 源代码

FrameLeap - AI驱动的动态漫自动生成系统

## 目录结构

```
src/
├── frameleap/           # 主包
│   ├── __init__.py     # 包初始化
│   ├── generator.py    # 主生成器
│   ├── config/         # 配置管理
│   ├── models/         # 数据模型
│   ├── stages/         # 处理阶段（10个阶段）
│   └── utils/          # 工具函数
├── tests/              # 测试代码
│   ├── unit/          # 单元测试
│   ├── integration/   # 集成测试
│   └── fixtures/      # 测试夹具
├── scripts/           # 辅助脚本
├── run.py            # 命令行入口
└── requirements.txt  # 依赖列表
```

## 快速开始

### 安装依赖

```bash
cd src
pip install -r requirements.txt
```

### 运行示例

```bash
# 基础使用
python run.py --input "一个少年在雨夜中遇到了神秘少女"

# 指定风格和时长
python run.py --input "..." --style anime --duration 60

# 从文件读取
python run.py --input story.txt --resolution 1080p_vertical
```

### 代码中使用

```python
from frameleap import FrameLeapGenerator

# 初始化生成器
generator = FrameLeapGenerator()

# 生成动态漫
result = generator.generate(
    input_text="一个少年在雨夜中遇到了神秘少女",
    style="anime",
    duration=180,
)

if result.success:
    print(f"视频已生成: {result.video_path}")
```

## 运行测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行特定测试
pytest tests/unit/test_config.py

# 生成覆盖率报告
pytest --cov=frameleap --cov-report=html
```

## 开发指南

### 代码规范

- 使用类型注解
- 编写单元测试
- 遵循PEP 8

### 提交代码

使用项目根目录的自动化提交脚本：

```bash
python git_auto_new.py "feat: 添加xxx功能"
```
