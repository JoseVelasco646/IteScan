from fastapi import WebSocket
from typing import List, Set
import json
import asyncio

class WebSocketManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self.cancelled_scans: Set[str] = set()  # IDs de scans cancelados

    async def connect(self, websocket: WebSocket):
        """Acepta y registra una nueva conexión WebSocket"""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)

    async def disconnect(self, websocket: WebSocket):
        """Desconecta y elimina un WebSocket"""
        async with self._lock:
            self.active_connections.discard(websocket)

    def cancel_scan(self, scan_id: str):
        """Marca un scan como cancelado"""
        self.cancelled_scans.add(scan_id)

    def is_scan_cancelled(self, scan_id: str) -> bool:
        """Verifica si un scan ha sido cancelado"""
        return scan_id in self.cancelled_scans

    def clear_scan(self, scan_id: str):
        """Limpia un scan del registro de cancelados"""
        self.cancelled_scans.discard(scan_id)

    async def broadcast(self, event_type: str, data: dict):
        """Envía un mensaje a todos los clientes conectados de forma no bloqueante"""
        if not self.active_connections:
            return
            
        message = json.dumps({
            "type": event_type,
            "data": data
        })
        
        # Obtener copia rápida de conexiones sin bloquear mucho
        async with self._lock:
            connections = list(self.active_connections)
        
        # Enviar mensajes sin esperar - fire and forget
        for connection in connections:
            asyncio.create_task(self._send_to_connection(connection, message))
    
    async def _send_to_connection(self, connection: WebSocket, message: str):
        """Envía mensaje a una conexión específica y maneja errores"""
        try:
            await connection.send_text(message)
        except Exception as e:
            # Si falla, remover la conexión
            async with self._lock:
                self.active_connections.discard(connection)

    async def send_schedule_update(self, schedule_data: dict):
        """Notifica cambios en schedules"""
        await self.broadcast("schedule_update", schedule_data)

    async def send_scan_update(self, scan_data: dict):
        """Notifica cambios en scans"""
        await self.broadcast("scan_update", scan_data)

    async def send_host_update(self, host_data: dict):
        """Notifica cambios en hosts"""
        await self.broadcast("host_update", host_data)

# Instancia global del WebSocket manager
ws_manager = WebSocketManager()
