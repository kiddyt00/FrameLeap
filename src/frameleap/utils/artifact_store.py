"""
制品存储管理器

支持：
- 版本化存储：每个阶段的制品都持久化保存
- 分支管理：从任意节点创建分支
- 历史追溯：查看任意历史版本
- 空间优化：共享相同内容的制品
"""

import json
import shutil
import hashlib
from pathlib import Path
from typing import Optional, Any
from datetime import datetime

from frameleap.models.version import (
    VersionNode, ArtifactMetadata, Project, BranchOperation,
    StageType, ArtifactStatus,
)
from frameleap.models import ScriptData, SceneData, TimelineData, AudioData
from frameleap.config import Config


# =============================================================================
# 制品存储结构
# =============================================================================

"""
存储目录结构：
projects/
├── {project_id}/
│   ├── project.json              # 项目元数据
│   ├── nodes/                    # 版本节点
│   │   ├── {node_id}.json        # 节点数据
│   │   └── ...
│   ├── artifacts/                # 制品文件
│   │   ├── {artifact_id}/        # 制品目录
│   │   │   ├── data.json         # 制品数据
│   │   │   ├── preview.png       # 预览图（如果有）
│   │   │   └── files/            # 附加文件
│   │   │       └── ...
│   │   └── _shared/              # 共享制品（内容哈希索引）
│   │       ├── {hash}/           # 内容寻址存储
│   │       │   └── ...
│   └── branches/                 # 分支信息
│       └── {branch_name}.json    # 分支头节点
"""


# =============================================================================
# 制品存储管理器
# =============================================================================

class ArtifactStore:
    """制品存储管理器

    管理所有制品的持久化存储
    """

    def __init__(self, cfg: Config, project_id: str):
        """初始化存储管理器

        Args:
            cfg: 配置对象
            project_id: 项目ID
        """
        self.cfg = cfg
        self.project_id = project_id

        # 项目目录
        self.project_dir = self.cfg.paths.work_dir / "projects" / project_id
        self.nodes_dir = self.project_dir / "nodes"
        self.artifacts_dir = self.project_dir / "artifacts"
        self.shared_dir = self.artifacts_dir / "_shared"
        self.branches_dir = self.project_dir / "branches"

        # 创建目录
        self._create_directories()

        # 加载或创建项目
        self.project = self._load_or_create_project()

    def _create_directories(self) -> None:
        """创建必要的目录"""
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.nodes_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.shared_dir.mkdir(parents=True, exist_ok=True)
        self.branches_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # 项目管理
    # -------------------------------------------------------------------------

    def _load_or_create_project(self) -> Project:
        """加载或创建项目"""
        project_file = self.project_dir / "project.json"

        if project_file.exists():
            with open(project_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return Project.from_dict(data)
        else:
            # 创建新项目
            project = Project(name=f"Project {self.project_id[:8]}")
            self._save_project(project)
            return project

    def _save_project(self, project: Project) -> None:
        """保存项目"""
        project.updated_at = datetime.now().isoformat()
        project_file = self.project_dir / "project.json"

        with open(project_file, "w", encoding="utf-8") as f:
            json.dump(project.to_dict(), f, ensure_ascii=False, indent=2)

    def save_project_metadata(
        self,
        name: str,
        description: str = "",
    ) -> None:
        """保存项目元数据"""
        self.project.name = name
        self.project.description = description
        self._save_project(self.project)

    # -------------------------------------------------------------------------
    # 节点管理
    # -------------------------------------------------------------------------

    def create_node(
        self,
        stage: StageType,
        stage_index: int,
        parent_id: Optional[str] = None,
        branch_name: str = "main",
        commit_message: str = "",
        input_hash: Optional[str] = None,
        metadata: dict | None = None,
    ) -> VersionNode:
        """创建版本节点

        Args:
            stage: 当前阶段
            stage_index: 阶段索引
            parent_id: 父节点ID
            branch_name: 分支名称
            commit_message: 提交信息
            input_hash: 输入哈希
            metadata: 元数据

        Returns:
            创建的节点
        """
        node = VersionNode(
            project_id=self.project_id,
            parent_id=parent_id,
            branch_name=branch_name,
            commit_message=commit_message,
            stage=stage,
            stage_index=stage_index,
            input_hash=input_hash,
            metadata=metadata or {},
        )

        # 保存节点
        self._save_node(node)

        # 更新项目
        self.project.node_ids.append(node.id)
        if not self.project.root_node_id:
            self.project.root_node_id = node.id
        self.project.current_node_id = node.id
        self.project.branches[branch_name] = node.id
        self._save_project(self.project)

        return node

    def _save_node(self, node: VersionNode) -> None:
        """保存节点"""
        node.updated_at = datetime.now().isoformat()
        node_file = self.nodes_dir / f"{node.id}.json"

        with open(node_file, "w", encoding="utf-8") as f:
            json.dump(node.to_dict(), f, ensure_ascii=False, indent=2)

    def get_node(self, node_id: str) -> Optional[VersionNode]:
        """获取节点"""
        node_file = self.nodes_dir / f"{node_id}.json"

        if not node_file.exists():
            return None

        with open(node_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return VersionNode.from_dict(data)

    def get_node_history(self, node_id: str) -> list[VersionNode]:
        """获取节点历史（从根到该节点）"""
        history = []
        current = self.get_node(node_id)

        while current:
            history.append(current)
            if current.parent_id:
                current = self.get_node(current.parent_id)
            else:
                break

        return list(reversed(history))

    def list_nodes(self, branch_name: str | None = None) -> list[VersionNode]:
        """列出节点

        Args:
            branch_name: 分支名称，None表示所有节点

        Returns:
            节点列表
        """
        if branch_name:
            # 获取分支节点
            head_id = self.project.branches.get(branch_name)
            if not head_id:
                return []
            # 返回从根到分支头的所有节点
            return self.get_node_history(head_id)
        else:
            # 返回所有节点
            nodes = []
            for node_id in self.project.node_ids:
                node = self.get_node(node_id)
                if node:
                    nodes.append(node)
            return nodes

    # -------------------------------------------------------------------------
    # 制品管理
    # -------------------------------------------------------------------------

    def save_artifact(
        self,
        node_id: str,
        stage: StageType,
        artifact_type: str,
        data: Any,
        summary: str = "",
        preview_data: bytes | None = None,
        dependencies: list[str] | None = None,
    ) -> ArtifactMetadata:
        """保存制品

        Args:
            node_id: 节点ID
            stage: 阶段
            artifact_type: 制品类型
            data: 制品数据（可JSON序列化的对象）
            summary: 内容摘要
            preview_data: 预览图数据
            dependencies: 依赖的制品ID

        Returns:
            制品元数据
        """
        import pickle

        # 计算内容哈希
        content_hash = self._compute_hash(data)

        # 创建制品目录
        artifact_id = f"{stage.value}_{artifact_type}_{content_hash[:16]}"
        artifact_dir = self.artifacts_dir / artifact_id
        artifact_dir.mkdir(parents=True, exist_ok=True)

        # 保存制品数据
        data_file = artifact_dir / "data.json"
        if isinstance(data, (ScriptData, SceneData, TimelineData, AudioData)):
            # 数据类对象
            with open(data_file, "w", encoding="utf-8") as f:
                json.dump(data.__dict__, f, ensure_ascii=False, indent=2, default=str)
        else:
            # 其他类型
            with open(data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        # 保存预览图
        preview_path = None
        if preview_data:
            preview_path = str(artifact_dir / "preview.png")
            with open(preview_path, "wb") as f:
                f.write(preview_data)

        # 创建元数据
        metadata = ArtifactMetadata(
            node_id=node_id,
            stage=stage,
            artifact_type=artifact_type,
            file_path=str(data_file),
            file_size=data_file.stat().st_size,
            summary=summary,
            preview_path=preview_path,
            dependencies=dependencies or [],
        )

        # 保存元数据
        meta_file = artifact_dir / "meta.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(metadata.to_dict(), f, ensure_ascii=False, indent=2)

        # 更新节点
        node = self.get_node(node_id)
        if node:
            node.artifact_path = artifact_id
            node.status = ArtifactStatus.COMPLETED
            self._save_node(node)

        return metadata

    def get_artifact(self, artifact_path: str) -> Optional[tuple[Any, ArtifactMetadata]]:
        """获取制品

        Args:
            artifact_path: 制品路径

        Returns:
            (制品数据, 元数据) 或 None
        """
        artifact_dir = self.artifacts_dir / artifact_path
        data_file = artifact_dir / "data.json"
        meta_file = artifact_dir / "meta.json"

        if not data_file.exists() or not meta_file.exists():
            return None

        # 读取数据
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 读取元数据
        with open(meta_file, "r", encoding="utf-8") as f:
            meta_data = json.load(f)
            metadata = ArtifactMetadata(**meta_data)

        return data, metadata

    def _compute_hash(self, data: Any) -> str:
        """计算数据哈希"""
        # 序列化为字符串
        if isinstance(data, (ScriptData, SceneData, TimelineData, AudioData)):
            content = json.dumps(data.__dict__, sort_keys=True, default=str)
        else:
            content = json.dumps(data, sort_keys=True, default=str)

        # 计算哈希
        return hashlib.sha256(content.encode()).hexdigest()

    # -------------------------------------------------------------------------
    # 分支管理
    # -------------------------------------------------------------------------

    def create_branch(
        self,
        from_node_id: str,
        branch_name: str,
        commit_message: str = "",
    ) -> VersionNode:
        """创建分支

        Args:
            from_node_id: 源节点ID
            branch_name: 新分支名称
            commit_message: 提交信息

        Returns:
            新分支的节点
        """
        from_node = self.get_node(from_node_id)
        if not from_node:
            raise ValueError(f"源节点不存在: {from_node_id}")

        # 创建新节点（指向同一制品）
        new_node = VersionNode(
            project_id=self.project_id,
            parent_id=from_node_id,
            branch_name=branch_name,
            commit_message=commit_message,
            stage=from_node.stage,
            stage_index=from_node.stage_index,
            artifact_path=from_node.artifact_path,
            status=from_node.status,
            input_hash=from_node.input_hash,
            metadata=from_node.metadata.copy(),
        )

        # 保存节点
        self._save_node(new_node)

        # 更新项目
        self.project.node_ids.append(new_node.id)
        self.project.branches[branch_name] = new_node.id
        self._save_project(self.project)

        return new_node

    def get_branch_head(self, branch_name: str) -> Optional[VersionNode]:
        """获取分支头节点"""
        head_id = self.project.branches.get(branch_name)
        if not head_id:
            return None
        return self.get_node(head_id)

    def list_branches(self) -> dict[str, str]:
        """列出所有分支"""
        return self.project.branches.copy()

    # -------------------------------------------------------------------------
    # 清理
    # -------------------------------------------------------------------------

    def cleanup_temp_files(self) -> int:
        """清理临时文件"""
        count = 0
        # 简化实现：清理未引用的制品
        # 实际需要引用计数
        return count


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    "ArtifactStore",
]
