from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ...core.bus import bus

router = APIRouter()


@router.websocket("/alerts")
async def alerts_ws(ws: WebSocket):
    """Push channel: {'type':'incident', ...} on every new POSSIBLE_EMERGENCY,
    {'type':'incident_updated', ...} on verify/dismiss/review."""
    await ws.accept()
    await bus.connect(ws)
    await ws.send_json({"type": "connected", "subscribers": bus.subscribers})
    try:
        while True:
            await ws.receive_text()  # client pings ignored; keeps socket open
    except WebSocketDisconnect:
        await bus.disconnect(ws)
