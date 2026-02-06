"""
FrameLeap Web界面

按照新流程图展示4大阶段8个子阶段：
- 阶段1: 输入层 (1.0)
- 阶段2: 故事创作层 (2.1-2.4)
- 阶段3: 制作层 (3.1-3.2)
- 阶段4: 输出层 (4.0)
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
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


# 阶段定义 - 按照新流程图：4大阶段8个子阶段
STAGE_DEFINITIONS = {
    # 阶段1: 输入层
    "1_0": {
        "id": "1_0",
        "name": "📥 输入处理",
        "short_name": "输入处理",
        "stage": "1",
        "sub_stage": "1.0",
        "description": "处理用户输入文本，获取风格配置",
        "icon": "📥",
        "color": "#6c757d",
        "details": ["预处理文本", "获取风格配置", "验证输入"],
        "outputs": ["输入文本", "风格", "分辨率"]
    },

    # 阶段2: 故事创作层
    "2_1": {
        "id": "2_1",
        "name": "📜 剧本生成",
        "short_name": "剧本生成",
        "stage": "2",
        "sub_stage": "2.1",
        "description": "调用千问LLM分析文本，生成完整剧本结构",
        "icon": "📜",
        "color": "#4facfe",
        "details": ["构建LLM提示词", "调用千问API", "解析生成结果", "提取场景和角色"],
        "outputs": ["剧本结构", "场景列表", "角色数据"]
    },
    "2_2": {
        "id": "2_2",
        "name": "🎨 画面描述+运镜规划",
        "short_name": "画面描述",
        "stage": "2",
        "sub_stage": "2.2",
        "description": "为每个场景生成详细的画面描述和AI绘画提示词，规划运镜方案",
        "icon": "🎨",
        "color": "#f59e0b",
        "details": ["分析场景内容", "构建画面描述", "生成AI绘画提示词", "规划景别运镜转场"],
        "outputs": ["场景提示词", "运镜方案"]
    },
    "2_3": {
        "id": "2_3",
        "name": "🖼️ 图像生成",
        "short_name": "图像生成",
        "stage": "2",
        "sub_stage": "2.3",
        "description": "使用通义万相模型为每个场景生成高质量图像",
        "icon": "🖼️",
        "color": "#10b981",
        "details": ["连接通义万相API", "生成场景图像", "保存图像文件"],
        "outputs": ["场景图像"]
    },
    "2_4": {
        "id": "2_4",
        "name": "🔊 音频生成",
        "short_name": "音频生成",
        "stage": "2",
        "sub_stage": "2.4",
        "description": "生成配音（TTS）和背景音乐",
        "icon": "🔊",
        "color": "#8b5cf6",
        "details": ["TTS语音生成", "BGM音乐选择/生成", "音频混音", "上传至公网URL"],
        "outputs": ["音频文件URL"]
    },

    # 阶段3: 制作层
    "3_1": {
        "id": "3_1",
        "name": "🎬 视频生成",
        "short_name": "视频生成",
        "stage": "3",
        "sub_stage": "3.1",
        "description": "使用通义万相wan2.6-i2v将图片+音频生成视频",
        "icon": "🎬",
        "color": "#ec4899",
        "details": ["根据运镜方案构建API参数", "调用wan2.6-i2v API", "轮询任务状态", "下载视频到本地"],
        "outputs": ["视频片段"]
    },
    "3_2": {
        "id": "3_2",
        "name": "🎞️ 视频拼接",
        "short_name": "视频拼接",
        "stage": "3",
        "sub_stage": "3.2",
        "description": "将多个场景视频拼接成完整视频",
        "icon": "🎞️",
        "color": "#f43f5e",
        "details": ["根据转场方案生成拼接命令", "FFmpeg拼接处理", "添加转场效果"],
        "outputs": ["完整视频文件"]
    },

    # 阶段4: 输出层
    "4_0": {
        "id": "4_0",
        "name": "📤 输出交付",
        "short_name": "输出交付",
        "stage": "4",
        "sub_stage": "4.0",
        "description": "格式化并打包交付文件",
        "icon": "📤",
        "color": "#14b8a6",
        "details": ["生成视频缩略图", "保存元数据JSON", "打包输出目录"],
        "outputs": ["最终视频包"]
    },
}

# 阶段分组
STAGE_GROUPS = {
    "1": {
        "id": "1",
        "name": "阶段1: 输入层",
        "icon": "📥",
        "stages": ["1_0"]
    },
    "2": {
        "id": "2",
        "name": "阶段2: 故事创作层",
        "icon": "📖",
        "stages": ["2_1", "2_2", "2_3", "2_4"]
    },
    "3": {
        "id": "3",
        "name": "阶段3: 制作层",
        "icon": "🎬",
        "stages": ["3_1", "3_2"]
    },
    "4": {
        "id": "4",
        "name": "阶段4: 输出层",
        "icon": "📤",
        "stages": ["4_0"]
    },
}

# 阶段执行顺序
STAGE_ORDER = ["1_0", "2_1", "2_2", "2_3", "2_4", "3_1", "3_2", "4_0"]

# 阶段依赖关系（哪些阶段需要前置阶段完成）
STAGE_DEPENDENCIES = {
    "1_0": [],
    "2_1": ["1_0"],
    "2_2": ["2_1"],
    "2_3": ["2_2"],
    "2_4": ["2_1"],
    "3_1": ["2_2", "2_3", "2_4"],
    "3_2": ["2_2", "3_1"],
    "4_0": ["3_2"],
}


@dataclass
class StageNode:
    """阶段节点"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    stage_id: str = ""  # 阶段ID (如 2_1, 2_2 等)
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
    input_node = session.get_node("1_0")
    input_node.status = StageStatus.SUCCESS
    input_node.start_time = datetime.now()
    input_node.end_time = datetime.now()
    input_node.output = {
        "input_text": input_text,
        "style": style,
        "resolution": resolution
    }

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

    执行完整流程，通过 WebSocket 推送进度更新
    当前实现：阶段1(输入) + 阶段2(故事创作: 2.1剧本 2.2画面 2.3图像)
    """
    print(f"[DEBUG] run_generation_task started for session {session_id}")
    session = get_session(session_id)
    if not session:
        print(f"[DEBUG] Session not found: {session_id}")
        return

    # 阶段执行顺序（当前实现到2.4）
    implemented_stages = ["1_0", "2_1", "2_2", "2_3", "2_4"]

    # 创建进度队列
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
                for sid, sdef in STAGE_DEFINITIONS.items():
                    if sdef["short_name"] == stage_name or sdef["name"] == stage_name:
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

        # 创建同步回调
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

        # 创建生成器并设置回调
        import time
        start = time.time()
        generator = Generator(cfg=config)
        elapsed = time.time() - start
        print(f"[DEBUG] Generator created in {elapsed:.2f}s")
        generator._progress_callback = sync_progress_callback
        generator._error_callback = sync_error_callback

        print(f"[DEBUG] Starting generation for session {session_id}")

        # 执行生成（在线程池中运行）
        result = await asyncio.to_thread(
            generator.generate,
            text=session.input_text,
            style=session.style,
            resolution=session.resolution
        )

        print(f"[DEBUG] Generation completed: success={result.success}")

        # 等待队列处理完毕
        await progress_queue.join()
        await error_queue.join()

        # 取消分发器任务
        progress_task.cancel()
        error_task.cancel()
        await asyncio.gather(progress_task, error_task, return_exceptions=True)

        # 更新所有已实现阶段的状态
        for stage_id in implemented_stages:
            node = session.get_node(stage_id)
            if not node:
                continue

            if result.success:
                node.status = StageStatus.SUCCESS
                node.end_time = datetime.now()
                if node.start_time is None:
                    node.start_time = node.end_time

                # 收集输出数据
                if stage_id == "1_0":
                    node.output = {
                        "input_text": session.input_text,
                        "style": session.style,
                        "resolution": session.resolution
                    }
                elif stage_id == "2_1" and result.script:
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
                elif stage_id == "2_2":
                    # 场景描述阶段
                    node.output = {
                        "description_count": len(result.script.scenes) if result.script else 0,
                        "scenes_prepared": len(result.script.scenes) if result.script else 0
                    }
                elif stage_id == "2_3" and result.images:
                    node.output = {"image_paths": result.images}
                elif stage_id == "2_4" and result.audio:
                    # 序列化音频数据
                    tracks_data = []
                    if result.audio.tracks:
                        for track in result.audio.tracks:
                            tracks_data.append({
                                "id": track.id,
                                "type": track.type,
                                "source": track.source,
                                "duration": track.duration
                            })
                    node.output = {
                        "track_count": len(result.audio.tracks) if result.audio.tracks else 0,
                        "tracks": tracks_data
                    }

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

        # 标记未实现的阶段为跳过
        for stage_id in STAGE_DEFINITIONS:
            if stage_id not in implemented_stages:
                node = session.get_node(stage_id)
                if node and node.status == StageStatus.PENDING:
                    node.status = StageStatus.SKIPPED
                    node.output = {"message": "该阶段尚未实现"}

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
        import traceback
        traceback.print_exc()
        # 标记当前运行中的阶段为失败
        for stage_id in implemented_stages:
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

    # 验证阶段ID
    if stage_id not in STAGE_DEFINITIONS:
        await manager.broadcast_to_session(session_id, {
            "type": "error",
            "error": f"无效的阶段ID: {stage_id}"
        })
        return

    # 检查依赖
    dependencies = STAGE_DEPENDENCIES.get(stage_id, [])
    for dep_id in dependencies:
        dep_node = session.get_node(dep_id)
        if not dep_node or dep_node.status != StageStatus.SUCCESS:
            await manager.broadcast_to_session(session_id, {
                "type": "error",
                "error": f"依赖阶段 {STAGE_DEFINITIONS[dep_id]['short_name']} 未完成"
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
        try:
            while True:
                stage_name, progress = await progress_queue.get()
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
        progress_task = asyncio.create_task(progress_dispatcher())
        error_task = asyncio.create_task(error_dispatcher())

        from app.generator import Generator
        from app.config import config

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

        generator = Generator(cfg=config)
        generator._progress_callback = sync_progress_callback
        generator._error_callback = sync_error_callback

        # 根据阶段执行不同的生成逻辑
        if stage_id == "2_1":
            # 重新生成剧本
            script = await asyncio.to_thread(
                generator.generate_script,
                session.input_text,
                session.style
            )
            if script:
                scenes_data = []
                for scene in script.scenes:
                    scenes_data.append({
                        "order": scene.order,
                        "title": scene.title,
                        "description": scene.description,
                        "atmosphere": scene.atmosphere
                    })

                characters_data = []
                for char_id, char in script.characters.items():
                    characters_data.append({
                        "id": char_id,
                        "name": char.name,
                        "type": char.character_type.value if hasattr(char.character_type, 'value') else str(char.character_type),
                        "description": char.description,
                        "personality": char.personality if hasattr(char, 'personality') else [],
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

        elif stage_id == "2_2":
            # 场景描述需要重新生成（暂不支持）
            node.output = {
                "description_count": 0,
                "scenes_prepared": 0
            }
            node.status = StageStatus.SKIPPED
            node.error_message = "该阶段暂不支持单独重新生成"

        elif stage_id == "2_3":
            # 重新生成图像
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

        elif stage_id == "2_4":
            # 重新生成音频
            audio_data = await asyncio.to_thread(
                generator.generate_audio,
                session.input_text,
                session.style,
                session.resolution
            )
            if audio_data:
                # 序列化音频数据
                tracks_data = []
                if audio_data.tracks:
                    for track in audio_data.tracks:
                        tracks_data.append({
                            "id": track.id,
                            "type": track.type,
                            "source": track.source,
                            "duration": track.duration
                        })
                node.output = {
                    "track_count": len(audio_data.tracks) if audio_data.tracks else 0,
                    "tracks": tracks_data
                }
                node.status = StageStatus.SUCCESS
            else:
                node.status = StageStatus.FAILED
                node.error_message = "音频生成失败"

        else:
            node.status = StageStatus.SKIPPED
            node.error_message = "该阶段暂不支持重新生成"

        node.end_time = datetime.now()
        if node.start_time is None:
            node.start_time = node.end_time

        await progress_queue.join()
        await error_queue.join()

        progress_task.cancel()
        error_task.cancel()
        await asyncio.gather(progress_task, error_task, return_exceptions=True)

        await manager.broadcast_to_session(session_id, {
            "type": "stage_update",
            "stage_id": stage_id,
            "status": node.status.value,
            "output": node.output,
            "duration": node.duration,
            "is_regeneration": True
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
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
    llm_configured = bool(config.api.llm_api_key)

    # 将阶段定义转换为JSON字符串
    stages_json = json.dumps(STAGE_DEFINITIONS, ensure_ascii=False)
    groups_json = json.dumps(STAGE_GROUPS, ensure_ascii=False)
    order_json = json.dumps(STAGE_ORDER, ensure_ascii=False)
    deps_json = json.dumps(STAGE_DEPENDENCIES, ensure_ascii=False)

    # 读取HTML模板
    html_template = Path(__file__).parent / "templates" / "index.html"
    if not html_template.exists():
        # 如果模板文件不存在，返回内嵌的HTML
        return HTMLResponse(content=get_embedded_html(stages_json, groups_json, order_json, deps_json, llm_configured))

    html_content = html_template.read_text(encoding='utf-8')
    html_content = html_content.replace('__STAGE_DEFINITIONS__', stages_json)
    html_content = html_content.replace('__STAGE_GROUPS__', groups_json)
    html_content = html_content.replace('__STAGE_ORDER__', order_json)
    html_content = html_content.replace('__STAGE_DEPENDENCIES__', deps_json)
    html_content = html_content.replace('__LLM_CONFIGURED__', str(llm_configured).lower())

    return HTMLResponse(content=html_content)




@app.get("/api/config/check")
async def check_config():
    """检查配置状态"""
    return {
        "llm_configured": bool(config.api.llm_api_key),
        "llm_provider": config.api.llm_provider,
        "llm_model": config.api.llm_model
    }


@app.post("/api/generate")
async def start_generation(request: GenerateRequest):
    """开始生成"""
    session = create_session(request.text, request.style, request.resolution)
    asyncio.create_task(run_generation_task(session.id))
    return {
        "session_id": session.id,
        "stages": STAGE_DEFINITIONS
    }


@app.post("/api/regenerate_stage")
async def regenerate_stage_api(request: RegenerateRequest, background_tasks: BackgroundTasks):
    """重新生成指定阶段"""
    session = get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    background_tasks.add_task(run_stage_regeneration, request.session_id, request.stage_id)

    return {
        "success": True,
        "message": f"开始重新生成阶段: {request.stage_id}"
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
    await websocket.accept()

    session_id = None

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "subscribe":
                session_id = data.get("session_id")
                session = get_session(session_id)

                if session:
                    await manager.connect(websocket, session_id)

                    # 发送当前会话状态
                    await websocket.send_json({
                        "type": "session_init",
                        "session_id": session.id,
                        "stages": STAGE_DEFINITIONS,
                        "groups": STAGE_GROUPS,
                        "order": STAGE_ORDER,
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

def get_embedded_html(stages_json: str, groups_json: str, order_json: str, deps_json: str, llm_configured: bool) -> str:
    """获取内嵌的HTML内容"""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FrameLeap - 动态漫生成</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f1f5f9;
            color: #1e293b;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1800px;
            margin: 0 auto;
            padding: 20px;
        }}

        /* 标题 */
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 30px 0;
            background: linear-gradient(135deg, #2563eb 0%, #3b82f6 50%, #06b6d4 100%);
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(37, 99, 235, 0.15);
        }}
        .header h1 {{
            color: #ffffff;
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        .header p {{
            color: rgba(255, 255, 255, 0.9);
            font-size: 1.1em;
        }}

        /* 配置警告 */
        .config-warning {{
            background: #fff7ed;
            border: 2px solid #f59e0b;
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 20px;
            display: {'flex' if not llm_configured else 'none'};
            align-items: center;
            gap: 16px;
        }}
        .warning-content {{
            display: flex;
            align-items: center;
            gap: 12px;
            flex: 1;
        }}
        .warning-icon {{ font-size: 28px; }}
        .warning-text {{
            color: #92400e;
            font-size: 14px;
        }}

        /* 输入区域 */
        .input-section {{
            background: #ffffff;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }}
        .input-group {{ margin-bottom: 15px; }}
        .input-group label {{
            display: block;
            margin-bottom: 10px;
            color: #334155;
            font-weight: 600;
            font-size: 14px;
        }}
        textarea {{
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
        }}
        textarea:focus {{
            outline: none;
            border-color: #2563eb;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
            background: #ffffff;
        }}
        .controls {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            margin-top: 20px;
        }}
        select {{
            flex: 1;
            min-width: 150px;
            padding: 12px 16px;
            border-radius: 10px;
            background: #f8fafc;
            color: #334155;
            border: 1px solid #cbd5e1;
            cursor: pointer;
            font-size: 14px;
        }}
        .btn {{
            padding: 12px 32px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 15px;
            font-weight: 600;
            transition: all 0.2s;
        }}
        .btn-primary {{
            background: linear-gradient(135deg, #2563eb, #3b82f6);
            color: #ffffff;
            box-shadow: 0 2px 10px rgba(37, 99, 235, 0.2);
        }}
        .btn-primary:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
        }}
        .btn-primary:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }}

        /* 进度条 */
        .progress-section {{
            background: #ffffff;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            display: none;
            border: 1px solid #e2e8f0;
        }}
        .progress-section.active {{ display: block; }}
        .progress-bar-container {{
            height: 6px;
            background: #f1f5f9;
            border-radius: 3px;
            overflow: hidden;
            margin-bottom: 10px;
        }}
        .progress-bar {{
            height: 100%;
            background: linear-gradient(90deg, #2563eb, #3b82f6, #06b6d4);
            border-radius: 3px;
            transition: width 0.4s ease;
            width: 0%;
        }}
        .progress-text {{
            text-align: center;
            color: #64748b;
            font-size: 14px;
        }}

        /* 流程展示区域 */
        .flow-section {{ display: none; }}
        .flow-section.active {{ display: block; }}

        /* 阶段分组 */
        .stage-group {{
            margin-bottom: 24px;
        }}
        .group-header {{
            background: linear-gradient(135deg, #e0e7ff 0%, #f3e8ff 100%);
            border-radius: 12px;
            padding: 16px 24px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 12px;
            border: 1px solid #c7d2fe;
        }}
        .group-icon {{ font-size: 28px; }}
        .group-name {{
            font-size: 18px;
            font-weight: 700;
            color: #3730a3;
        }}
        .group-stages {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}

        /* 阶段行 */
        .stage-row {{
            display: flex;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            overflow: hidden;
            transition: all 0.3s;
        }}
        .stage-row:hover {{
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        }}

        /* 左侧阶段信息 */
        .stage-info {{
            flex-shrink: 0;
            width: 320px;
            padding: 16px 20px;
            border-right: 1px solid #e2e8f0;
            background: #f8fafc;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .stage-info-icon {{ font-size: 32px; flex-shrink: 0; }}
        .stage-info-text {{ flex: 1; min-width: 0; }}
        .stage-info-name {{
            font-weight: 600;
            font-size: 15px;
            color: #1e293b;
            margin-bottom: 4px;
        }}
        .stage-info-sub {{
            font-size: 11px;
            color: #64748b;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .stage-info-desc {{
            font-size: 12px;
            color: #94a3b8;
            line-height: 1.4;
        }}

        /* 状态指示器 */
        .stage-status-indicator {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            flex-shrink: 0;
        }}
        .status-pending {{ background: #cbd5e1; }}
        .status-running {{
            background: #f59e0b;
            animation: pulse 1.5s infinite;
        }}
        .status-success {{ background: #10b981; }}
        .status-failed {{ background: #ef4444; }}
        .status-skipped {{ background: #94a3b8; }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}

        /* 重新生成按钮 */
        .stage-regenerate-btn {{
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
        }}
        .stage-regenerate-btn:hover:not(:disabled) {{
            background: #f8fafc;
            border-color: #2563eb;
            color: #2563eb;
        }}
        .stage-regenerate-btn:disabled {{
            opacity: 0.4;
            cursor: not-allowed;
        }}

        /* 右侧结果区域 */
        .stage-results {{
            flex: 1;
            padding: 20px;
            display: flex;
            gap: 16px;
            overflow-x: auto;
            min-height: 120px;
            align-items: stretch;
        }}
        .stage-results::-webkit-scrollbar {{
            height: 8px;
        }}
        .stage-results::-webkit-scrollbar-track {{
            background: #f1f5f9;
            border-radius: 4px;
        }}
        .stage-results::-webkit-scrollbar-thumb {{
            background: #cbd5e1;
            border-radius: 4px;
        }}

        /* 空状态 */
        .empty-state {{
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #94a3b8;
            font-size: 14px;
        }}

        /* 结果卡片 */
        .result-card {{
            flex-shrink: 0;
            width: 300px;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            overflow: hidden;
            transition: all 0.2s;
        }}
        .result-card:hover {{
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
        }}
        .result-header {{
            padding: 12px 16px;
            background: #f8fafc;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .result-title {{
            font-size: 13px;
            font-weight: 600;
            color: #334155;
        }}
        .result-time {{
            font-size: 11px;
            color: #94a3b8;
        }}
        .result-content {{
            padding: 16px;
            max-height: 280px;
            overflow-y: auto;
        }}

        /* 结果内容样式 */
        .result-text {{
            font-size: 13px;
            line-height: 1.6;
            color: #334155;
        }}
        .result-text strong {{
            color: #2563eb;
            font-weight: 600;
        }}

        /* 场景列表 */
        .scene-list {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .scene-item {{
            padding: 10px 12px;
            background: #f8fafc;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }}
        .scene-title {{
            font-size: 13px;
            font-weight: 600;
            color: #2563eb;
            margin-bottom: 4px;
        }}
        .scene-desc {{
            font-size: 12px;
            color: #64748b;
            line-height: 1.4;
        }}

        /* 图像网格 */
        .image-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
        }}
        .image-item {{
            aspect-ratio: 16/10;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #e2e8f0;
            background: #f1f5f9;
        }}
        .image-item img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}

        /* 响应式 */
        @media (max-width: 768px) {{
            .stage-row {{ flex-direction: column; }}
            .stage-info {{ width: 100%; border-right: none; border-bottom: 1px solid #e2e8f0; }}
            .stage-results {{ flex-direction: column; }}
            .result-card {{ width: 100%; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 FrameLeap</h1>
            <p>AI驱动的动态漫生成系统 - 4大阶段8个子流程</p>
        </div>

        <!-- 配置警告 -->
        <div class="config-warning" id="configWarning">
            <div class="warning-content">
                <span class="warning-icon">⚠️</span>
                <div class="warning-text">
                    <strong>未配置千问 API Key</strong><br>
                    剧本生成将使用简化规则。请配置 API Key 以获得更好的生成效果。
                </div>
            </div>
        </div>

        <!-- 输入区域 -->
        <div class="input-section">
            <div class="input-group">
                <label>📝 输入你的故事</label>
                <textarea id="inputText" placeholder="输入你想要生成的故事...&#10;&#10;例如：&#10;一个少年在雨夜中遇到了神秘少女。少女告诉他，他是被选中的勇者，必须拯救即将崩塌的世界。"></textarea>
            </div>
            <div class="controls">
                <select id="style">
                    <option value="anime">🎨 日式动漫</option>
                    <option value="manhwa">📖 韩漫</option>
                    <option value="manhua">🏮 国漫</option>
                    <option value="watercolor">🎨 水彩风</option>
                    <option value="oil">🖼️ 油画风</option>
                </select>
                <select id="resolution">
                    <option value="1080p">📺 1080P 横屏</option>
                    <option value="1080p_v">📱 1080P 竖屏</option>
                    <option value="720p">📺 720P</option>
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
            <div id="pipelineContainer"></div>
        </div>
    </div>

    <script>
        let currentSessionId = null;
        let ws = null;
        const STAGE_DEFINITIONS = {stages_json};
        const STAGE_GROUPS = {groups_json};
        const STAGE_ORDER = {order_json};
        const STAGE_DEPENDENCIES = {deps_json};
        const stageResults = {{}};

        document.addEventListener('DOMContentLoaded', function() {{
            checkLLMConfig();
            renderInitialPipeline();
        }});

        function checkLLMConfig() {{
            const llmConfigured = {str(llm_configured).lower()};
            if (!llmConfigured || llmConfigured === 'false') {{
                document.getElementById('configWarning').style.display = 'flex';
            }}
        }}

        function renderInitialPipeline() {{
            const container = document.getElementById('pipelineContainer');
            container.innerHTML = '';

            for (const [groupId, group] of Object.entries(STAGE_GROUPS)) {{
                const groupDiv = document.createElement('div');
                groupDiv.className = 'stage-group';

                // 分组标题
                const header = document.createElement('div');
                header.className = 'group-header';
                header.innerHTML = `
                    <span class="group-icon">${{group.icon}}</span>
                    <span class="group-name">${{group.name}}</span>
                `;
                groupDiv.appendChild(header);

                // 阶段列表
                const stagesDiv = document.createElement('div');
                stagesDiv.className = 'group-stages';

                for (const stageId of group.stages) {{
                    const stageDef = STAGE_DEFINITIONS[stageId];
                    const row = createStageRow(stageId, stageDef);
                    stagesDiv.appendChild(row);
                }}

                groupDiv.appendChild(stagesDiv);
                container.appendChild(groupDiv);
            }}
        }}

        function createStageRow(stageId, stageDef) {{
            const row = document.createElement('div');
            row.className = 'stage-row';
            row.id = `stage-row-${{stageId}}`;

            row.innerHTML = `
                <div class="stage-info">
                    <span class="stage-info-icon">${{stageDef.icon}}</span>
                    <div class="stage-info-text">
                        <div class="stage-info-sub">${{stageDef.sub_stage}}</div>
                        <div class="stage-info-name">${{stageDef.short_name}}</div>
                        <div class="stage-info-desc">${{stageDef.description}}</div>
                    </div>
                    <button class="stage-regenerate-btn" id="regenerate-${{stageId}}" onclick="regenerateStage('${{stageId}}')" disabled>
                        🔄 重新生成
                    </button>
                    <div class="stage-status-indicator status-pending" id="status-${{stageId}}"></div>
                </div>
                <div class="stage-results" id="results-${{stageId}}">
                    <div class="empty-state">等待中...</div>
                </div>
            `;

            return row;
        }}

        async function startGeneration() {{
            const text = document.getElementById('inputText').value.trim();
            if (!text) {{
                alert('请输入故事内容');
                return;
            }}

            const btn = document.getElementById('generateBtn');
            btn.disabled = true;
            btn.textContent = '⏳ 生成中...';

            try {{
                const res = await fetch('/api/generate', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        text: text,
                        style: document.getElementById('style').value,
                        resolution: document.getElementById('resolution').value
                    }})
                }});

                const data = await res.json();
                if (data.error) {{
                    alert('启动失败: ' + data.error);
                    btn.disabled = false;
                    btn.textContent = '🚀 开始生成';
                    return;
                }}

                currentSessionId = data.session_id;
                renderInitialPipeline();
                document.getElementById('progressSection').classList.add('active');
                document.getElementById('flowSection').classList.add('active');
                connectWebSocket();

            }} catch (e) {{
                alert('请求失败: ' + e.message);
                btn.disabled = false;
                btn.textContent = '🚀 开始生成';
            }}
        }}

        function connectWebSocket() {{
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${{protocol}}//${{window.location.host}}/ws`;

            ws = new WebSocket(wsUrl);

            ws.onopen = () => {{
                console.log('WebSocket connected');
                if (currentSessionId) {{
                    ws.send(JSON.stringify({{
                        type: 'subscribe',
                        session_id: currentSessionId
                    }}));
                }}
            }};

            ws.onmessage = (event) => {{
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            }};

            ws.onclose = () => {{
                console.log('WebSocket disconnected');
                setTimeout(() => {{
                    if (currentSessionId) {{
                        connectWebSocket();
                    }}
                }}, 5000);
            }};

            ws.onerror = (error) => {{
                console.error('WebSocket error:', error);
            }};
        }}

        function handleWebSocketMessage(data) {{
            console.log('收到消息:', data);

            if (data.type === 'stage_update') {{
                updateStageStatus(data.stage_id, data.status);

                if (data.status === 'success' && data.output) {{
                    addResultCard(data.stage_id, data.output);
                }}

                // 更新进度
                let completed = 0;
                STAGE_ORDER.forEach(id => {{
                    const resultsContainer = document.getElementById(`results-${{id}}`);
                    if (resultsContainer && !resultsContainer.querySelector('.empty-state')) {{
                        completed++;
                    }}
                }});
                const progress = Math.min(completed / STAGE_ORDER.length, 1);
                const stageDef = STAGE_DEFINITIONS[data.stage_id];
                const isRegeneration = data.is_regeneration ? '重新' : '';
                updateProgress(progress, `${{isRegeneration}}${{stageDef ? stageDef.short_name : '处理中'}}`);

            }} else if (data.type === 'complete') {{
                generationComplete(data.output_path);
            }} else if (data.type === 'error') {{
                generationError(data.error);
            }}
        }}

        function updateStageStatus(stageId, status) {{
            const indicator = document.getElementById(`status-${{stageId}}`);
            if (indicator) {{
                indicator.className = `stage-status-indicator status-${{status}}`;
            }}

            // 更新重新生成按钮状态
            const regenerateBtn = document.getElementById(`regenerate-${{stageId}}`);
            if (regenerateBtn) {{
                // 检查依赖是否满足
                const deps = STAGE_DEPENDENCIES[stageId] || [];
                let canRegenerate = deps.every(depId => {{
                    const depIndicator = document.getElementById(`status-${{depId}}`);
                    return depIndicator && depIndicator.classList.contains('status-success');
                }});

                // 只对已实现的阶段允许重新生成
                const implementedStages = ['1_0', '2_1', '2_2', '2_3'];
                regenerateBtn.disabled = !canRegenerate || status === 'running' || !implementedStages.includes(stageId);
            }}
        }}

        async function regenerateStage(stageId) {{
            if (!currentSessionId) {{
                alert('请先生成完整流程');
                return;
            }}

            const regenerateBtn = document.getElementById(`regenerate-${{stageId}}`);
            regenerateBtn.disabled = true;
            regenerateBtn.textContent = '⏳ 生成中...';

            updateStageStatus(stageId, 'running');

            try {{
                const res = await fetch('/api/regenerate_stage', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        session_id: currentSessionId,
                        stage_id: stageId
                    }})
                }});

                const data = await res.json();
                if (data.error) {{
                    alert('重新生成失败: ' + data.error);
                    updateStageStatus(stageId, 'failed');
                }}
            }} catch (e) {{
                alert('请求失败: ' + e.message);
                updateStageStatus(stageId, 'failed');
            }} finally {{
                regenerateBtn.textContent = '🔄 重新生成';
            }}
        }}

        function addResultCard(stageId, output) {{
            const resultsContainer = document.getElementById(`results-${{stageId}}`);
            if (!resultsContainer) return;

            const emptyState = resultsContainer.querySelector('.empty-state');
            if (emptyState) {{
                emptyState.remove();
            }}

            if (!stageResults[stageId]) {{
                stageResults[stageId] = [];
            }}
            const resultIndex = stageResults[stageId].length;
            stageResults[stageId].push(output);

            const card = createResultCard(stageId, output, resultIndex);
            resultsContainer.appendChild(card);
            resultsContainer.scrollLeft = resultsContainer.scrollWidth;
        }}

        function createResultCard(stageId, output, index) {{
            const card = document.createElement('div');
            card.className = 'result-card';

            const now = new Date();
            const timeStr = `${{now.getHours().toString().padStart(2, '0')}}:${{now.getMinutes().toString().padStart(2, '0')}}:${{now.getSeconds().toString().padStart(2, '0')}}`;

            let content = '';

            switch(stageId) {{
                case '1_0':
                    content = `
                        <div class="result-text">
                            <div><strong>输入文本:</strong> ${{output.input_text || ''}}</div>
                            <div style="margin-top:8px;"><strong>风格:</strong> ${{output.style || 'anime'}}</div>
                            <div><strong>分辨率:</strong> ${{output.resolution || '1080p'}}</div>
                        </div>
                    `;
                    break;

                case '2_1':
                    content = `
                        <div class="result-text">
                            <div style="margin-bottom:8px;"><strong>标题:</strong> ${{output.title || '未命名'}}</div>
                            <div style="margin-bottom:8px;"><strong>类型:</strong> ${{output.story_type || '未知'}}</div>
                            <div style="margin-bottom:8px;"><strong>主题:</strong> ${{output.theme || '未知'}}</div>
                            <div style="margin-bottom:12px;"><strong>场景数:</strong> ${{output.scene_count || 0}} | <strong>角色数:</strong> ${{output.character_count || 0}}</div>
                        </div>
                    `;
                    if (output.scenes && output.scenes.length > 0) {{
                        content += `<div class="scene-list">`;
                        output.scenes.slice(0, 3).forEach(scene => {{
                            content += `
                                <div class="scene-item">
                                    <div class="scene-title">场景 ${{scene.order + 1}}: ${{scene.title}}</div>
                                    <div class="scene-desc">${{(scene.description || '').substring(0, 80)}}...</div>
                                </div>
                            `;
                        }});
                        if (output.scenes.length > 3) {{
                            content += `<div style="text-align:center;color:#94a3b8;font-size:12px;padding:8px;">...还有 ${{output.scenes.length - 3}} 个场景</div>`;
                        }}
                        content += `</div>`;
                    }}
                    break;

                case '2_2':
                    content = `
                        <div class="result-text">
                            <div><strong>已准备场景描述:</strong> ${{output.description_count || 0}} 个场景</div>
                        </div>
                    `;
                    break;

                case '2_3':
                    if (output.image_paths && output.image_paths.length > 0) {{
                        content = `<div class="image-grid">`;
                        output.image_paths.slice(0, 4).forEach((path, idx) => {{
                            const fileName = path.split(/[\\/]/).pop();
                            const imageUrl = '/temp/' + fileName;
                            content += `
                                <div class="image-item">
                                    <img src="${{imageUrl}}" alt="场景 ${{idx + 1}}" onerror="this.parentElement.innerHTML='<div style=\\'display:flex;align-items:center;justify-content:center;height:100%;color:#ef4444;font-size:11px;\\'>加载失败</div>'">
                                </div>
                            `;
                        }});
                        if (output.image_paths.length > 4) {{
                            content += `<div style="grid-column:1/-1;text-align:center;color:#94a3b8;font-size:12px;padding:8px;">...还有 ${{output.image_paths.length - 4}} 张图像</div>`;
                        }}
                        content += `</div>`;
                    }} else {{
                        content = `<div class="result-text">无图像生成</div>`;
                    }}
                    break;

                default:
                    content = `<div class="result-text">该阶段尚未实现</div>`;
                    break;
            }}

            card.innerHTML = `
                <div class="result-header">
                    <span class="result-title">#${{index + 1}}</span>
                    <span class="result-time">${{timeStr}}</span>
                </div>
                <div class="result-content">
                    ${{content}}
                </div>
            `;

            return card;
        }}

        function updateProgress(progress, message) {{
            const progressBar = document.getElementById('progressBar');
            const progressText = document.getElementById('progressText');

            progressBar.style.width = `${{progress * 100}}%`;
            progressText.textContent = `${{message}} (${{Math.round(progress * 100)}}%)`;
        }}

        function generationComplete(outputPath) {{
            const btn = document.getElementById('generateBtn');
            btn.disabled = false;
            btn.textContent = '🚀 开始生成';
            updateProgress(1, '生成完成！');
        }}

        function generationError(error) {{
            const btn = document.getElementById('generateBtn');
            btn.disabled = false;
            btn.textContent = '🚀 开始生成';
            alert('生成失败: ' + error);
        }}
    </script>
</body>
</html>
    """


@app.get("/api/config/check")
async def check_config():
    """检查配置状态"""
    return {
        "llm_configured": bool(config.api.llm_api_key),
        "llm_provider": config.api.llm_provider,
        "llm_model": config.api.llm_model
    }


@app.post("/api/generate")
async def start_generation(request: GenerateRequest):
    """开始生成"""
    session = create_session(request.text, request.style, request.resolution)
    asyncio.create_task(run_generation_task(session.id))
    return {
        "session_id": session.id,
        "stages": STAGE_DEFINITIONS
    }


@app.post("/api/regenerate_stage")
async def regenerate_stage_api(request: RegenerateRequest, background_tasks: BackgroundTasks):
    """重新生成指定阶段"""
    session = get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    background_tasks.add_task(run_stage_regeneration, request.session_id, request.stage_id)

    return {
        "success": True,
        "message": f"开始重新生成阶段: {request.stage_id}"
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
    await websocket.accept()

    session_id = None

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "subscribe":
                session_id = data.get("session_id")
                session = get_session(session_id)

                if session:
                    await manager.connect(websocket, session_id)

                    # 发送当前会话状态
                    await websocket.send_json({
                        "type": "session_init",
                        "session_id": session.id,
                        "stages": STAGE_DEFINITIONS,
                        "groups": STAGE_GROUPS,
                        "order": STAGE_ORDER,
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.web:app", host="0.0.0.0", port=8000, reload=True)
