#!/usr/bin/env python3
"""
FrameLeap命令行入口

使用示例:
    python run.py --input "一个少年在雨夜中遇到了神秘少女"
    python run.py --input story.txt --style anime --duration 60
    python run.py --input "..." --resolution 1080p_vertical
"""

import argparse
import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from frameleap import FrameLeapGenerator, Settings
from app.utils import setup_logging


def main():
    parser = argparse.ArgumentParser(
        description="FrameLeap - AI驱动的动态漫自动生成系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --input "一个少年在雨夜中遇到了神秘少女"
  %(prog)s --input story.txt --style anime --duration 60
  %(prog)s --input "..." --resolution 1080p_vertical --output my_video.mp4
        """,
    )

    # 必需参数
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="输入文本或文件路径",
    )

    # 风格参数
    parser.add_argument(
        "-s", "--style",
        choices=["anime", "comic", "manhwa", "manhua", "watercolor", "oil", "pixel", "realistic"],
        default="anime",
        help="艺术风格 (默认: anime)",
    )

    # 视频参数
    parser.add_argument(
        "-d", "--duration",
        type=int,
        help="目标时长（秒）",
    )
    parser.add_argument(
        "-r", "--resolution",
        choices=["1080p", "1080p_vertical", "720p", "4k", "cinema", "square"],
        default="1080p",
        help="输出分辨率 (默认: 1080p)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        choices=[24, 30, 60],
        help="帧率 (默认: 根据分辨率自动选择)",
    )

    # 输出参数
    parser.add_argument(
        "-o", "--output",
        help="输出文件路径",
    )

    # 配置参数
    parser.add_argument(
        "-c", "--config",
        help="配置文件路径 (YAML)",
    )
    parser.add_argument(
        "--work-dir",
        help="工作目录",
    )

    # 其他参数
    parser.add_argument(
        "--debug",
        action="store_true",
        help="调试模式",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="详细输出",
    )

    args = parser.parse_args()

    # 设置日志
    log_level = "DEBUG" if args.debug or args.verbose else "INFO"
    setup_logging(level=log_level)
    logger = setup_logging()

    # 加载配置
    if args.config:
        settings = Settings.from_yaml(args.config)
        logger.info(f"Loaded config from: {args.config}")
    else:
        settings = Settings()

    # 应用命令行参数
    if args.work_dir:
        from app.config import PathConfig
        import tempfile
        settings.paths = PathConfig(
            work_dir=Path(args.work_dir) / "work",
            temp_dir=Path(args.work_dir) / "temp",
            cache_dir=Path(args.work_dir) / "cache",
            model_dir=Path(args.work_dir) / "models",
            output_dir=Path(args.work_dir) / "output",
        )

    settings.video = settings.video.__class__.from_preset(args.resolution)
    if args.fps:
        settings.video.fps = args.fps
    if args.duration:
        settings.video.duration = args.duration
    if args.style:
        settings.style.art_style = args.style
    if args.debug:
        settings.debug = True

    # 创建生成器
    generator = FrameLeapGenerator(settings)

    # 读取输入
    input_path = Path(args.input)
    if input_path.exists() and input_path.is_file():
        logger.info(f"Reading input from file: {args.input}")
        result = generator.generate_from_file(
            input_path,
            style=args.style,
            duration=args.duration,
        )
    else:
        logger.info(f"Using input text: {args.input[:50]}...")
        result = generator.generate(
            input_text=args.input,
            style=args.style,
            duration=args.duration,
        )

    # 处理结果
    if result.success:
        logger.info(f"✓ Generation successful!")
        logger.info(f"  Video: {result.video_path}")
        logger.info(f"  Time: {result.generation_time:.2f}s")

        # 如果指定了输出路径，复制文件
        if args.output and result.video_path:
            import shutil
            shutil.copy2(result.video_path, args.output)
            logger.info(f"  Copied to: {args.output}")
    else:
        logger.error(f"✗ Generation failed: {result.error_message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
