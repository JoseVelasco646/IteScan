from fastapi import WebSocket
from typing import List, Set, Dict, Optional
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[WebSocket, Optional[int]] = {}
        self._lock = asyncio.Lock()
        self.cancelled_scans: Set[str] = set()
        self.scan_owners: Dict[str, int] = {}

    async def connect(self, websocket: WebSocket, user_id: int = None):
        await websocket.accept()
        async with self._lock:
            self.active_connections[websocket] = user_id
        logger.info(f"[WS] User {user_id} connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            self.active_connections.pop(websocket, None)

    def register_scan(self, scan_id: str, user_id: int):
        self.scan_owners[scan_id] = user_id
        logger.info(f"[WS] Scan {scan_id[:8]} registered to user_id={user_id}")

    def unregister_scan(self, scan_id: str):
        self.scan_owners.pop(scan_id, None)

    def schedule_unregister(self, scan_id: str, delay: float = 10.0):
        async def _delayed_unregister():
            await asyncio.sleep(delay)
            self.scan_owners.pop(scan_id, None)
        asyncio.create_task(_delayed_unregister())

    def cancel_scan(self, scan_id: str):
        self.cancelled_scans.add(scan_id)

    def is_scan_cancelled(self, scan_id: str) -> bool:
        return scan_id in self.cancelled_scans

    def clear_scan(self, scan_id: str):
        self.cancelled_scans.discard(scan_id)
        self.scan_owners.pop(scan_id, None)

    async def send_to_user(self, user_id: int, event_type: str, data: dict):
        message = json.dumps({"type": event_type, "data": data})
        async with self._lock:
            connections = [ws for ws, uid in self.active_connections.items() if uid == user_id]
        for connection in connections:
            asyncio.create_task(self._send_to_connection(connection, message))

    async def broadcast(self, event_type: str, data: dict):
        if event_type == "scan_progress" and "scan_id" in data:
            scan_id = data["scan_id"]
            user_id = self.scan_owners.get(scan_id)
            logger.info(f"[WS] scan_progress for {scan_id[:8]}: owner={user_id}, owners_map={list(self.scan_owners.keys())[:3]}")
            if user_id is not None:
                await self.send_to_user(user_id, event_type, data)
                return
            else:
                logger.warning(f"[WS] No owner for scan {scan_id[:8]}, broadcasting to ALL")

        if not self.active_connections:
            return
            
        message = json.dumps({
            "type": event_type,
            "data": data
        })
        
        async with self._lock:
            connections = list(self.active_connections.keys())
        
        for connection in connections:
            asyncio.create_task(self._send_to_connection(connection, message))
    
    async def _send_to_connection(self, connection: WebSocket, message: str):
        try:
            await connection.send_text(message)
        except Exception as e:
            async with self._lock:
                self.active_connections.pop(connection, None)

    async def send_schedule_update(self, schedule_data: dict):
        await self.broadcast("schedule_update", schedule_data)

    async def send_scan_update(self, scan_data: dict):
        await self.broadcast("scan_update", scan_data)

    async def send_host_update(self, host_data: dict):
        await self.broadcast("host_update", host_data)

ws_manager = WebSocketManager()
