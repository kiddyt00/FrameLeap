# FrameLeap 制品存储规范

## 概述

FrameLeap 采用**版本化制品存储**设计，支持：
- **历史追溯** - 每个阶段的制品都可追溯
- **分支创作** - 从任意节点分岔出新的创作路径
- **版本对比** - 查看不同版本的差异
- **空间优化** - 相同内容的制品共享存储

## 存储结构

```
~/FrameLeap/output/projects/{project_id}/
├── project.json              # 项目元数据
├── nodes/                    # 版本节点
│   ├── {node_id}.json        # 节点数据
│   └── ...
├── artifacts/                # 制品文件
│   ├── {artifact_id}/        # 制品目录
│   │   ├── data.json         # 制品数据
│   │   ├── preview.png       # 预览图（如果有）
│   │   ├── meta.json         # 制品元数据
│   │   └── files/            # 附加文件
│   │       └── ...
│   └── _shared/              # 共享制品（内容哈希索引）
│       ├── {hash}/           # 内容寻址存储
│       │   └── ...
└── branches/                 # 分支信息
    ├── main.json             # 主分支头节点
    └── {branch_name}.json    # 其他分支头节点
```

## 版本节点 (VersionNode)

每个节点代表一个创作状态：

```python
@dataclass
class VersionNode:
    id: str                      # 节点唯一ID
    project_id: str              # 所属项目
    parent_id: str | None        # 父节点（追溯历史）
    branch_name: str             # 所属分支
    version: str                 # 版本号
    commit_message: str          # 提交信息

    stage: StageType             # 当前阶段（1-10）
    stage_index: int             # 阶段索引
    artifact_path: str | None    # 关联的制品路径
    status: ArtifactStatus       # 状态

    created_at: str              # 创建时间
    updated_at: str              # 更新时间
    input_hash: str | None       # 输入哈希（缓存判断）
    metadata: dict               # 元数据
```

## 阶段制品清单

| 阶段 | 阶段名称 | 制品类型 | 文件格式 | 持久化 |
|------|---------|---------|---------|--------|
| 1 | 输入阶段 | 输入数据 | JSON | ✅ |
| 2 | 剧本生成 | ScriptData | JSON | ✅ |
| 3 | 画面描述 | SceneData | JSON | ✅ |
| 4 | 图像生成 | 场景图像 | PNG | ✅ |
| 5 | 分镜编排 | TimelineData | JSON | ✅ |
| 6 | 动画化 | 动画数据 | JSON | ✅ |
| 7 | 音频生成 | AudioData | JSON + MP3 | ✅ |
| 8 | 字幕制作 | 字幕数据 | JSON | ✅ |
| 9 | 合成渲染 | 视频数据 | JSON | ✅ |
| 10 | 输出交付 | 最终视频 | MP4 | ✅ |

## 制品元数据 (ArtifactMetadata)

```python
@dataclass
class ArtifactMetadata:
    id: str                      # 制品唯一ID
    node_id: str                 # 所属节点
    stage: StageType             # 所属阶段
    artifact_type: str           # 制品类型

    file_path: str               # 文件路径
    file_size: int               # 文件大小
    summary: str                 # 内容摘要
    preview_path: str | None     # 预览图

    dependencies: list[str]      # 依赖的制品ID
    created_at: str              # 创建时间
```

## 分支管理

### 创建分支

```python
from frameleap.utils import ArtifactStore

store = ArtifactStore(cfg, project_id)

# 从任意节点创建分支
new_node = store.create_branch(
    from_node_id="original_node_id",
    branch_name="alternative_ending",
    commit_message="尝试另一种结局"
)
```

### 查看历史

```python
# 获取节点历史（从根到该节点）
history = store.get_node_history(node_id)
for node in history:
    print(f"{node.stage}: {node.commit_message}")
```

### 切换分支

```python
# 获取分支头节点
head = store.get_branch_head("main")
current_node = store.get_node(head.id)
```

## API 使用示例

### 保存制品

```python
from frameleap.models import ScriptData
from frameleap.models.version import StageType
from frameleap.utils import ArtifactStore

store = ArtifactStore(cfg, project_id)

# 创建节点
node = store.create_node(
    stage=StageType.SCRIPT,
    stage_index=2,
    parent_id=parent_node_id,
    commit_message="生成初始剧本"
)

# 保存制品
metadata = store.save_artifact(
    node_id=node.id,
    stage=StageType.SCRIPT,
    artifact_type="script",
    data=script_data,
    summary="包含5个场景的剧本",
)
```

### 加载制品

```python
# 加载节点
node = store.get_node(node_id)

# 加载制品
data, metadata = store.get_artifact(node.artifact_path)
script_data = ScriptData(**data)
```

## 缓存策略

### 输入哈希

每个节点存储 `input_hash`，用于判断是否可以复用缓存：

```python
# 相同输入哈希 = 可复用制品
if node.input_hash == current_input_hash:
    return store.get_artifact(node.artifact_path)
```

### 内容寻址存储

相同内容的制品只存储一份（`_shared/` 目录）：

```
artifacts/_shared/
├── a1b2c3d4/    # 内容哈希
│   └── actual_file.png
```

## 清理策略

### 未引用制品清理

```python
# 统计引用
ref_count = count_artifact_references(artifact_id)

# 删除未引用的制品
if ref_count == 0:
    cleanup_artifact(artifact_id)
```

### 过期缓存清理

```python
# 清理超过 TTL 的缓存
cleanup_expired_cache(ttl=3600)  # 1小时
```

## Web 界面展示

### 倒树形分支展示

```
                    [根节点]
                       |
          ┌────────────┼────────────┐
          v            v            v
      [分支A]       [分支B]      [分支C]
          |            |            |
      ┌───┴───┐    ┌───┴───┐        |
      v       v    v       v        v
   [A1]    [A2]  [B1]    [B2]     [C1]
```

### 节点状态颜色

- 🟢 `completed` - 已完成
- 🟡 `generating` - 生成中
- 🔴 `failed` - 失败
- ⚪ `pending` - 等待生成
- 🔵 `cached` - 使用缓存

## 数据完整性

### 校验和验证

每个制品存储时计算 SHA-256 哈希：

```python
hash_value = hashlib.sha256(content).hexdigest()
```

### 元数据验证

加载时验证元数据完整性：

```python
assert metadata.file_path.exists()
assert metadata.file_size == file.stat().st_size
```

## 导出导入

### 导出项目

```python
import shutil

# 导出整个项目
shutil.make_archive(
    f"project_{project_id}",
    "zip",
    project_dir
)
```

### 导入项目

```python
shutil.unpack_archive(
    "project_xxx.zip",
    import_dir
)
```

## 性能考虑

### 懒加载

- 节点列表：只加载元数据
- 制品数据：按需加载

### 索引优化

- `node_ids` 列表：快速遍历
- `branches` 字典：快速分支查找
- 内容哈希：快速去重

## 备份建议

1. **定期备份** `projects/` 目录
2. **重要分支** 导出为独立包
3. **制品数据** 使用云存储同步
