"""
FrameLeap Web界面

倒树形结构展示生成过程，支持分支和重新生成
"""

from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum
import uuid


class StageStatus(str, Enum):
    """阶段状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageNode:
    """阶段节点"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    stage_name: str = ""
    status: StageStatus = StageStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    output: Optional[dict] = None

    # 分支相关
    parent_id: Optional[str] = None  # 父节点ID
    branch_index: int = 0  # 分支序号
    is_active_branch: bool = True  # 是否是当前激活的分支

    @property
    def duration(self) -> Optional[float]:
        """耗时（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


@dataclass
class GenerationTree:
    """生成树"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    input_text: str = ""
    create_time: datetime = field(default_factory=datetime.now)
    nodes: List[StageNode] = field(default_factory=list)

    # 当前激活的分支路径（从根到叶）
    active_path: List[str] = field(default_factory=list)

    def add_node(self, node: StageNode, parent_id: Optional[str] = None):
        """添加节点"""
        node.parent_id = parent_id
        self.nodes.append(node)

        # 更新激活路径
        if parent_id is None:
            # 根节点
            self.active_path = [node.id]
        elif parent_id == self.active_path[-1]:
            # 继续当前分支
            self.active_path.append(node.id)
        else:
            # 新分支，切换到新分支
            if parent_id in self.active_path:
                idx = self.active_path.index(parent_id)
                self.active_path = self.active_path[:idx+1] + [node.id]

    def get_node(self, node_id: str) -> Optional[StageNode]:
        """获取节点"""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_children(self, parent_id: str) -> List[StageNode]:
        """获取子节点"""
        return [n for n in self.nodes if n.parent_id == parent_id]

    def get_active_nodes(self) -> List[StageNode]:
        """获取当前激活分支的所有节点"""
        return [self.get_node(nid) for nid in self.active_path if self.get_node(nid)]

    def regenerate_branch(self, node_id: str) -> StageNode:
        """从指定节点重新生成（创建新分支）"""
        parent_node = self.get_node(node_id)
        if not parent_node:
            raise ValueError(f"Node not found: {node_id}")

        # 创建新节点
        new_node = StageNode(
            stage_name=parent_node.stage_name,
            status=StageStatus.PENDING,
            parent_id=node_id,
            branch_index=len(self.get_children(node_id)),
        )

        # 标记原节点的分支为非激活
        parent_node.is_active_branch = False

        self.add_node(new_node, node_id)
        return new_node


# 全局存储
_trees: dict[str, GenerationTree] = {}


def create_tree(input_text: str) -> GenerationTree:
    """创建新的生成树"""
    tree = GenerationTree(input_text=input_text)
    _trees[tree.id] = tree

    # 创建输入节点
    input_node = StageNode(stage_name="输入", status=StageStatus.SUCCESS)
    tree.add_node(input_node)
    input_node.start_time = datetime.now()
    input_node.end_time = datetime.now()

    return tree


def get_tree(tree_id: str) -> Optional[GenerationTree]:
    """获取生成树"""
    return _trees.get(tree_id)


def list_trees() -> List[GenerationTree]:
    """列出所有生成树"""
    return list(_trees.values())


# =============================================================================
# FastAPI应用
# =============================================================================

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json

app = FastAPI(title="FrameLeap")


class RegenerateRequest(BaseModel):
    """重新生成请求"""
    tree_id: str
    node_id: str


@app.get("/", response_class=HTMLResponse)
async def index():
    """主页"""
    return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>FrameLeap - 动态漫生成</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: #1a1a2e;
            color: #eee;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 { color: #00d9ff; margin-bottom: 20px; }
        .input-area {
            background: #16213e;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        textarea {
            width: 100%;
            height: 100px;
            background: #0f3460;
            border: 1px solid #00d9ff;
            border-radius: 4px;
            color: #eee;
            padding: 10px;
            font-size: 14px;
            resize: vertical;
        }
        .btn {
            background: #00d9ff;
            color: #1a1a2e;
            border: none;
            padding: 10px 24px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
        }
        .btn:hover { background: #00b8e6; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }

        /* 倒树形结构 */
        .tree-container {
            position: relative;
        }
        .tree {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .level {
            display: flex;
            justify-content: center;
            margin-bottom: 40px;
            position: relative;
        }
        .node {
            background: #16213e;
            border: 2px solid #00d9ff;
            border-radius: 8px;
            padding: 12px 20px;
            min-width: 150px;
            text-align: center;
            position: relative;
            margin: 0 10px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .node:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,217,255,0.3);
        }
        .node.active {
            background: #00d9ff;
            color: #1a1a2e;
        }
        .node.success { border-color: #00ff88; }
        .node.failed { border-color: #ff4444; }
        .node.running {
            border-color: #ffaa00;
            animation: pulse 1s infinite;
        }
        @keyframes pulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(255,170,0,0.4); }
            50% { box-shadow: 0 0 0 8px rgba(255,170,0,0); }
        }
        .node-title { font-weight: 600; margin-bottom: 4px; }
        .node-status { font-size: 12px; opacity: 0.7; }
        .node-time { font-size: 11px; opacity: 0.5; margin-top: 4px; }

        /* 连接线 */
        .connection {
            position: absolute;
            width: 2px;
            background: #00d9ff;
            opacity: 0.3;
        }

        /* 分支标记 */
        .branch-badge {
            position: absolute;
            top: -8px;
            right: -8px;
            background: #ff4444;
            color: white;
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 10px;
        }

        /* 详情面板 */
        .detail-panel {
            background: #16213e;
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
        }
        .detail-panel h3 { margin-bottom: 15px; color: #00d9ff; }
        .detail-content {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .detail-item {
            background: #0f3460;
            padding: 10px;
            border-radius: 4px;
        }
        .detail-label {
            font-size: 12px;
            opacity: 0.6;
            margin-bottom: 4px;
        }
        .detail-value {
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 FrameLeap - 动态漫生成</h1>

        <div class="input-area">
            <textarea id="inputText" placeholder="输入你想要生成的故事...&#10;例如：一个少年在雨夜中遇到了神秘少女"></textarea>
            <div style="margin-top: 15px; display: flex; gap: 10px;">
                <button class="btn" onclick="startGeneration()">🚀 开始生成</button>
                <select id="style" style="padding: 10px; border-radius: 4px; background: #0f3460; color: #eee; border: 1px solid #00d9ff;">
                    <option value="anime">日式动漫</option>
                    <option value="manhwa">韩漫</option>
                    <option value="manhua">国漫</option>
                    <option value="watercolor">水彩风</option>
                </select>
                <select id="resolution" style="padding: 10px; border-radius: 4px; background: #0f3460; color: #eee; border: 1px solid #00d9ff;">
                    <option value="1080p">1080P</option>
                    <option value="1080p_v">1080P竖屏</option>
                    <option value="720p">720P</option>
                </select>
            </div>
        </div>

        <div class="tree-container">
            <div id="tree" class="tree"></div>
        </div>

        <div id="detailPanel" class="detail-panel" style="display: none;">
            <h3>📋 阶段详情</h3>
            <div id="detailContent" class="detail-content"></div>
        </div>
    </div>

    <script>
        let ws = null;
        let currentTreeId = null;

        const stageNames = [
            "输入",
            "剧本生成",
            "画面描述",
            "图像生成",
            "分镜编排",
            "动画化",
            "音频生成",
            "文字字幕",
            "合成渲染",
            "输出交付"
        ];

        function connectWS() {
            ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleUpdate(data);
            };
        }

        function handleUpdate(data) {
            if (data.type === "tree_update") {
                renderTree(data.tree);
            }
        }

        function renderTree(tree) {
            const container = document.getElementById("tree");
            container.innerHTML = "";

            // 按层级分组
            const levels = {};
            tree.nodes.forEach(node => {
                const depth = getDepth(tree, node);
                if (!levels[depth]) levels[depth] = [];
                levels[depth].push(node);
            });

            // 渲染每一层
            Object.keys(levels).sort((a,b) => a-b).forEach(level => {
                const levelDiv = document.createElement("div");
                levelDiv.className = "level";

                levels[level].forEach(node => {
                    const nodeDiv = createNodeElement(node);
                    levelDiv.appendChild(nodeDiv);
                });

                container.appendChild(levelDiv);
            });
        }

        function getDepth(tree, node) {
            let depth = 0;
            let current = node;
            while (current.parent_id) {
                depth++;
                current = tree.nodes.find(n => n.id === current.parent_id);
                if (!current) break;
            }
            return depth;
        }

        function createNodeElement(node) {
            const div = document.createElement("div");
            div.className = `node ${node.status.toLowerCase()}`;
            if (node.is_active_branch) div.classList.add("active");

            div.innerHTML = `
                <div class="node-title">${node.stage_name}</div>
                <div class="node-status">${getStatusText(node.status)}</div>
                ${node.duration ? `<div class="node-time">${node.duration.toFixed(1)}s</div>` : ""}
            `;

            div.onclick = () => showDetail(node);

            return div;
        }

        function getStatusText(status) {
            const texts = {
                "pending": "等待中",
                "running": "处理中",
                "success": "完成",
                "failed": "失败",
                "skipped": "跳过"
            };
            return texts[status] || status;
        }

        function showDetail(node) {
            const panel = document.getElementById("detailPanel");
            const content = document.getElementById("detailContent");
            panel.style.display = "block";

            content.innerHTML = `
                <div class="detail-item">
                    <div class="detail-label">阶段</div>
                    <div class="detail-value">${node.stage_name}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">状态</div>
                    <div class="detail-value">${getStatusText(node.status)}</div>
                </div>
                ${node.duration ? `
                <div class="detail-item">
                    <div class="detail-label">耗时</div>
                    <div class="detail-value">${node.duration.toFixed(2)}秒</div>
                </div>
                ` : ""}
                ${node.error_message ? `
                <div class="detail-item">
                    <div class="detail-label">错误</div>
                    <div class="detail-value" style="color: #ff4444;">${node.error_message}</div>
                </div>
                ` : ""}
                ${node.status === "failed" || node.stage_name === "图像生成" ? `
                <div class="detail-item">
                    <button class="btn" onclick="regenerate('${node.id}')">🔄 重新生成此阶段</button>
                </div>
                ` : ""}
            `;
        }

        async function startGeneration() {
            const text = document.getElementById("inputText").value;
            if (!text.trim()) {
                alert("请输入内容");
                return;
            }

            const btn = document.querySelector(".btn");
            btn.disabled = true;
            btn.textContent = "生成中...";

            try {
                const res = await fetch("/api/generate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        text: text,
                        style: document.getElementById("style").value,
                        resolution: document.getElementById("resolution").value
                    })
                });
                const data = await res.json();
                currentTreeId = data.tree_id;
            } catch (e) {
                alert("启动失败: " + e.message);
            }

            btn.disabled = false;
            btn.textContent = "🚀 开始生成";
        }

        async function regenerate(nodeId) {
            if (!currentTreeId) return;

            try {
                const res = await fetch("/api/regenerate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        tree_id: currentTreeId,
                        node_id: nodeId
                    })
                });
                const data = await res.json();
                if (data.error) {
                    alert(data.error);
                }
            } catch (e) {
                alert("重新生成失败: " + e.message);
            }
        }

        connectWS();
    </script>
</body>
</html>
    """


@app.post("/api/generate")
async def start_generation(request: dict):
    """开始生成"""
    text = request.get("text", "")
    tree = create_tree(text)

    # TODO: 启动后台生成任务
    # 这里应该异步运行生成流程

    return {"tree_id": tree.id}


@app.post("/api/regenerate")
async def regenerate(request: RegenerateRequest):
    """重新生成指定阶段"""
    tree = get_tree(request.tree_id)
    if not tree:
        return {"error": "Tree not found"}

    try:
        new_node = tree.regenerate_branch(request.node_id)
        # TODO: 重新运行该阶段

        return {"success": True, "new_node_id": new_node.id}
    except ValueError as e:
        return {"error": str(e)}


@app.get("/api/trees")
async def list_trees_api():
    """列出所有生成树"""
    trees = list_trees()
    return {
        "trees": [
            {
                "id": t.id,
                "input": t.input_text[:100],
                "create_time": t.create_time.isoformat(),
                "status": t.active_path and t.get_node(t.active_path[-1])?.status
            }
            for t in trees
        ]
    }


@app.get("/api/trees/{tree_id}")
async def get_tree_api(tree_id: str):
    """获取生成树详情"""
    tree = get_tree(tree_id)
    if not tree:
        return {"error": "Tree not found"}

    return {
        "id": tree.id,
        "input": tree.input_text,
        "create_time": tree.create_time.isoformat(),
        "nodes": [
            {
                "id": n.id,
                "stage_name": n.stage_name,
                "status": n.status.value,
                "start_time": n.start_time.isoformat() if n.start_time else None,
                "end_time": n.end_time.isoformat() if n.end_time else None,
                "duration": n.duration,
                "error_message": n.error_message,
                "parent_id": n.parent_id,
                "is_active_branch": n.is_active_branch,
            }
            for n in tree.nodes
        ],
        "active_path": tree.active_path,
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点，推送更新"""
    await websocket.accept()
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()

            if data.get("type") == "subscribe":
                tree_id = data.get("tree_id")
                # TODO: 发送树的更新
                tree = get_tree(tree_id)
                if tree:
                    await websocket.send_json({
                        "type": "tree_update",
                        "tree": {
                            "id": tree.id,
                            "nodes": [
                                {
                                    "id": n.id,
                                    "stage_name": n.stage_name,
                                    "status": n.status.value,
                                    "duration": n.duration,
                                    "parent_id": n.parent_id,
                                    "is_active_branch": n.is_active_branch,
                                }
                                for n in tree.nodes
                            ],
                            "active_path": tree.active_path,
                        }
                    })

    except WebSocketDisconnect:
        pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
