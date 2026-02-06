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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.web:app", host="0.0.0.0", port=8000, reload=True)
