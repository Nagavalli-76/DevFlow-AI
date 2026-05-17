from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# ─── CONNECTION MANAGER ───
class ConnectionManager:
    def __init__(self):
        # room_id -> list of websockets
        self.rooms: Dict[str, List[WebSocket]] = {}
        # ws -> user_id
        self.users: Dict[WebSocket, str] = {}

    async def connect(self, ws: WebSocket, room_id: str, user_id: str):
        await ws.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = []
        self.rooms[room_id].append(ws)
        self.users[ws] = user_id
        logger.info(f"User {user_id} joined room {room_id}")

        # Notify others
        await self.broadcast(room_id, {
            "type": "USER_JOINED",
            "userId": user_id,
            "message": f"User {user_id} joined"
        }, exclude=ws)

    def disconnect(self, ws: WebSocket, room_id: str):
        user_id = self.users.pop(ws, "unknown")
        if room_id in self.rooms:
            self.rooms[room_id] = [c for c in self.rooms[room_id] if c != ws]
            if not self.rooms[room_id]:
                del self.rooms[room_id]
        return user_id

    async def broadcast(self, room_id: str, message: dict, exclude: WebSocket = None):
        if room_id not in self.rooms:
            return
        dead = []
        for ws in self.rooms[room_id]:
            if ws == exclude:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.rooms[room_id].remove(ws)

    async def send_to_user(self, user_id: str, message: dict):
        for ws, uid in self.users.items():
            if uid == user_id:
                try:
                    await ws.send_json(message)
                except Exception:
                    pass

    def get_room_users(self, room_id: str) -> List[str]:
        if room_id not in self.rooms:
            return []
        return [self.users.get(ws, "unknown") for ws in self.rooms[room_id]]

manager = ConnectionManager()

# ─── WEBSOCKET ENDPOINTS ───

@router.websocket("/project/{project_id}")
async def project_ws(ws: WebSocket, project_id: str, user_id: str = "anonymous"):
    """Real-time collaboration for a project room"""
    await manager.connect(ws, f"project:{project_id}", user_id)
    try:
        while True:
            raw = await ws.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            event_type = data.get("type", "MESSAGE")

            if event_type == "CURSOR_MOVE":
                await manager.broadcast(f"project:{project_id}", {
                    "type": "CURSOR_MOVE",
                    "userId": user_id,
                    "position": data.get("position")
                }, exclude=ws)

            elif event_type == "TASK_UPDATE":
                await manager.broadcast(f"project:{project_id}", {
                    "type": "TASK_UPDATE",
                    "userId": user_id,
                    "taskId": data.get("taskId"),
                    "changes": data.get("changes")
                })

            elif event_type == "CHAT":
                await manager.broadcast(f"project:{project_id}", {
                    "type": "CHAT",
                    "userId": user_id,
                    "message": data.get("message"),
                })

            elif event_type == "PING":
                await ws.send_json({"type": "PONG"})

            elif event_type == "GET_USERS":
                await ws.send_json({
                    "type": "ROOM_USERS",
                    "users": manager.get_room_users(f"project:{project_id}")
                })

    except WebSocketDisconnect:
        uid = manager.disconnect(ws, f"project:{project_id}")
        await manager.broadcast(f"project:{project_id}", {
            "type": "USER_LEFT",
            "userId": uid,
        })
        logger.info(f"User {uid} left room project:{project_id}")

@router.websocket("/notifications/{user_id}")
async def notifications_ws(ws: WebSocket, user_id: str):
    """Personal notification channel"""
    await manager.connect(ws, f"notif:{user_id}", user_id)
    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "PING":
                await ws.send_json({"type": "PONG"})
    except WebSocketDisconnect:
        manager.disconnect(ws, f"notif:{user_id}")
