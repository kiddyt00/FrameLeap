"""
FrameLeap Web界面

完整展示10阶段生成流程，支持逐步展示和重新生成
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import uuid
import asyncio
import json


class StageStatus(str, Enum):
    """阶段状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


# 阶段定义 - 完整10阶段流程
STAGE_DEFINITIONS = {
    "input": {
        "id": "input",
        "name": "📥 输入处理",
        "description": "处理用户输入文本，获取风格配置",
        "icon": "📥",
        "color": "#6c757d",
        "details": ["预处理文本", "获取风格配置", "验证输入"]
    },
    "script": {
        "id": "script",
        "name": "📜 剧本生成",
        "description": "分析文本，生成剧本结构和角色",
        "icon": "📜",
        "color": "#4facfe",
        "details": ["分析输入文本", "推断故事类型", "提取主题", "解析场景(三幕式)", "解析角色", "计算节奏点"],
        "outputs": ["故事类型", "场景列表", "角色数据", "节奏曲线"]
    },
    "scene_desc": {
        "id": "scene_desc",
        "name": "🎨 画面描述",
        "description": "为每个场景生成图像生成提示词",
        "icon": "🎨",
        "color": "#00f2fe",
        "details": ["提取场景描述", "生成正向提示词", "生成负面提示词"],
        "outputs": ["提示词(prompt)", "负面提示词(negative_prompt)"]
    },
    "image": {
        "id": "image",
        "name": "🖼️ 图像生成",
        "description": "调用API生成场景图像",
        "icon": "🖼️",
        "color": "#43e97b",
        "details": ["创建图像API实例", "调用API生成图像", "保存图像文件"],
        "outputs": ["场景图像文件"]
    },
    "storyboard": {
        "id": "storyboard",
        "name": "🎬 分镜编排",
        "description": "编排镜头顺序和时间轴",
        "icon": "🎬",
        "color": "#fa709a",
        "details": ["计算时间范围", "选择景别", "创建镜头数据"],
        "outputs": ["时间轴", "镜头列表"]
    },
    "animation": {
        "id": "animation",
        "name": "🎭 动画化",
        "description": "添加运镜和动画效果",
        "icon": "🎭",
        "color": "#fee140",
        "details": ["运镜动画", "角色动画", "环境特效", "帧插值"],
        "outputs": ["动画帧序列"]
    },
    "audio": {
        "id": "audio",
        "name": "🔊 音频生成",
        "description": "生成配音、音效和BGM",
        "icon": "🔊",
        "color": "#a8edea",
        "details": ["TTS配音", "音效生成", "BGM匹配", "多轨混音"],
        "outputs": ["音频文件"]
    },
    "text": {
        "id": "text",
        "name": "💬 文字字幕",
        "description": "生成字幕和对话气泡",
        "icon": "💬",
        "color": "#ff6b6b",
        "details": ["生成字幕时间轴", "生成对话气泡位置"],
        "outputs": ["字幕数据", "气泡位置"]
    },
    "compose": {
        "id": "compose",
        "name": "🎞️ 合成渲染",
        "description": "合成动画、音频和字幕",
        "icon": "🎞️",
        "color": "#f093fb",
        "details": ["使用FFmpeg/MoviePy合成"],
        "outputs": ["视频文件"]
    },
    "output": {
        "id": "output",
        "name": "📤 输出交付",
        "description": "输出最终视频文件",
        "icon": "📤",
        "color": "#4facfe",
        "details": ["复制到输出目录"],
        "outputs": ["output.mp4"]
    },
}


@dataclass
class StageNode:
    """阶段节点"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    stage_id: str = ""  # 阶段ID (如 script, image 等)
    stage_name: str = ""
    status: StageStatus = StageStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    output: Optional[Dict[str, Any]] = None
    progress: float = 0.0  # 进度 0-1

    @property
    def duration(self) -> Optional[float]:
        """耗时（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


@dataclass
class GenerationSession:
    """生成会话"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    input_text: str = ""
    style: str = "anime"
    resolution: str = "1080p"
    create_time: datetime = field(default_factory=datetime.now)
    nodes: Dict[str, StageNode] = field(default_factory=dict)  # stage_id -> StageNode

    def get_node(self, stage_id: str) -> Optional[StageNode]:
        """获取阶段节点"""
        return self.nodes.get(stage_id)

    def set_node(self, stage_id: str, node: StageNode):
        """设置阶段节点"""
        self.nodes[stage_id] = node

    def get_progress(self) -> float:
        """获取整体进度"""
        if not self.nodes:
            return 0.0
        total = len(STAGE_DEFINITIONS)
        completed = sum(1 for n in self.nodes.values() if n.status == StageStatus.SUCCESS)
        return completed / total


# 全局存储
_sessions: dict[str, GenerationSession] = {}


def create_session(input_text: str, style: str = "anime", resolution: str = "1080p") -> GenerationSession:
    """创建新的生成会话"""
    session = GenerationSession(
        input_text=input_text,
        style=style,
        resolution=resolution
    )
    _sessions[session.id] = session

    # 初始化所有阶段节点
    for stage_id, stage_def in STAGE_DEFINITIONS.items():
        node = StageNode(
            stage_id=stage_id,
            stage_name=stage_def["name"],
            status=StageStatus.PENDING
        )
        session.set_node(stage_id, node)

    # 输入阶段直接完成
    input_node = session.get_node("input")
    input_node.status = StageStatus.SUCCESS
    input_node.start_time = datetime.now()
    input_node.end_time = datetime.now()

    return session


def get_session(session_id: str) -> Optional[GenerationSession]:
    """获取生成会话"""
    return _sessions.get(session_id)


def list_sessions() -> List[GenerationSession]:
    """列出所有生成会话"""
    return list(_sessions.values())


# =============================================================================
# WebSocket 连接管理
# =============================================================================

class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def broadcast_to_session(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)

            # 清理断开的连接
            for conn in disconnected:
                self.disconnect(conn, session_id)


manager = ConnectionManager()


# =============================================================================
# 后台生成任务
# =============================================================================

async def run_generation_task(session_id: str):
    """
    后台运行生成任务

    执行完整的10阶段流程，并通过 WebSocket 推送进度更新
    """
    session = get_session(session_id)
    if not session:
        return

    # 阶段执行顺序映射
    stage_order = ["input", "script", "scene_desc", "image", "storyboard",
                   "animation", "audio", "text", "compose", "output"]

    # 阶段名称映射
    stage_names = {
        "input": "输入处理",
        "script": "剧本生成",
        "scene_desc": "画面描述",
        "image": "图像生成",
        "storyboard": "分镜编排",
        "animation": "动画化",
        "audio": "音频生成",
        "text": "文字字幕",
        "compose": "合成渲染",
        "output": "输出交付"
    }

    try:
        # 导入 Generator
        from app.generator import Generator
        from app.config import config

        # 创建进度回调
        async def progress_callback(stage_name: str, progress: float):
            """进度回调 - 更新当前阶段状态"""
            # 找到对应的 stage_id
            stage_id = None
            for sid, sname in stage_names.items():
                if sname == stage_name:
                    stage_id = sid
                    break

            if stage_id:
                node = session.get_node(stage_id)
                if node:
                    node.status = StageStatus.RUNNING
                    node.progress = progress
                    if node.start_time is None:
                        node.start_time = datetime.now()

                    # 推送更新
                    await manager.broadcast_to_session(session_id, {
                        "type": "stage_update",
                        "stage_id": stage_id,
                        "status": "running",
                        "progress": progress
                    })

        # 创建错误回调
        async def error_callback(error: Exception):
            """错误回调"""
            await manager.broadcast_to_session(session_id, {
                "type": "error",
                "error": str(error)
            })

        # 创建生成器
        generator = Generator(cfg=config)

        # 包装回调为异步
        def sync_progress_callback(stage_name: str, progress: float):
            asyncio.create_task(progress_callback(stage_name, progress))

        def sync_error_callback(error: Exception):
            asyncio.create_task(error_callback(error))

        generator._progress_callback = sync_progress_callback
        generator._error_callback = sync_error_callback

        # 执行生成
        result = generator.generate(
            text=session.input_text,
            style=session.style,
            resolution=session.resolution
        )

        # 更新所有阶段状态
        for i, stage_id in enumerate(stage_order):
            node = session.get_node(stage_id)
            if node:
                if result.success:
                    node.status = StageStatus.SUCCESS
                    node.end_time = datetime.now()
                    if node.start_time is None:
                        node.start_time = node.end_time

                    # 收集输出数据
                    if result.script and stage_id == "script":
                        node.output = {
                            "story_type": result.script.story_type.value if hasattr(result.script.story_type, 'value') else str(result.script.story_type),
                            "theme": result.script.theme,
                            "scene_count": len(result.script.scenes),
                            "characters": list(result.script.characters.keys()) if result.script.characters else []
                        }
                    elif result.images and stage_id == "image":
                        node.output = {"image_paths": result.images}

                    # 推送更新
                    await manager.broadcast_to_session(session_id, {
                        "type": "stage_update",
                        "stage_id": stage_id,
                        "status": "success",
                        "output": node.output,
                        "duration": node.duration
                    })
                else:
                    node.status = StageStatus.FAILED
                    node.error_message = result.error_message
                    node.end_time = datetime.now()

                    await manager.broadcast_to_session(session_id, {
                        "type": "stage_update",
                        "stage_id": stage_id,
                        "status": "failed",
                        "error": result.error_message,
                        "duration": node.duration
                    })

        # 发送完成消息
        if result.success:
            await manager.broadcast_to_session(session_id, {
                "type": "complete",
                "output_path": result.video_path,
                "generation_time": result.generation_time
            })
        else:
            await manager.broadcast_to_session(session_id, {
                "type": "error",
                "error": result.error_message
            })

    except Exception as e:
        # 标记当前运行中的阶段为失败
        for stage_id in stage_order:
            node = session.get_node(stage_id)
            if node and node.status == StageStatus.RUNNING:
                node.status = StageStatus.FAILED
                node.error_message = str(e)
                node.end_time = datetime.now()

        await manager.broadcast_to_session(session_id, {
            "type": "error",
            "error": f"生成失败: {str(e)}"
        })


# =============================================================================
# FastAPI应用
# =============================================================================

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(title="FrameLeap")


class GenerateRequest(BaseModel):
    """生成请求"""
    text: str
    style: str = "anime"
    resolution: str = "1080p"


class RegenerateRequest(BaseModel):
    """重新生成请求"""
    session_id: str
    stage_id: str


@app.get("/", response_class=HTMLResponse)
async def index():
    """主页"""
    import json

    # 将阶段定义转换为JSON字符串注入到页面
    stages_json = json.dumps(STAGE_DEFINITIONS, ensure_ascii=False)

    # 读取HTML模板并替换占位符
    html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FrameLeap - 动态漫生成</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f8fafc;
            color: #1e293b;
            min-height: 100vh;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        /* 标题 */
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 30px 0;
            background: linear-gradient(135deg, #2563eb 0%, #3b82f6 50%, #06b6d4 100%);
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(37, 99, 235, 0.15);
        }
        .header h1 {
            color: #ffffff;
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        .header p {
            color: rgba(255, 255, 255, 0.9);
            font-size: 1.1em;
        }

        /* 输入区域 */
        .input-section {
            background: #ffffff;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 10px 40px rgba(0, 0, 0, 0.05);
        }
        .input-group {
            margin-bottom: 15px;
        }
        .input-group label {
            display: block;
            margin-bottom: 10px;
            color: #334155;
            font-weight: 600;
            font-size: 14px;
        }
        textarea {
            width: 100%;
            height: 120px;
            background: #f8fafc;
            border: 1px solid #cbd5e1;
            border-radius: 10px;
            color: #1e293b;
            padding: 16px;
            font-size: 14px;
            resize: vertical;
            transition: all 0.2s;
            font-family: inherit;
        }
        textarea:focus {
            outline: none;
            border-color: #2563eb;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
            background: #ffffff;
        }
        .controls {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            margin-top: 20px;
        }
        select {
            flex: 1;
            min-width: 150px;
            padding: 12px 16px;
            border-radius: 10px;
            background: #f8fafc;
            color: #334155;
            border: 1px solid #cbd5e1;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
        }
        select:hover {
            border-color: #94a3b8;
        }
        select:focus {
            outline: none;
            border-color: #2563eb;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }
        .btn {
            padding: 12px 32px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 15px;
            font-weight: 600;
            transition: all 0.2s;
        }
        .btn-primary {
            background: linear-gradient(135deg, #2563eb, #3b82f6);
            color: #ffffff;
            box-shadow: 0 2px 10px rgba(37, 99, 235, 0.2);
        }
        .btn-primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
            background: linear-gradient(135deg, #1d4ed8, #2563eb);
        }
        .btn-primary:active {
            transform: translateY(0);
        }
        .btn-primary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
            background: #94a3b8;
        }

        /* 进度条 */
        .progress-section {
            background: #ffffff;
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 30px;
            display: none;
            border: 1px solid #e2e8f0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        .progress-section.active {
            display: block;
        }
        .progress-bar-container {
            height: 10px;
            background: #f1f5f9;
            border-radius: 5px;
            overflow: hidden;
            margin-bottom: 12px;
        }
        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #2563eb, #3b82f6, #06b6d4);
            border-radius: 5px;
            transition: width 0.4s ease;
            width: 0%;
            position: relative;
        }
        .progress-bar::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            animation: shimmer 1.5s infinite;
        }
        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        .progress-text {
            text-align: center;
            color: #64748b;
            font-size: 14px;
            font-weight: 500;
        }

        /* 流程树 */
        .flow-section {
            display: none;
        }
        .flow-section.active {
            display: block;
        }
        .flow-title {
            color: #1e293b;
            font-size: 1.5em;
            margin-bottom: 25px;
            font-weight: 700;
        }

        /* 阶段卡片 */
        .stages-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
        }
        .stage-card {
            background: #ffffff;
            border-radius: 14px;
            padding: 22px;
            border: 2px solid #e2e8f0;
            transition: all 0.25s;
            cursor: pointer;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        .stage-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }
        .stage-card.pending {
            border-color: #cbd5e1;
            background: #f8fafc;
        }
        .stage-card.running {
            border-color: #f59e0b;
            box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.1);
            animation: pulse-card 2s infinite;
        }
        .stage-card.success {
            border-color: #10b981;
            background: linear-gradient(135deg, #ffffff 0%, #f0fdf4 100%);
        }
        .stage-card.failed {
            border-color: #ef4444;
            background: linear-gradient(135deg, #ffffff 0%, #fef2f2 100%);
        }
        @keyframes pulse-card {
            0%, 100% { box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.1); }
            50% { box-shadow: 0 0 0 6px rgba(245, 158, 11, 0.05); }
        }

        .stage-header {
            display: flex;
            align-items: center;
            margin-bottom: 14px;
        }
        .stage-icon {
            font-size: 24px;
            margin-right: 12px;
        }
        .stage-name {
            font-weight: 600;
            font-size: 16px;
            flex: 1;
            color: #1e293b;
        }
        .stage-status {
            font-size: 12px;
            padding: 5px 12px;
            border-radius: 20px;
            font-weight: 600;
        }
        .status-pending { background: #f1f5f9; color: #64748b; }
        .status-running { background: #fef3c7; color: #d97706; }
        .status-success { background: #d1fae5; color: #059669; }
        .status-failed { background: #fee2e2; color: #dc2626; }

        .stage-description {
            color: #64748b;
            font-size: 13px;
            margin-bottom: 16px;
            line-height: 1.6;
        }

        .stage-details {
            border-top: 1px solid #f1f5f9;
            padding-top: 16px;
        }
        .detail-item {
            display: flex;
            align-items: center;
            margin-bottom: 8px;
            font-size: 13px;
            color: #64748b;
        }
        .detail-item:before {
            content: "→";
            margin-right: 10px;
            color: #2563eb;
            font-weight: bold;
        }
        .detail-item.done {
            color: #059669;
        }
        .detail-item.done:before {
            content: "✓";
            color: #059669;
        }

        .stage-outputs {
            margin-top: 14px;
            padding-top: 14px;
            border-top: 1px solid #f1f5f9;
        }
        .output-tag {
            display: inline-block;
            background: #eff6ff;
            color: #2563eb;
            padding: 5px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 500;
            margin-right: 8px;
            margin-bottom: 8px;
        }

        .stage-time {
            margin-top: 14px;
            font-size: 12px;
            color: #94a3b8;
        }

        /* 详情弹窗 */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(4px);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        .modal.active {
            display: flex;
        }
        .modal-content {
            background: #ffffff;
            border-radius: 20px;
            padding: 35px;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
        }
        .modal-title {
            color: #1e293b;
            font-size: 1.5em;
            margin-bottom: 25px;
            font-weight: 700;
        }
        .modal-close {
            float: right;
            cursor: pointer;
            font-size: 28px;
            color: #94a3b8;
            transition: color 0.2s;
        }
        .modal-close:hover {
            color: #475569;
        }
        .detail-row {
            display: flex;
            margin-bottom: 18px;
        }
        .detail-label {
            width: 120px;
            color: #64748b;
            font-weight: 500;
        }
        .detail-value {
            flex: 1;
            color: #1e293b;
        }
        .prompt-box {
            background: #f8fafc;
            padding: 18px;
            border-radius: 10px;
            margin: 18px 0;
            font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
            font-size: 13px;
            line-height: 1.7;
            max-height: 200px;
            overflow-y: auto;
            color: #334155;
            border: 1px solid #e2e8f0;
        }
        .prompt-label {
            color: #2563eb;
            margin-bottom: 10px;
            font-weight: 600;
        }

        /* 树形连接线 */
        .tree-connector {
            display: none;
        }

        /* 响应式 */
        @media (max-width: 768px) {
            .stages-container {
                grid-template-columns: 1fr;
            }
            .controls {
                flex-direction: column;
            }
            select, .btn {
                width: 100%;
            }
            .header {
                padding: 20px 0;
            }
            .header h1 {
                font-size: 1.8em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 FrameLeap</h1>
            <p>AI驱动的动态漫自动生成系统</p>
        </div>

        <!-- 输入区域 -->
        <div class="input-section">
            <div class="input-group">
                <label>📝 输入你的故事</label>
                <textarea id="inputText" placeholder="输入你想要生成的故事...&#10;&#10;例如：&#10;一个少年在雨夜中遇到了神秘少女。少女告诉他，他是被选中的勇者，必须拯救即将崩塌的世界。&#10;&#10;或者只输入一句话：&#10;一个少年在雨夜中遇到了神秘少女"></textarea>
            </div>
            <div class="controls">
                <select id="style">
                    <option value="anime">🎨 日式动漫</option>
                    <option value="manhwa">📖 韩漫</option>
                    <option value="manhua">🏮 国漫</option>
                    <option value="watercolor">🎨 水彩风</option>
                    <option value="oil">🖼️ 油画风</option>
                    <option value="pixel">👾 像素风</option>
                    <option value="realistic">📷 写实风</option>
                </select>
                <select id="resolution">
                    <option value="1080p">📺 1080P 横屏</option>
                    <option value="1080p_v">📱 1080P 竖屏</option>
                    <option value="720p">📺 720P</option>
                    <option value="4k">🎬 4K</option>
                </select>
                <button class="btn btn-primary" id="generateBtn" onclick="startGeneration()">
                    🚀 开始生成
                </button>
            </div>
        </div>

        <!-- 进度区域 -->
        <div class="progress-section" id="progressSection">
            <div class="progress-bar-container">
                <div class="progress-bar" id="progressBar"></div>
            </div>
            <div class="progress-text" id="progressText">准备中...</div>
        </div>

        <!-- 流程展示区域 -->
        <div class="flow-section" id="flowSection">
            <h2 class="flow-title">📊 生成流程</h2>
            <div class="stages-container" id="stagesContainer"></div>
        </div>
    </div>

    <!-- 详情弹窗 -->
    <div class="modal" id="detailModal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal()">&times;</span>
            <h2 class="modal-title" id="modalTitle">阶段详情</h2>
            <div id="modalBody"></div>
        </div>
    </div>

    <script>
        // 阶段定义（从后端注入）
        let currentSessionId = null;
        let ws = null;
        const STAGE_DEFINITIONS = __STAGE_DEFINITIONS__;

        // 初始化页面
        document.addEventListener('DOMContentLoaded', function() {
            renderInitialStages();
        });

        // 渲染初始阶段卡片
        function renderInitialStages() {
            const container = document.getElementById('stagesContainer');
            container.innerHTML = '';

            for (const [stageId, stageDef] of Object.entries(STAGE_DEFINITIONS)) {
                const card = createStageCard(stageId, stageDef, 'pending');
                container.appendChild(card);
            }
        }

        // 创建阶段卡片
        function createStageCard(stageId, stageDef, status, output = null) {
            const card = document.createElement('div');
            card.className = `stage-card ${status}`;
            card.id = `stage-${stageId}`;
            card.onclick = () => showStageDetail(stageId);

            const statusText = {
                'pending': '等待中',
                'running': '处理中',
                'success': '完成',
                'failed': '失败'
            }[status] || status;

            let detailsHtml = stageDef.details.map(detail =>
                `<div class="detail-item">${detail}</div>`
            ).join('');

            let outputsHtml = '';
            if (stageDef.outputs) {
                outputsHtml = '<div class="stage-outputs">' +
                    stageDef.outputs.map(o => `<span class="output-tag">${o}</span>`).join('') +
                    '</div>';
            }

            card.innerHTML = `
                <div class="stage-header">
                    <span class="stage-icon">${stageDef.icon}</span>
                    <span class="stage-name">${stageDef.name}</span>
                    <span class="stage-status status-${status}">${statusText}</span>
                </div>
                <div class="stage-description">${stageDef.description}</div>
                <div class="stage-details" id="details-${stageId}">
                    ${detailsHtml}
                </div>
                ${outputsHtml}
                <div class="stage-time" id="time-${stageId}"></div>
            `;

            return card;
        }

        // 开始生成
        async function startGeneration() {
            const text = document.getElementById('inputText').value.trim();
            if (!text) {
                alert('请输入故事内容');
                return;
            }

            const btn = document.getElementById('generateBtn');
            btn.disabled = true;
            btn.textContent = '⏳ 生成中...';

            try {
                const res = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        text: text,
                        style: document.getElementById('style').value,
                        resolution: document.getElementById('resolution').value
                    })
                });

                const data = await res.json();
                if (data.error) {
                    alert('启动失败: ' + data.error);
                    btn.disabled = false;
                    btn.textContent = '🚀 开始生成';
                    return;
                }

                currentSessionId = data.session_id;

                // 显示进度和流程区域
                document.getElementById('progressSection').classList.add('active');
                document.getElementById('flowSection').classList.add('active');

                // 连接WebSocket
                connectWebSocket();

            } catch (e) {
                alert('请求失败: ' + e.message);
                btn.disabled = false;
                btn.textContent = '🚀 开始生成';
            }
        }

        // 连接WebSocket
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;

            ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                console.log('WebSocket connected');
                // 订阅当前会话
                if (currentSessionId) {
                    ws.send(JSON.stringify({
                        type: 'subscribe',
                        session_id: currentSessionId
                    }));
                }
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            };

            ws.onclose = () => {
                console.log('WebSocket disconnected');
                // 5秒后重连
                setTimeout(() => {
                    if (currentSessionId) {
                        connectWebSocket();
                    }
                }, 5000);
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        }

        // 处理WebSocket消息
        function handleWebSocketMessage(data) {
            console.log('收到消息:', data);

            if (data.type === 'session_init') {
                // 初始化会话状态
                for (const [stageId, nodeData] of Object.entries(data.nodes || {})) {
                    updateStage(stageId, nodeData.status, nodeData.output, nodeData.duration);
                }
                updateProgress(data.progress, '准备就绪');

            } else if (data.type === 'stage_update') {
                updateStage(data.stage_id, data.status, data.output, data.duration);

                // 计算整体进度
                const stageOrder = ['input', 'script', 'scene_desc', 'image', 'storyboard',
                                  'animation', 'audio', 'text', 'compose', 'output'];
                let completed = 0;
                stageOrder.forEach(id => {
                    const card = document.getElementById(`stage-${id}`);
                    if (card && card.classList.contains('success')) {
                        completed++;
                    }
                });
                const progress = completed / stageOrder.length;
                const stageNames = {
                    'input': '输入处理',
                    'script': '剧本生成',
                    'scene_desc': '画面描述',
                    'image': '图像生成',
                    'storyboard': '分镜编排',
                    'animation': '动画化',
                    'audio': '音频生成',
                    'text': '文字字幕',
                    'compose': '合成渲染',
                    'output': '输出交付'
                };
                updateProgress(progress, stageNames[data.stage_id] || '处理中');

            } else if (data.type === 'progress') {
                updateProgress(data.progress, data.message);

            } else if (data.type === 'complete') {
                generationComplete(data.output_path);

            } else if (data.type === 'error') {
                generationError(data.error);
            }
        }

        // 更新阶段状态
        function updateStage(stageId, status, output = null, duration = null) {
            const stageDef = STAGE_DEFINITIONS[stageId];
            if (!stageDef) return;

            const container = document.getElementById('stagesContainer');
            const oldCard = document.getElementById(`stage-${stageId}`);

            const newCard = createStageCard(stageId, stageDef, status, output);

            if (oldCard) {
                oldCard.replaceWith(newCard);
            } else {
                container.appendChild(newCard);
            }

            // 更新时间
            if (duration) {
                const timeEl = document.getElementById(`time-${stageId}`);
                if (timeEl) {
                    timeEl.textContent = `耗时: ${duration.toFixed(2)}秒`;
                }
            }

            // 如果完成，标记详情项
            if (status === 'success') {
                const detailsEl = document.getElementById(`details-${stageId}`);
                if (detailsEl) {
                    const items = detailsEl.querySelectorAll('.detail-item');
                    items.forEach(item => item.classList.add('done'));
                }
            }
        }

        // 更新进度
        function updateProgress(progress, message) {
            const progressBar = document.getElementById('progressBar');
            const progressText = document.getElementById('progressText');

            progressBar.style.width = `${progress * 100}%`;
            progressText.textContent = `${message} (${Math.round(progress * 100)}%)`;
        }

        // 生成完成
        function generationComplete(outputPath) {
            const btn = document.getElementById('generateBtn');
            btn.disabled = false;
            btn.textContent = '🚀 开始生成';

            updateProgress(1, '生成完成！');

            // 显示完成消息
            const container = document.getElementById('stagesContainer');
            const completeCard = document.createElement('div');
            completeCard.className = 'stage-card success';
            completeCard.innerHTML = `
                <div class="stage-header">
                    <span class="stage-icon">🎉</span>
                    <span class="stage-name">生成完成</span>
                </div>
                <div class="stage-description">
                    视频已生成完成！<br>
                    <a href="/output/${encodeURIComponent(outputPath)}" download style="color: #00d9ff;">点击下载视频</a>
                </div>
            `;
            container.appendChild(completeCard);
        }

        // 生成错误
        function generationError(error) {
            const btn = document.getElementById('generateBtn');
            btn.disabled = false;
            btn.textContent = '🚀 开始生成';

            alert('生成失败: ' + error);
        }

        // 显示阶段详情
        function showStageDetail(stageId) {
            const stageDef = STAGE_DEFINITIONS[stageId];
            if (!stageDef) return;

            const modal = document.getElementById('detailModal');
            const title = document.getElementById('modalTitle');
            const body = document.getElementById('modalBody');

            title.innerHTML = `${stageDef.icon} ${stageDef.name}`;

            let html = `
                <div class="detail-row">
                    <span class="detail-label">描述:</span>
                    <span class="detail-value">${stageDef.description}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">处理步骤:</span>
                </div>
            `;

            stageDef.details.forEach((detail, i) => {
                html += `<div class="detail-item" style="margin-left: 120px;">${detail}</div>`;
            });

            if (stageDef.outputs) {
                html += `
                    <div class="detail-row" style="margin-top: 15px;">
                        <span class="detail-label">输出:</span>
                    </div>
                `;
                stageDef.outputs.forEach(output => {
                    html += `<span class="output-tag">${output}</span>`;
                });
            }

            // 特殊处理画面描述阶段 - 显示提示词示例
            if (stageId === 'scene_desc') {
                html += `
                    <div style="margin-top: 20px;">
                        <div class="prompt-label">📝 正向提示词示例:</div>
                        <div class="prompt-box">
一个少年在雨夜中遇到了神秘少女, anime风格, masterpiece, best quality, highly detailed
                        </div>
                        <div class="prompt-label">🚫 负面提示词:</div>
                        <div class="prompt-box">
low quality, blurry, ugly, deformed, disfigured, bad anatomy, extra limbs, missing limbs, watermark, text
                        </div>
                    </div>
                `;
            }

            // 特殊处理剧本生成阶段 - 显示三幕式结构
            if (stageId === 'script') {
                html += `
                    <div style="margin-top: 20px;">
                        <div class="prompt-label">📜 三幕式结构:</div>
                        <div style="margin-top: 10px; padding: 18px; background: #f8fafc; border-radius: 10px; border: 1px solid #e2e8f0;">
                            <div style="margin-bottom: 12px; padding: 10px; background: #eff6ff; border-radius: 8px;"><strong style="color: #2563eb;">第一幕 (25%):</strong> 建立世界观、介绍角色、激励事件</div>
                            <div style="margin-bottom: 12px; padding: 10px; background: #fef3c7; border-radius: 8px;"><strong style="color: #d97706;">第二幕 (50%):</strong> 发展冲突、角色成长、中点转折、危机加深</div>
                            <div style="padding: 10px; background: #d1fae5; border-radius: 8px;"><strong style="color: #059669;">第三幕 (25%):</strong> 高潮对决、情感释放、故事收尾</div>
                        </div>
                    </div>
                `;
            }

            body.innerHTML = html;
            modal.classList.add('active');
        }

        // 关闭弹窗
        function closeModal() {
            document.getElementById('detailModal').classList.remove('active');
        }

        // 点击弹窗外部关闭
        window.onclick = function(event) {
            const modal = document.getElementById('detailModal');
            if (event.target === modal) {
                closeModal();
            }
        }
    </script>
</body>
</html>
    """

    # 替换占位符
    return html_template.replace('__STAGE_DEFINITIONS__', stages_json)


@app.post("/api/generate")
async def start_generation(request: GenerateRequest, background_tasks: BackgroundTasks):
    """开始生成"""
    session = create_session(request.text, request.style, request.resolution)

    # 启动后台生成任务
    background_tasks.add_task(run_generation_task, session.id)

    return {
        "session_id": session.id,
        "stages": STAGE_DEFINITIONS
    }


@app.post("/api/regenerate")
async def regenerate_stage(request: RegenerateRequest):
    """重新生成指定阶段"""
    session = get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    node = session.get_node(request.stage_id)
    if not node:
        raise HTTPException(status_code=404, detail="Stage not found")

    # TODO: 重新运行该阶段

    return {
        "success": True,
        "stage_id": request.stage_id,
        "message": f"重新生成阶段: {node.stage_name}"
    }


@app.get("/api/sessions")
async def list_sessions_api():
    """列出所有生成会话"""
    sessions = list_sessions()
    return {
        "sessions": [
            {
                "id": s.id,
                "input": s.input_text[:100],
                "style": s.style,
                "resolution": s.resolution,
                "create_time": s.create_time.isoformat(),
                "progress": s.get_progress(),
                "status": s.get_node("output").status.value if s.get_node("output") else "pending"
            }
            for s in sessions
        ]
    }


@app.get("/api/sessions/{session_id}")
async def get_session_api(session_id: str):
    """获取生成会话详情"""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "id": session.id,
        "input": session.input_text,
        "style": session.style,
        "resolution": session.resolution,
        "create_time": session.create_time.isoformat(),
        "progress": session.get_progress(),
        "stages": {
            stage_id: {
                "id": node.id,
                "stage_id": node.stage_id,
                "stage_name": node.stage_name,
                "status": node.status.value,
                "start_time": node.start_time.isoformat() if node.start_time else None,
                "end_time": node.end_time.isoformat() if node.end_time else None,
                "duration": node.duration,
                "error_message": node.error_message,
                "output": node.output,
                "progress": node.progress,
            }
            for stage_id, node in session.nodes.items()
        }
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点，推送更新"""
    # 等待客户端发送订阅消息
    await websocket.accept()

    session_id = None

    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()

            if data.get("type") == "subscribe":
                session_id = data.get("session_id")
                session = get_session(session_id)

                if session:
                    # 注册连接
                    await manager.connect(websocket, session_id)

                    # 发送当前会话状态
                    await websocket.send_json({
                        "type": "session_init",
                        "session_id": session.id,
                        "stages": STAGE_DEFINITIONS,
                        "progress": session.get_progress(),
                        "nodes": {
                            stage_id: {
                                "status": node.status.value,
                                "output": node.output,
                                "duration": node.duration,
                                "error": node.error_message
                            }
                            for stage_id, node in session.nodes.items()
                        }
                    })

    except WebSocketDisconnect:
        if session_id:
            manager.disconnect(websocket, session_id)
    except Exception as e:
        print(f"WebSocket error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

