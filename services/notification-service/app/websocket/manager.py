"""
WebSocket Connection Manager - Singleton

Manages active WebSocket connections and broadcasts messages
to all connected clients in real-time.
"""
import asyncio
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Thread-safe WebSocket connection manager.

    Handles connect/disconnect lifecycle and broadcasts
    JSON messages to all active connections.
    """

    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
            count = len(self.active_connections)
        logger.info("WebSocket connected. Active connections: %d", count)

    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection from the active list."""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            count = len(self.active_connections)
        logger.info("WebSocket disconnected. Active connections: %d", count)

    async def broadcast(self, message: dict):
        """
        Send a JSON message to all active connections.

        Dead connections are cleaned up automatically.
        """
        dead_connections: list[WebSocket] = []

        async with self._lock:
            connections = list(self.active_connections)

        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                logger.warning("Dead WebSocket detected, removing")
                dead_connections.append(connection)

        if dead_connections:
            async with self._lock:
                for dead in dead_connections:
                    if dead in self.active_connections:
                        self.active_connections.remove(dead)
                count = len(self.active_connections)
            logger.info(
                "Cleaned up %d dead connections. Active: %d",
                len(dead_connections),
                count,
            )


# Singleton instance
manager = ConnectionManager()
