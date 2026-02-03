"""
测试模块初始化
"""

import sys
from pathlib import Path

# 添加src目录到路径
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))
