"""
FrameLeap 安装配置
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# 读取版本
version_file = Path(__file__).parent / "app" / "__init__.py"
version_content = version_file.read_text(encoding="utf-8")
version_line = [line for line in version_content.split("\n") if line.startswith("__version__")]
version = version_line[0].split("=")[1].strip().strip('"').strip("'") if version_line else "0.1.0"

setup(
    name="frameleap",
    version=version,
    author="FrameLeap Team",
    description="AI驱动的动态漫自动生成系统",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/FrameLeap",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Video",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=6.0",
        "Pillow>=10.2.0",
        "numpy>=1.24.0",
        "tqdm>=4.66.0",
        "requests>=2.31.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "black>=24.0.0",
            "isort>=5.13.0",
            "mypy>=1.8.0",
        ],
        "llm": [
            "openai>=1.12.0",
            "anthropic>=0.18.0",
        ],
        "image": [
            "diffusers>=0.25.0",
            "transformers>=4.36.0",
            "torch>=2.1.0",
        ],
        "audio": [
            "azure-cognitiveservices-speech>=1.34.0",
            "librosa>=0.10.0",
        ],
        "video": [
            "ffmpeg-python>=0.2.0",
            "moviepy>=1.0.3",
        ],
    },
    entry_points={
        "console_scripts": [
            "frameleap=run:main",
        ],
    },
)
