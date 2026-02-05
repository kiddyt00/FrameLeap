"""
FrameLeap Web界面

完整展示10阶段生成流程，支持逐步展示和重新生成
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import uuid
import asyncio
import json

from fastapi import WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel


class StageStatus(str, Enum):
    """阶段状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


# 阶段定义 - 4阶段流程
STAGE_DEFINITIONS = {
    "input": {
        "id": "input",
        "name": "📥 输入处理",
        "description": "处理用户输入文本，获取风格配置",
        "icon": "📥",
        "color": "#6c757d",
        "details": ["预处理文本", "获取风格配置", "验证输入"],
        "outputs": ["输入文本", "风格", "分辨率"]
    },
    "script": {
        "id": "script",
        "name": "📜 剧本生成",
        "description": "调用千问LLM分析文本，生成完整剧本结构",
        "icon": "📜",
        "color": "#4facfe",
        "details": ["构建LLM提示词", "调用千问API", "解析生成结果", "提取场景和角色"],
        "outputs": ["剧本结构", "场景列表", "角色数据"]
    },
    "scene_desc": {
        "id": "scene_desc",
        "name": "🎨 场景描述",
        "description": "为每个场景生成详细的画面描述和AI绘画提示词",
        "icon": "🎨",
        "color": "#f59e0b",
        "details": ["分析场景内容", "构建画面描述", "生成AI绘画提示词"],
        "outputs": ["场景描述", "绘画提示词"]
    },
    "image": {
        "id": "image",
        "name": "🖼️ 图像生成",
        "description": "使用通义万相模型为每个场景生成高质量图像",
        "icon": "🖼️",
        "color": "#10b981",
        "details": ["连接通义万相API", "生成场景图像", "保存图像文件"],
        "outputs": ["场景图像"]
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
    print(f"[DEBUG] run_generation_task started for session {session_id}")
    session = get_session(session_id)
    if not session:
        print(f"[DEBUG] Session not found: {session_id}")
        return
    print(f"[DEBUG] Session found, proceeding...")

    # 阶段执行顺序映射（4个阶段）
    stage_order = ["input", "script", "scene_desc", "image"]

    # 阶段名称映射
    stage_names = {
        "input": "输入处理",
        "script": "剧本生成",
        "scene_desc": "场景描述",
        "image": "图像生成",
    }

    # 创建进度队列（线程安全）
    progress_queue: asyncio.Queue[tuple[str, float]] = asyncio.Queue()
    error_queue: asyncio.Queue[Exception] = asyncio.Queue()

    async def progress_dispatcher():
        """后台任务：从队列处理进度更新并发送WebSocket"""
        try:
            while True:
                stage_name, progress = await progress_queue.get()
                print(f"[DEBUG] Dispatcher received: {stage_name} - {progress}")

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
                        print(f"[DEBUG] Broadcasted: {stage_id}")
                progress_queue.task_done()
        except asyncio.CancelledError:
            # 任务被取消，正常退出
            pass

    async def error_dispatcher():
        """后台任务：从队列处理错误并发送WebSocket"""
        try:
            while True:
                error = await error_queue.get()
                await manager.broadcast_to_session(session_id, {
                    "type": "error",
                    "error": str(error)
                })
        except asyncio.CancelledError:
            pass

    try:
        print(f"[DEBUG] Starting try block")
        # 启动分发器任务
        print(f"[DEBUG] Creating dispatcher tasks...")
        progress_task = asyncio.create_task(progress_dispatcher())
        error_task = asyncio.create_task(error_dispatcher())
        print(f"[DEBUG] Dispatcher tasks created")

        # 导入 Generator
        print(f"[DEBUG] Importing Generator...")
        from app.generator import Generator
        from app.config import config
        print(f"[DEBUG] Generator imported")

        # 创建同步回调（线程安全地向队列提交数据）
        def sync_progress_callback(stage_name: str, progress: float):
            """从工作线程调用，将进度放入队列"""
            print(f"[DEBUG] Progress callback: {stage_name} - {progress}")
            try:
                # Queue.put_nowait 是线程安全的
                progress_queue.put_nowait((stage_name, progress))
                print(f"[DEBUG] Queued progress: {stage_name}")
            except Exception as e:
                print(f"Failed to queue progress: {e}")

        def sync_error_callback(error: Exception):
            """从工作线程调用，将错误放入队列"""
            try:
                error_queue.put_nowait(error)
            except Exception as e:
                print(f"Failed to queue error: {e}")

        # 创建生成器并设置回调
        print(f"[DEBUG] Creating Generator instance...")
        import time
        start = time.time()
        generator = Generator(cfg=config)
        elapsed = time.time() - start
        print(f"[DEBUG] Generator created in {elapsed:.2f}s")
        generator._progress_callback = sync_progress_callback
        generator._error_callback = sync_error_callback
        print(f"[DEBUG] Callbacks set")

        print(f"[DEBUG] Starting generation for session {session_id}")

        # 执行生成（在线程池中运行，避免阻塞事件循环）
        result = await asyncio.to_thread(
            generator.generate,
            text=session.input_text,
            style=session.style,
            resolution=session.resolution
        )

        print(f"[DEBUG] Generation completed: success={result.success}")
        if not result.success:
            print(f"[DEBUG] Error message: {result.error_message}")
        else:
            print(f"[DEBUG] Output path: {result.video_path}")

        # 等待队列处理完毕（确保所有消息都已发送）
        await progress_queue.join()
        await error_queue.join()

        # 取消分发器任务
        progress_task.cancel()
        error_task.cancel()
        await asyncio.gather(progress_task, error_task, return_exceptions=True)

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
                    if stage_id == "input":
                        node.output = {
                            "input_text": session.input_text,
                            "style": session.style,
                            "resolution": session.resolution
                        }
                    elif result.script and stage_id == "script":
                        # 序列化场景数据
                        scenes_data = []
                        for scene in result.script.scenes:
                            scenes_data.append({
                                "order": scene.order,
                                "title": scene.title,
                                "description": scene.description,
                                "atmosphere": scene.atmosphere
                            })

                        # 序列化角色数据
                        characters_data = []
                        for char_id, char in result.script.characters.items():
                            characters_data.append({
                                "id": char_id,
                                "name": char.name,
                                "type": char.character_type.value if hasattr(char.character_type, 'value') else str(char.character_type),
                                "description": char.description,
                                "personality": char.personality if hasattr(char, 'personality') else [],
                                "age": char.appearance.age if hasattr(char, 'appearance') and char.appearance else "unknown",
                                "gender": char.appearance.gender if hasattr(char, 'appearance') and char.appearance else "unknown"
                            })

                        node.output = {
                            "title": result.script.title,
                            "story_type": result.script.story_type.value if hasattr(result.script.story_type, 'value') else str(result.script.story_type),
                            "theme": result.script.theme,
                            "premise": result.script.premise,
                            "scene_count": len(result.script.scenes),
                            "scenes": scenes_data,
                            "character_count": len(result.script.characters),
                            "characters": characters_data
                        }
                    elif stage_id == "scene_desc" and result.script:
                        # 场景描述阶段的输出已经在script阶段生成，这里只是确认完成
                        node.output = {
                            "description_count": len(result.script.scenes),
                            "scenes_prepared": len(result.script.scenes)
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


async def run_stage_regeneration(session_id: str, stage_id: str):
    """
    重新生成指定阶段

    只重新生成指定阶段，不影响其他阶段
    """
    print(f"[DEBUG] Regenerating stage {stage_id} for session {session_id}")
    session = get_session(session_id)
    if not session:
        print(f"[DEBUG] Session not found: {session_id}")
        return

    # 阶段名称映射
    stage_names = {
        "input": "输入处理",
        "script": "剧本生成",
        "scene_desc": "场景描述",
        "image": "图像生成",
    }

    # 验证阶段ID
    if stage_id not in stage_names:
        await manager.broadcast_to_session(session_id, {
            "type": "error",
            "error": f"无效的阶段ID: {stage_id}"
        })
        return

    # 重置阶段状态
    node = session.get_node(stage_id)
    if not node:
        await manager.broadcast_to_session(session_id, {
            "type": "error",
            "error": f"阶段不存在: {stage_id}"
        })
        return

    node.status = StageStatus.PENDING
    node.progress = 0.0
    node.start_time = None
    node.end_time = None
    node.error_message = None

    # 创建进度队列
    progress_queue: asyncio.Queue[tuple[str, float]] = asyncio.Queue()
    error_queue: asyncio.Queue[Exception] = asyncio.Queue()

    async def progress_dispatcher():
        """后台任务：从队列处理进度更新并发送WebSocket"""
        try:
            while True:
                stage_name, progress = await progress_queue.get()
                print(f"[DEBUG] Regeneration dispatcher received: {stage_name} - {progress}")

                # 推送更新
                await manager.broadcast_to_session(session_id, {
                    "type": "stage_update",
                    "stage_id": stage_id,
                    "status": "running",
                    "progress": progress,
                    "is_regeneration": True
                })
                progress_queue.task_done()
        except asyncio.CancelledError:
            pass

    async def error_dispatcher():
        """后台任务：从队列处理错误并发送WebSocket"""
        try:
            while True:
                error = await error_queue.get()
                await manager.broadcast_to_session(session_id, {
                    "type": "error",
                    "error": str(error)
                })
        except asyncio.CancelledError:
            pass

    try:
        # 启动分发器任务
        progress_task = asyncio.create_task(progress_dispatcher())
        error_task = asyncio.create_task(error_dispatcher())

        # 导入 Generator
        from app.generator import Generator
        from app.config import config

        # 创建回调
        def sync_progress_callback(stage_name: str, progress: float):
            try:
                progress_queue.put_nowait((stage_name, progress))
            except Exception as e:
                print(f"Failed to queue progress: {e}")

        def sync_error_callback(error: Exception):
            try:
                error_queue.put_nowait(error)
            except Exception as e:
                print(f"Failed to queue error: {e}")

        # 创建生成器
        generator = Generator(cfg=config)
        generator._progress_callback = sync_progress_callback
        generator._error_callback = sync_error_callback

        # 根据阶段执行不同的生成逻辑
        result = None

        if stage_id == "script":
            # 重新生成剧本
            from app.models.script import Script
            result = asyncio.to_thread(
                generator.generate_script,
                session.input_text,
                session.style
            )
            script = await result
            if script:
                # 序列化场景数据
                scenes_data = []
                for scene in script.scenes:
                    scenes_data.append({
                        "order": scene.order,
                        "title": scene.title,
                        "description": scene.description,
                        "atmosphere": scene.atmosphere
                    })

                # 序列化角色数据
                characters_data = []
                for char_id, char in script.characters.items():
                    characters_data.append({
                        "id": char_id,
                        "name": char.name,
                        "type": char.character_type.value if hasattr(char.character_type, 'value') else str(char.character_type),
                        "description": char.description,
                        "personality": char.personality if hasattr(char, 'personality') else [],
                        "age": char.appearance.age if hasattr(char, 'appearance') and char.appearance else "unknown",
                        "gender": char.appearance.gender if hasattr(char, 'appearance') and char.appearance else "unknown"
                    })

                node.output = {
                    "title": script.title,
                    "story_type": script.story_type.value if hasattr(script.story_type, 'value') else str(script.story_type),
                    "theme": script.theme,
                    "premise": script.premise,
                    "scene_count": len(script.scenes),
                    "scenes": scenes_data,
                    "character_count": len(script.characters),
                    "characters": characters_data
                }
                node.status = StageStatus.SUCCESS
            else:
                node.status = StageStatus.FAILED
                node.error_message = "剧本生成失败"

        elif stage_id == "scene_desc":
            # 重新生成场景描述（需要先有剧本）
            if not session.get_node("script").output:
                node.status = StageStatus.FAILED
                node.error_message = "请先生成剧本"
            else:
                # 场景描述是在剧本生成时一起完成的
                node.output = {
                    "description_count": len(session.get_node("script").output.get("scenes", [])),
                    "scenes_prepared": len(session.get_node("script").output.get("scenes", []))
                }
                node.status = StageStatus.SUCCESS

        elif stage_id == "image":
            # 重新生成图像（需要先有剧本）
            script_output = session.get_node("script").output
            if not script_output:
                node.status = StageStatus.FAILED
                node.error_message = "请先生成剧本"
            else:
                # 调用图像生成
                images = await asyncio.to_thread(
                    generator.generate_images,
                    session.input_text,
                    session.style,
                    session.resolution
                )
                if images:
                    node.output = {"image_paths": images}
                    node.status = StageStatus.SUCCESS
                else:
                    node.status = StageStatus.FAILED
                    node.error_message = "图像生成失败"

        elif stage_id == "input":
            # 输入阶段不需要重新生成
            node.output = {
                "input_text": session.input_text,
                "style": session.style,
                "resolution": session.resolution
            }
            node.status = StageStatus.SUCCESS

        node.end_time = datetime.now()
        if node.start_time is None:
            node.start_time = node.end_time

        # 等待队列处理完毕
        await progress_queue.join()
        await error_queue.join()

        # 取消分发器任务
        progress_task.cancel()
        error_task.cancel()
        await asyncio.gather(progress_task, error_task, return_exceptions=True)

        # 推送最终状态
        await manager.broadcast_to_session(session_id, {
            "type": "stage_update",
            "stage_id": stage_id,
            "status": node.status.value,
            "output": node.output,
            "duration": node.duration,
            "is_regeneration": True
        })

    except Exception as e:
        node.status = StageStatus.FAILED
        node.error_message = str(e)
        node.end_time = datetime.now()

        await manager.broadcast_to_session(session_id, {
            "type": "stage_update",
            "stage_id": stage_id,
            "status": "failed",
            "error": str(e),
            "is_regeneration": True
        })


# =============================================================================
# FastAPI应用
# =============================================================================

app = FastAPI(title="FrameLeap")

# 挂载静态文件目录
from fastapi.staticfiles import StaticFiles
from app.config import config
import os

# 确保temp目录存在
temp_dir = Path(config.paths.temp_dir)
temp_dir.mkdir(parents=True, exist_ok=True)

# 挂载temp目录为静态文件
app.mount("/temp", StaticFiles(directory=str(temp_dir)), name="temp")


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

    # 检查LLM配置状态
    from app.config import config
    llm_configured = bool(config.api.llm_api_key)

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
            background: #f1f5f9;
            color: #1e293b;
            min-height: 100vh;
        }
        .container {
            max-width: 1800px;
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

        /* 配置警告 */
        .config-warning {
            background: #fff7ed;
            border: 2px solid #f59e0b;
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 20px;
            display: none;
            align-items: center;
            gap: 16px;
            animation: slideDown 0.3s ease;
            box-shadow: 0 2px 8px rgba(245, 158, 11, 0.1);
        }
        .config-warning.active {
            display: flex;
        }
        .warning-content {
            display: flex;
            align-items: center;
            gap: 12px;
            flex: 1;
        }
        .warning-icon {
            font-size: 28px;
            flex-shrink: 0;
        }
        .warning-text {
            color: #92400e;
            font-size: 14px;
            line-height: 1.5;
        }
        .warning-text a {
            color: #2563eb;
            text-decoration: underline;
            margin: 0 4px;
        }
        .warning-text strong {
            display: block;
            margin-bottom: 4px;
        }

        @keyframes slideDown {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* 输入区域 */
        .input-section {
            background: #ffffff;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
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
            height: 100px;
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
        }
        select:focus {
            outline: none;
            border-color: #2563eb;
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
        }
        .btn-primary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        /* 进度条 */
        .progress-section {
            background: #ffffff;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            display: none;
            border: 1px solid #e2e8f0;
        }
        .progress-section.active {
            display: block;
        }
        .progress-bar-container {
            height: 6px;
            background: #f1f5f9;
            border-radius: 3px;
            overflow: hidden;
            margin-bottom: 10px;
        }
        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #2563eb, #3b82f6, #06b6d4);
            border-radius: 3px;
            transition: width 0.4s ease;
            width: 0%;
        }
        .progress-text {
            text-align: center;
            color: #64748b;
            font-size: 14px;
        }

        /* 瀑布流布局 */
        .flow-section {
            display: none;
        }
        .flow-section.active {
            display: block;
        }

        .pipeline-container {
            display: flex;
            flex-direction: column;
            gap: 0;
        }

        /* 阶段行 */
        .stage-row {
            display: flex;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            margin-bottom: 16px;
            overflow: hidden;
            transition: all 0.3s;
        }
        .stage-row:hover {
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        }

        /* 左侧阶段信息 */
        .stage-info {
            flex-shrink: 0;
            width: 280px;
            padding: 20px;
            border-right: 1px solid #e2e8f0;
            background: #f8fafc;
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .stage-info-icon {
            font-size: 36px;
            flex-shrink: 0;
        }
        .stage-info-text {
            flex: 1;
            min-width: 0;
        }
        .stage-info-name {
            font-weight: 600;
            font-size: 16px;
            color: #1e293b;
            margin-bottom: 4px;
        }
        .stage-info-desc {
            font-size: 12px;
            color: #64748b;
            line-height: 1.4;
        }

        /* 状态指示器 */
        .stage-status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            flex-shrink: 0;
            margin-left: 8px;
        }
        .status-pending { background: #cbd5e1; }
        .status-running {
            background: #f59e0b;
            animation: pulse 1.5s infinite;
        }
        .status-success { background: #10b981; }
        .status-failed { background: #ef4444; }

        /* 重新生成按钮 */
        .stage-regenerate-btn {
            padding: 6px 14px;
            font-size: 12px;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            background: #ffffff;
            color: #64748b;
            cursor: pointer;
            transition: all 0.2s;
            margin-left: auto;
            white-space: nowrap;
        }
        .stage-regenerate-btn:hover:not(:disabled) {
            background: #f8fafc;
            border-color: #2563eb;
            color: #2563eb;
        }
        .stage-regenerate-btn:disabled {
            opacity: 0.4;
            cursor: not-allowed;
        }
        .stage-regenerate-btn.running {
            animation: spin 1s linear infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        /* 右侧结果区域 */
        .stage-results {
            flex: 1;
            padding: 20px;
            display: flex;
            gap: 16px;
            overflow-x: auto;
            min-height: 140px;
            align-items: stretch;
        }
        .stage-results::-webkit-scrollbar {
            height: 8px;
        }
        .stage-results::-webkit-scrollbar-track {
            background: #f1f5f9;
            border-radius: 4px;
        }
        .stage-results::-webkit-scrollbar-thumb {
            background: #cbd5e1;
            border-radius: 4px;
        }
        .stage-results::-webkit-scrollbar-thumb:hover {
            background: #94a3b8;
        }

        /* 空状态 */
        .empty-state {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #94a3b8;
            font-size: 14px;
        }

        /* 结果卡片 */
        .result-card {
            flex-shrink: 0;
            width: 320px;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            overflow: hidden;
            transition: all 0.2s;
        }
        .result-card:hover {
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
        }

        .result-header {
            padding: 12px 16px;
            background: #f8fafc;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .result-title {
            font-size: 13px;
            font-weight: 600;
            color: #334155;
        }
        .result-time {
            font-size: 11px;
            color: #94a3b8;
        }
        .result-actions {
            display: flex;
            gap: 8px;
        }
        .result-btn {
            padding: 4px 10px;
            font-size: 11px;
            border-radius: 6px;
            border: 1px solid #e2e8f0;
            background: #ffffff;
            color: #64748b;
            cursor: pointer;
            transition: all 0.2s;
        }
        .result-btn:hover {
            background: #f1f5f9;
            border-color: #cbd5e1;
        }

        .result-content {
            padding: 16px;
            max-height: 300px;
            overflow-y: auto;
        }

        /* 结果内容样式 */
        .result-text {
            font-size: 13px;
            line-height: 1.6;
            color: #334155;
        }
        .result-text strong {
            color: #2563eb;
            font-weight: 600;
        }

        /* 场景列表 */
        .scene-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .scene-item {
            padding: 10px 12px;
            background: #f8fafc;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }
        .scene-title {
            font-size: 13px;
            font-weight: 600;
            color: #2563eb;
            margin-bottom: 4px;
        }
        .scene-desc {
            font-size: 12px;
            color: #64748b;
            line-height: 1.4;
        }

        /* 角色列表 */
        .char-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
        }
        .char-item {
            padding: 10px;
            background: #fef3c7;
            border-radius: 8px;
            border: 1px solid #fcd34d;
        }
        .char-name {
            font-size: 12px;
            font-weight: 600;
            color: #92400e;
            margin-bottom: 4px;
        }
        .char-desc {
            font-size: 11px;
            color: #b45309;
        }

        /* 图像网格 */
        .image-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
        }
        .image-item {
            aspect-ratio: 16/10;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #e2e8f0;
            background: #f1f5f9;
        }
        .image-item img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .image-item.loading {
            display: flex;
            align-items: center;
            justify-content: center;
            color: #94a3b8;
            font-size: 12px;
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
            border-radius: 16px;
            padding: 30px;
            max-width: 800px;
            width: 90%;
            max-height: 85vh;
            overflow-y: auto;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
        }
        .modal-title {
            color: #1e293b;
            font-size: 1.3em;
            margin-bottom: 20px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .modal-close {
            margin-left: auto;
            cursor: pointer;
            font-size: 24px;
            color: #94a3b8;
            transition: color 0.2s;
        }
        .modal-close:hover {
            color: #475569;
        }

        /* 响应式 */
        @media (max-width: 768px) {
            .stage-row {
                flex-direction: column;
            }
            .stage-info {
                width: 100%;
                border-right: none;
                border-bottom: 1px solid #e2e8f0;
            }
            .stage-results {
                flex-direction: column;
            }
            .result-card {
                width: 100%;
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
            <p>AI驱动的剧本生成系统（使用千问LLM）</p>
        </div>

        <!-- LLM配置警告 -->
        <div class="config-warning" id="configWarning">
            <div class="warning-content">
                <span class="warning-icon">⚠️</span>
                <div class="warning-text">
                    <strong>未配置千问 API Key</strong><br>
                    剧本生成将使用简化规则。请配置 API Key 以获得更好的生成效果。<br>
                    <a href="https://help.aliyun.com/zh/dashscope/" target="_blank">获取千问 API Key</a>
                    |
                    <a href="#" onclick="dismissWarning(); return false;">暂时忽略</a>
                </div>
            </div>
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

        <!-- 瀑布流流程展示区域 -->
        <div class="flow-section" id="flowSection">
            <div class="pipeline-container" id="pipelineContainer"></div>
        </div>
    </div>

    <!-- 详情弹窗 -->
    <div class="modal" id="detailModal">
        <div class="modal-content">
            <div class="modal-title">
                <span id="modalTitle">阶段详情</span>
                <span class="modal-close" onclick="closeModal()">&times;</span>
            </div>
            <div id="modalBody"></div>
        </div>
    </div>

    <script>
        // 阶段定义（从后端注入）
        let currentSessionId = null;
        let ws = null;
        const STAGE_DEFINITIONS = __STAGE_DEFINITIONS__;
        const stageResults = {};  // 存储每个阶段的所有结果（支持多次生成）

        // 阶段顺序
        const STAGE_ORDER = ['input', 'script', 'scene_desc', 'image'];

        // 初始化页面
        document.addEventListener('DOMContentLoaded', function() {
            checkLLMConfig();
            renderInitialPipeline();
        });

        // 检查LLM配置
        async function checkLLMConfig() {
            try {
                const res = await fetch('/api/config/check');
                const data = await res.json();
                if (!data.llm_configured) {
                    showWarning();
                }
            } catch (e) {
                console.error('配置检查失败:', e);
            }
        }

        // 显示警告
        function showWarning() {
            document.getElementById('configWarning').classList.add('active');
        }

        // 忽略警告
        function dismissWarning() {
            document.getElementById('configWarning').classList.remove('active');
        }

        // 渲染初始流水线
        function renderInitialPipeline() {
            const container = document.getElementById('pipelineContainer');
            container.innerHTML = '';

            for (const stageId of STAGE_ORDER) {
                const stageDef = STAGE_DEFINITIONS[stageId];
                const row = createStageRow(stageId, stageDef);
                container.appendChild(row);
            }
        }

        // 创建阶段行
        function createStageRow(stageId, stageDef) {
            const row = document.createElement('div');
            row.className = 'stage-row';
            row.id = `stage-row-${stageId}`;

            row.innerHTML = `
                <div class="stage-info">
                    <span class="stage-info-icon">${stageDef.icon}</span>
                    <div class="stage-info-text">
                        <div class="stage-info-name">${stageDef.name}</div>
                        <div class="stage-info-desc">${stageDef.description}</div>
                    </div>
                    <button class="stage-regenerate-btn" id="regenerate-${stageId}" onclick="regenerateStage('${stageId}')" disabled>
                        🔄 重新生成
                    </button>
                    <div class="stage-status-indicator status-pending" id="status-${stageId}"></div>
                </div>
                <div class="stage-results" id="results-${stageId}">
                    <div class="empty-state">等待中...</div>
                </div>
            `;

            return row;
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

                // 重置流水线
                renderInitialPipeline();

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

            if (data.type === 'stage_update') {
                updateStageStatus(data.stage_id, data.status);

                if (data.status === 'success' && data.output) {
                    addResultCard(data.stage_id, data.output);
                }

                // 更新进度（只统计首次完成）
                let completed = 0;
                STAGE_ORDER.forEach(id => {
                    const resultsContainer = document.getElementById(`results-${id}`);
                    if (resultsContainer && !resultsContainer.querySelector('.empty-state')) {
                        completed++;
                    }
                });
                const progress = Math.min(completed / STAGE_ORDER.length, 1);
                const stageNames = {
                    'input': '输入处理',
                    'script': '剧本生成',
                    'scene_desc': '场景描述',
                    'image': '图像生成',
                };
                const isRegeneration = data.is_regeneration ? '重新' : '';
                updateProgress(progress, `${isRegeneration}${stageNames[data.stage_id] || '处理中'}`);

            } else if (data.type === 'complete') {
                generationComplete(data.output_path);

            } else if (data.type === 'error') {
                generationError(data.error);
            }
        }

        // 更新阶段状态
        function updateStageStatus(stageId, status) {
            const indicator = document.getElementById(`status-${stageId}`);
            if (indicator) {
                indicator.className = `stage-status-indicator status-${status}`;
            }

            // 更新重新生成按钮状态
            const regenerateBtn = document.getElementById(`regenerate-${stageId}`);
            if (regenerateBtn) {
                // 只有在之前阶段都完成时才启用重新生成按钮
                const stageIndex = STAGE_ORDER.indexOf(stageId);
                let canRegenerate = true;

                if (stageIndex > 0) {
                    // 检查前面的阶段是否都完成
                    for (let i = 0; i < stageIndex; i++) {
                        const prevIndicator = document.getElementById(`status-${STAGE_ORDER[i]}`);
                        if (!prevIndicator || !prevIndicator.classList.contains('status-success')) {
                            canRegenerate = false;
                            break;
                        }
                    }
                }

                regenerateBtn.disabled = !canRegenerate || status === 'running';
            }
        }

        // 重新生成阶段
        async function regenerateStage(stageId) {
            if (!currentSessionId) {
                alert('请先生成完整流程');
                return;
            }

            const regenerateBtn = document.getElementById(`regenerate-${stageId}`);
            if (regenerateBtn) {
                regenerateBtn.disabled = true;
                regenerateBtn.classList.add('running');
                regenerateBtn.textContent = '⏳ 生成中...';
            }

            // 更新状态为运行中
            updateStageStatus(stageId, 'running');

            try {
                const res = await fetch('/api/regenerate_stage', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: currentSessionId,
                        stage_id: stageId
                    })
                });

                const data = await res.json();
                if (data.error) {
                    alert('重新生成失败: ' + data.error);
                    updateStageStatus(stageId, 'failed');
                }
            } catch (e) {
                alert('请求失败: ' + e.message);
                updateStageStatus(stageId, 'failed');
            } finally {
                if (regenerateBtn) {
                    regenerateBtn.classList.remove('running');
                    regenerateBtn.textContent = '🔄 重新生成';
                }
            }
        }

        // 添加结果卡片
        function addResultCard(stageId, output) {
            const resultsContainer = document.getElementById(`results-${stageId}`);
            if (!resultsContainer) return;

            // 移除空状态
            const emptyState = resultsContainer.querySelector('.empty-state');
            if (emptyState) {
                emptyState.remove();
            }

            // 存储结果
            if (!stageResults[stageId]) {
                stageResults[stageId] = [];
            }
            const resultIndex = stageResults[stageId].length;
            stageResults[stageId].push(output);

            // 创建结果卡片
            const card = createResultCard(stageId, output, resultIndex);
            resultsContainer.appendChild(card);

            // 滚动到最新结果
            resultsContainer.scrollLeft = resultsContainer.scrollWidth;
        }

        // 创建结果卡片
        function createResultCard(stageId, output, index) {
            const card = document.createElement('div');
            card.className = 'result-card';

            const now = new Date();
            const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;

            let content = '';

            switch(stageId) {
                case 'input':
                    content = `
                        <div class="result-text">
                            <div><strong>输入文本:</strong> ${output.input_text || ''}</div>
                            <div style="margin-top:8px;"><strong>风格:</strong> ${output.style || 'anime'}</div>
                            <div><strong>分辨率:</strong> ${output.resolution || '1080p'}</div>
                        </div>
                    `;
                    break;

                case 'script':
                    content = `
                        <div class="result-text">
                            <div style="margin-bottom:8px;"><strong>标题:</strong> ${output.title || '未命名'}</div>
                            <div style="margin-bottom:8px;"><strong>类型:</strong> ${output.story_type || '未知'}</div>
                            <div style="margin-bottom:8px;"><strong>主题:</strong> ${output.theme || '未知'}</div>
                            <div style="margin-bottom:12px;"><strong>场景数:</strong> ${output.scene_count || 0} | <strong>角色数:</strong> ${output.character_count || 0}</div>
                        </div>
                    `;
                    if (output.scenes && output.scenes.length > 0) {
                        content += `<div class="scene-list">`;
                        output.scenes.slice(0, 3).forEach(scene => {
                            content += `
                                <div class="scene-item">
                                    <div class="scene-title">场景 ${scene.order + 1}: ${scene.title}</div>
                                    <div class="scene-desc">${(scene.description || '').substring(0, 80)}...</div>
                                </div>
                            `;
                        });
                        if (output.scenes.length > 3) {
                            content += `<div style="text-align:center;color:#94a3b8;font-size:12px;padding:8px;">...还有 ${output.scenes.length - 3} 个场景</div>`;
                        }
                        content += `</div>`;
                    }
                    break;

                case 'scene_desc':
                    content = `
                        <div class="result-text">
                            <div><strong>已准备场景描述:</strong> ${output.description_count || 0} 个场景</div>
                        </div>
                    `;
                    break;

                case 'image':
                    if (output.image_paths && output.image_paths.length > 0) {
                        content = `<div class="image-grid">`;
                        output.image_paths.slice(0, 4).forEach((path, idx) => {
                            const fileName = path.split(/[\\/]/).pop();
                            const imageUrl = '/temp/' + fileName;
                            content += `
                                <div class="image-item">
                                    <img src="${imageUrl}" alt="场景 ${idx + 1}" onerror="this.parentElement.innerHTML='<div style=\\'display:flex;align-items:center;justify-content:center;height:100%;color:#ef4444;font-size:11px;\\'>加载失败</div>'">
                                </div>
                            `;
                        });
                        if (output.image_paths.length > 4) {
                            content += `<div style="grid-column:1/-1;text-align:center;color:#94a3b8;font-size:12px;padding:8px;">...还有 ${output.image_paths.length - 4} 张图像</div>`;
                        }
                        content += `</div>`;
                    } else {
                        content = `<div class="result-text">无图像生成</div>`;
                    }
                    break;
            }

            card.innerHTML = `
                <div class="result-header">
                    <span class="result-title">#${index + 1}</span>
                    <span class="result-time">${timeStr}</span>
                </div>
                <div class="result-content">
                    ${content}
                </div>
            `;

            return card;
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
        }

        // 生成错误
        function generationError(error) {
            const btn = document.getElementById('generateBtn');
            btn.disabled = false;
            btn.textContent = '🚀 开始生成';
            alert('生成失败: ' + error);
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


@app.get("/api/config/check")
async def check_config():
    """检查配置状态"""
    from app.config import config
    return {
        "llm_configured": bool(config.api.llm_api_key),
        "llm_provider": config.api.llm_provider,
        "llm_model": config.api.llm_model
    }


@app.post("/api/generate")
async def start_generation(request: GenerateRequest):
    """开始生成"""
    print(f"[DEBUG] /api/generate called: text={request.text[:50]}, style={request.style}")
    session = create_session(request.text, request.style, request.resolution)
    print(f"[DEBUG] Session created: {session.id}")

    # 直接启动异步任务（更可靠）
    print(f"[DEBUG] Starting async task...")
    asyncio.create_task(run_generation_task(session.id))
    print(f"[DEBUG] Async task created")

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


@app.post("/api/regenerate_stage")
async def regenerate_stage_api(request: RegenerateRequest, background_tasks: BackgroundTasks):
    """重新生成指定阶段"""
    session = get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 启动后台重新生成任务
    background_tasks.add_task(run_stage_regeneration, request.session_id, request.stage_id)

    return {
        "success": True,
        "message": f"开始重新生成阶段: {request.stage_id}"
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
    uvicorn.run("app.web:app", host="0.0.0.0", port=8000, reload=True)

