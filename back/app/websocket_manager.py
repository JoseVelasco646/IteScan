from fastapi import WebSocket
from typing import List, Set
import json
import asyncio

class WebSocketManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self.cancelled_scans: Set[str] = set()  

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            self.active_connections.discard(websocket)

    def cancel_scan(self, scan_id: str):
        self.cancelled_scans.add(scan_id)

    def is_scan_cancelled(self, scan_id: str) -> bool:
        return scan_id in self.cancelled_scans

    def clear_scan(self, scan_id: str):
        self.cancelled_scans.discard(scan_id)

    async def broadcast(self, event_type: str, data: dict):
        if not self.active_connections:
            return
            
        message = json.dumps({
            "type": event_type,
            "data": data
        })
        
        async with self._lock:
            connections = list(self.active_connections)
        
        for connection in connections:
            asyncio.create_task(self._send_to_connection(connection, message))
    
    async def _send_to_connection(self, connection: WebSocket, message: str):
        try:
            await connection.send_text(message)
        except Exception as e:
            async with self._lock:
                self.active_connections.discard(connection)

    async def send_schedule_update(self, schedule_data: dict):
        await self.broadcast("schedule_update", schedule_data)

    async def send_scan_update(self, scan_data: dict):
        await self.broadcast("scan_update", scan_data)

    async def send_host_update(self, host_data: dict):
        await self.broadcast("host_update", host_data)

ws_manager = WebSocketManager()
