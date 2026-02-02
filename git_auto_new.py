#!/usr/bin/env python3
"""
Git 自动化提交脚本 - 新文件友好版
专门优化对新生成文件的处理

主要功能：
1. 自动检测并添加新文件和修改的文件
2. 提供详细的提交过程反馈
3. 支持指定文件提交
4. 智能处理各种 Git 状态
"""

import os
import sys
import subprocess
import datetime
import argparse
from pathlib import Path


class GitAutoCommit:
    def __init__(self, verbose=False):
        self.project_root = Path.cwd()
        self.verbose = verbose

    def log(self, message):
        """根据详细模式打印日志"""
        if self.verbose:
            print(f"[DEBUG] {message}")

    def run_git_command(self, cmd, exit_on_error=False):
        """执行 Git 命令"""
        self.log(f"执行命令: {cmd}")
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, check=True
            )
            self.log(f"命令输出: {result.stdout[:100] if result.stdout else '无输出'}")
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            error_msg = f"❌ Git命令失败: {cmd}\n   错误: {e.stderr.strip()}"
            if exit_on_error:
                print(error_msg)
                sys.exit(1)
            else:
                return None

    def get_git_status(self):
        """获取详细的 Git 状态"""
        return self.run_git_command("git status --porcelain")

    def get_new_files(self):
        """获取所有新文件（未跟踪文件）"""
        result = self.get_git_status()
        if not result:
            return []

        new_files = []
        for line in result.split('\n'):
            if line.startswith('??'):  # 未跟踪文件
                file_path = line[3:].strip()
                new_files.append(file_path)
        return new_files

    def get_modified_files(self):
        """获取所有修改的文件"""
        result = self.get_git_status()
        if not result:
            return []

        modified_files = []
        for line in result.split('\n'):
            if line and not line.startswith('??'):  # 非新文件
                status = line[:2].strip()
                file_path = line[3:].strip()
                if status:  # M(修改), D(删除), R(重命名)等
                    modified_files.append((status, file_path))
        return modified_files

    def show_git_status(self):
        """显示当前 Git 状态"""
        print("📊 当前工作区状态:")
        self.run_git_command("git status -s")

        new_files = self.get_new_files()
        modified = self.get_modified_files()

        if new_files:
            print(f"\n🆕 未跟踪的新文件 ({len(new_files)} 个):")
            for i, f in enumerate(new_files[:8], 1):
                print(f"  {i:2d}. {f}")
            if len(new_files) > 8:
                print(f"  ... 还有 {len(new_files) - 8} 个文件")

        if modified:
            print(f"\n📝 已修改的文件 ({len(modified)} 个):")
            status_symbols = {
                'M': '修改',
                'D': '删除',
                'R': '重命名',
                'A': '添加',
                'C': '复制'
            }
            for i, (status, file_path) in enumerate(modified[:8], 1):
                status_desc = status_symbols.get(status[0] if status else '?', '未知')
                print(f"  {i:2d}. [{status}] {status_desc}: {file_path}")
            if len(modified) > 8:
                print(f"  ... 还有 {len(modified) - 8} 个文件")

    def smart_add_files(self, specific_files=None, add_all=False):
        """
        智能添加文件

        Args:
            specific_files: 指定要添加的文件列表
            add_all: 是否添加所有文件（覆盖 specific_files）
        """
        if add_all or not specific_files:
            # 添加所有更改
            print("📦 添加所有更改到暂存区...")
            self.run_git_command("git add .", exit_on_error=True)
        elif specific_files:
            # 添加指定文件
            added_count = 0
            for file_pattern in specific_files:
                print(f"📄 添加文件模式: {file_pattern}")
                result = self.run_git_command(f"git add {file_pattern}")
                if result is not None:
                    added_count += 1

            if added_count == 0:
                print("⚠️  没有找到匹配的文件")
                return False

        # 显示添加结果
        status_after = self.get_git_status()
        if status_after:
            staged_files = [line for line in status_after.split('\n')
                            if line and not line.startswith('??') and not line.startswith(' ')]
            if staged_files:
                print(f"✅ 已暂存 {len(staged_files)} 个文件")
                if self.verbose:
                    for f in staged_files[:5]:
                        print(f"  - {f[3:]}")
        else:
            print("✅ 所有更改已暂存")

        return True

    def auto_commit(self, message, specific_files=None, add_all=True,
                    push=True, branch="main", skip_status=False):
        """
        自动化提交主函数

        Args:
            message: 提交信息
            specific_files: 指定要添加的文件
            add_all: 是否添加所有文件
            push: 是否推送到远程
            branch: 目标分支
            skip_status: 跳过状态显示
        """
        print(f"\n{'=' * 60}")
        print(f"🚀 Git 自动化提交")
        print(f"📅 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'=' * 60}")

        # 检查是否在 Git 仓库
        if not os.path.exists(".git"):
            print("❌ 错误：当前目录不是 Git 仓库")
            sys.exit(1)

        # 显示当前状态
        if not skip_status:
            self.show_git_status()

        # 检查是否有更改
        status = self.get_git_status()
        if not status:
            print("\n✅ 工作区干净，没有需要提交的更改")
            return True

        print(f"\n💡 提交信息: \"{message}\"")

        # 智能添加文件
        if not self.smart_add_files(specific_files, add_all):
            print("❌ 添加文件失败，终止提交")
            return False

        # 提交
        print(f"\n💾 正在提交更改...")
        commit_result = self.run_git_command(f'git commit -m "{message}"', exit_on_error=True)
        if commit_result:
            # 提取提交哈希
            lines = commit_result.split('\n')
            for line in lines:
                if line.startswith('['):
                    print(f"✅ {line}")
                    break

        # 推送到远程
        if push:
            print(f"\n🚀 正在推送到远程分支 '{branch}'...")
            push_result = self.run_git_command(f"git push origin {branch}", exit_on_error=True)
            if push_result:
                print("✅ 推送成功！")

        # 显示提交历史
        print(f"\n📋 最近提交记录:")
        self.run_git_command("git log --oneline -3 --graph --decorate")

        print(f"\n✨ 提交流程完成！")
        return True


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="Git 自动化提交工具 - 专门优化对新文件的处理",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 基本使用 - 提交所有更改
  %(prog)s "修复了视频渲染的bug"

  # 只提交指定文件
  %(prog)s "更新配置文件" -f config.yaml settings.ini

  # 只提交特定类型的文件
  %(prog)s "更新Python代码" -f "*.py" "utils/*.py"

  # 不推送到远程（仅本地提交）
  %(prog)s "本地保存" --no-push

  # 推送到特定分支
  %(prog)s "功能更新" -b develop

  # 详细模式
  %(prog)s "调试提交" -v

  # 只显示状态，不提交
  %(prog)s --status-only

  # 交互式添加（手动选择文件）
  %(prog)s "选择性提交" --interactive

高级功能:
  • 自动检测新文件和修改的文件
  • 支持文件通配符模式
  • 详细的提交过程反馈
  • 分支管理支持
  • 详细调试模式
        """
    )

    # 必需参数
    parser.add_argument(
        "message",
        nargs="?",  # 改为可选，与 --status-only 配合
        help="提交信息（用引号括起来）"
    )

    # 文件相关选项
    file_group = parser.add_argument_group("文件选择选项")
    file_group.add_argument(
        "-f", "--files",
        nargs="+",
        metavar="FILE",
        help="指定要提交的文件（支持通配符）"
    )
    file_group.add_argument(
        "-a", "--add-all",
        action="store_true",
        default=True,
        help="添加所有更改的文件（默认）"
    )
    file_group.add_argument(
        "--no-add-all",
        action="store_false",
        dest="add_all",
        help="不自动添加所有文件，需与 --files 一起使用"
    )

    # 提交选项
    commit_group = parser.add_argument_group("提交选项")
    commit_group.add_argument(
        "-b", "--branch",
        default="main",
        help="目标分支（默认: main）"
    )
    commit_group.add_argument(
        "--no-push",
        action="store_false",
        dest="push",
        default=True,
        help="只提交到本地，不推送到远程"
    )

    # 信息显示选项
    info_group = parser.add_argument_group("信息显示选项")
    info_group.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="详细模式，显示更多调试信息"
    )
    info_group.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="安静模式，只显示关键信息"
    )
    info_group.add_argument(
        "--status-only",
        action="store_true",
        help="只显示Git状态，不执行提交"
    )
    info_group.add_argument(
        "--skip-status",
        action="store_true",
        help="跳过状态显示，直接提交"
    )

    # 特殊功能
    advanced_group = parser.add_argument_group("高级功能")
    advanced_group.add_argument(
        "--interactive",
        action="store_true",
        help="交互式添加文件（需要 git 2.20+）"
    )
    advanced_group.add_argument(
        "--amend",
        action="store_true",
        help="修正上一次提交"
    )

    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    # 检查参数组合
    if not args.message and not args.status_only:
        parser.print_help()
        print(f"\n{'!' * 60}")
        print("错误：需要提交信息或 --status-only 参数")
        print("示例: git_auto_new.py \"提交信息\"")
        print("示例: git_auto_new.py --status-only")
        print(f"{'!' * 60}")
        sys.exit(1)

    if args.status_only:
        # 只显示状态模式
        git = GitAutoCommit(verbose=args.verbose)
        git.show_git_status()
        sys.exit(0)

    if getattr(args, 'no_add_all', False) and not args.files:
        print("❌ 错误：使用 --no-add-all 时必须指定 --files")
        sys.exit(1)

    # 创建 Git 实例
    git = GitAutoCommit(verbose=args.verbose)

    # 处理交互式添加
    if args.interactive:
        print("🔍 交互式添加模式...")
        os.system("git add -i")
        args.add_all = False
        args.files = None

    # 处理修正提交
    commit_message = args.message
    if args.amend:
        print("✏️  修正上一次提交...")
        commit_message = f"amend: {commit_message}"
        os.system(f'git commit --amend -m "{commit_message}"')
        if args.push:
            os.system(f"git push --force-with-lease origin {args.branch}")
        sys.exit(0)

    # 执行自动化提交
    try:
        success = git.auto_commit(
            message=commit_message,
            specific_files=args.files,
            add_all=args.add_all,
            push=args.push,
            branch=args.branch,
            skip_status=args.skip_status
        )

        if success:
            sys.exit(0)
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断，操作已取消")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()