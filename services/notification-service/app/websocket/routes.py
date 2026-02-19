"""
WebSocket Routes - Real-time notification endpoint.
"""
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.websocket.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time notifications."""
    await manager.connect(websocket)

    try:
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to notifications",
        })

        while True:
            text = await websocket.receive_text()
            try:
                data = json.loads(text)
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error("WebSocket error: %s", e)
        await manager.disconnect(websocket)
