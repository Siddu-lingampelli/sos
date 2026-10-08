from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
from ...core.bus import bus
from ..deps import websocket_authorized, websocket_user
from ...db.session import SessionLocal

router = APIRouter()


@router.websocket("/alerts")
async def alerts_ws(ws: WebSocket):
    """Push channel: {'type':'incident'|'notification'|'activity'|'system', ...}.

    Auth: ?ticket=<single-use ticket from POST /api/stream/ticket>, or the
    session cookie on same-origin handshakes. Long-lived JWTs are never
    accepted in the URL. The server sends {"type":"ping"} every 25 s; clients
    reply with any frame so dead NAT bindings are noticed.
    """
    await ws.accept()
    token = ws.query_params.get("ticket")
    user = None
    if token:
        from ...core.security import consume_stream_ticket
        from ...models import User
        db = SessionLocal()
        try:
            email = consume_stream_ticket(token)
            if email:
                row = db.query(User).filter(User.email == email).first()
                user = row if row is not None and row.is_active else None
        finally:
            db.close()
    else:
        # Same-origin browsers send the httpOnly session cookie on the
        # handshake; use it when no ticket was presented.
        cookie_token = ws.cookies.get("sos_session")
        if cookie_token and websocket_authorized(cookie_token):
            db = SessionLocal()
            try:
                user = websocket_user(cookie_token, db)
            finally:
                db.close()
    # Accept token for auth, but also allow optional identity for future per-user filtering
    if user is None:
        # Reject invalid token even in dev mode to avoid silent connection leaks
        await ws.send_json({"type": "error", "detail": "unauthorized"})
        await ws.close(code=1008)
        return
    # Optional: open a short-lived DB session to resolve user for audit / future filtering
    # (currently not used for filtering; left as hook for per-user scopes)
    # db = SessionLocal(); user = websocket_user(token, db); db.close()
    await bus.connect(ws)
    import asyncio
    try:
        while True:
            try:
                # Heartbeat doubles as a dead-peer detector: a wedged socket
                # raises here and gets pruned from the bus.
                await asyncio.wait_for(ws.receive_text(), timeout=25.0)
            except asyncio.TimeoutError:
                if ws.client_state is not WebSocketState.CONNECTED:
                    break
                try:
                    await ws.send_json({"type": "ping"})
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    finally:
        await bus.disconnect(ws)
