"""
版本控制和分支管理数据模型

支持：
- 历史追溯：每个阶段的制品都可追溯
- 分支创作：从任意节点创建新分支
- 版本对比：比较不同版本的差异
"""

import uuid
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum


# =============================================================================
# 枚举类型
# =============================================================================

class StageType(str, Enum):
    """阶段类型枚举"""
    INPUT = "input"           # 阶段1：输入
    SCRIPT = "script"         # 阶段2：剧本生成
    DESCRIPTION = "description"  # 阶段3：画面描述
    IMAGE = "image"           # 阶段4：图像生成
    STORYBOARD = "storyboard"  # 阶段5：分镜编排
    ANIMATION = "animation"   # 阶段6：动画化
    AUDIO = "audio"           # 阶段7：音频生成
    SUBTITLE = "subtitle"     # 阶段8：文字字幕
    COMPOSE = "compose"       # 阶段9：合成渲染
    OUTPUT = "output"         # 阶段10：输出交付


class NodeType(str, Enum):
    """节点类型枚举"""
    ROOT = "root"             # 根节点
    BRANCH = "branch"         # 分支节点
    LEAF = "leaf"             # 叶节点（最终输出）


class ArtifactStatus(str, Enum):
    """制品状态枚举"""
    PENDING = "pending"       # 等待生成
    GENERATING = "generating" # 生成中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"         # 失败
    CACHED = "cached"         # 使用缓存


# =============================================================================
# 版本节点模型
# =============================================================================

@dataclass
class VersionNode:
    """版本节点

    每个节点代表一个创作状态，包含：
    - 所属项目
    - 父节点（用于追溯）
    - 当前阶段
    - 制品数据
    - 分支信息
    """
    # 基础信息
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""  # 所属项目ID

    # 版本信息
    parent_id: Optional[str] = None  # 父节点ID
    branch_name: str = "main"        # 分支名称
    version: str = "1.0.0"           # 版本号
    commit_message: str = ""         # 提交信息

    # 阶段信息
    stage: StageType = StageType.INPUT
    stage_index: int = 0

    # 制品引用
    artifact_path: Optional[str] = None  # 制品文件路径

    # 状态
    status: ArtifactStatus = ArtifactStatus.PENDING

    # 时间戳
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # 元数据
    metadata: dict = field(default_factory=dict)

    # 输入哈希（用于缓存判断）
    input_hash: Optional[str] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "parent_id": self.parent_id,
            "branch_name": self.branch_name,
            "version": self.version,
            "commit_message": self.commit_message,
            "stage": self.stage.value,
            "stage_index": self.stage_index,
            "artifact_path": self.artifact_path,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
            "input_hash": self.input_hash,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VersionNode":
        """从字典创建"""
        return cls(
            id=data["id"],
            project_id=data["project_id"],
            parent_id=data.get("parent_id"),
            branch_name=data["branch_name"],
            version=data["version"],
            commit_message=data["commit_message"],
            stage=StageType(data["stage"]),
            stage_index=data["stage_index"],
            artifact_path=data.get("artifact_path"),
            status=ArtifactStatus(data["status"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            metadata=data.get("metadata", {}),
            input_hash=data.get("input_hash"),
        )


# =============================================================================
# 制品元数据模型
# =============================================================================

@dataclass
class ArtifactMetadata:
    """制品元数据

    描述制品的详细信息
    """
    # 基础信息
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    node_id: str = ""  # 所属节点
    stage: StageType = StageType.INPUT

    # 文件信息
    artifact_type: str = ""  # 数据类型：script, image, audio, etc.
    file_path: str = ""      # 文件路径
    file_size: int = 0       # 文件大小（字节）

    # 内容摘要
    summary: str = ""        # 内容摘要
    preview_path: Optional[str] = None  # 预览图路径

    # 关联信息
    dependencies: list[str] = field(default_factory=list)  # 依赖的制品ID

    # 时间戳
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "node_id": self.node_id,
            "stage": self.stage.value,
            "artifact_type": self.artifact_type,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "summary": self.summary,
            "preview_path": self.preview_path,
            "dependencies": self.dependencies,
            "created_at": self.created_at,
        }


# =============================================================================
# 项目模型
# =============================================================================

@dataclass
class Project:
    """项目模型

    一个项目包含完整的创作历史和所有分支
    """
    # 基础信息
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""

    # 根节点（项目起点）
    root_node_id: str = ""

    # 当前节点（当前工作位置）
    current_node_id: str = ""

    # 所有节点ID列表（按创建顺序）
    node_ids: list[str] = field(default_factory=list)

    # 分支信息
    branches: dict[str, str] = field(default_factory=dict)  # branch_name -> node_id

    # 设置
    settings: dict = field(default_factory=dict)

    # 时间戳
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def get_main_branch_nodes(self) -> list[str]:
        """获取主分支节点列表"""
        # 从根节点追踪到主分支末端
        result = []
        current = self.root_node_id
        while current:
            result.append(current)
            # 简化：假设主分支名为 "main"
            # 实际需要根据节点数据判断
            break
        return result

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "root_node_id": self.root_node_id,
            "current_node_id": self.current_node_id,
            "node_ids": self.node_ids,
            "branches": self.branches,
            "settings": self.settings,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        """从字典创建"""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            root_node_id=data["root_node_id"],
            current_node_id=data["current_node_id"],
            node_ids=data.get("node_ids", []),
            branches=data.get("branches", {}),
            settings=data.get("settings", {}),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


# =============================================================================
# 分支操作模型
# =============================================================================

@dataclass
class BranchOperation:
    """分支操作记录"""
    # 操作信息
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation_type: str = ""  # create_branch, merge_branch, delete_branch, switch_branch

    # 源和目标
    source_node_id: str = ""
    target_branch: str = ""

    # 操作信息
    operation_message: str = ""

    # 时间戳
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "operation_type": self.operation_type,
            "source_node_id": self.source_node_id,
            "target_branch": self.target_branch,
            "operation_message": self.operation_message,
            "created_at": self.created_at,
        }


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    # 枚举
    "StageType",
    "NodeType",
    "ArtifactStatus",
    # 模型
    "VersionNode",
    "ArtifactMetadata",
    "Project",
    "BranchOperation",
]
