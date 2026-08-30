import logging
from typing import List, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websockets"])

class ConnectionManager:
    """
    Manages active WebSocket connections and broadcasts real-time collaboration events.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcasts an event payload to all connected clients.
        """
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        for d in disconnected:
            self.disconnect(d)


ws_manager = ConnectionManager()


@router.websocket("/ws/collaboration")
async def websocket_collaboration_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time recruiter & hiring manager collaboration.
    Broadcasts live candidate status changes, comments, and interview notes.
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type", "COLLABORATION_EVENT")
            payload = data.get("payload", {})
            sender = data.get("sender", "Recruiter")

            # Broadcast received message to all connected peers
            broadcast_payload = {
                "type": event_type,
                "payload": payload,
                "sender": sender,
                "timestamp": data.get("timestamp")
            }
            await ws_manager.broadcast(broadcast_payload)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket error: {str(e)}")
        ws_manager.disconnect(websocket)
