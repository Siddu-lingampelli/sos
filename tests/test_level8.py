"""Level 8 tests: alert bus, incident schemas, WS handshake (no DB needed)."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.bus import AlertBus
from app.schemas import IncidentUpdate
from app.models import IncidentStatus


class FakeWS:
    def __init__(self):
        self.sent = []

    async def send_json(self, msg):
        self.sent.append(msg)


def test_bus_broadcast_and_disconnect():
    async def go():
        bus = AlertBus()
        a, b = FakeWS(), FakeWS()
        await bus.connect(a)
        await bus.connect(b)
        # After connect, first message is "connected", broadcast comes after
        n = await bus.broadcast({"type": "incident", "id": 7})
        assert n == 2
        # a.sent[0] is the "connected" handshake, [1] is the broadcast
        assert a.sent[1]["id"] == 7 and b.sent[1]["id"] == 7
        await bus.disconnect(a)
        await bus.broadcast({"type": "ping"})
        assert len(a.sent) == 2 and len(b.sent) == 3
        assert bus.subscribers == 1

    asyncio.run(go())


def test_bus_dead_socket_pruned():
    class DeadWS(FakeWS):
        async def send_json(self, msg):
            raise RuntimeError("gone")

    async def go():
        bus = AlertBus()
        await bus.connect(DeadWS())
        await bus.broadcast({"type": "ping"})
        assert bus.subscribers == 0

    asyncio.run(go())


def test_bus_broadcast_sync_without_loop_is_noop():
    bus = AlertBus()  # never connected -> no loop -> must not raise
    bus.broadcast_sync({"type": "ping"})


def test_incident_update_schema():
    ok = IncidentUpdate(status=IncidentStatus.VERIFIED)
    assert ok.status == IncidentStatus.VERIFIED
    try:
        IncidentUpdate(status="BOGUS")  # type: ignore[arg-type]
        raise AssertionError("should have raised")
    except Exception:
        pass


def test_ws_handshake():
    """The WS refuses anonymous and ?token= handshakes, and accepts a
    single-use ticket minted over the authed channel.
    """
    from fastapi.testclient import TestClient
    from app.core.config import settings
    from main import app

    client = TestClient(app)

    with client.websocket_connect("/api/ws/alerts") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "error"
        assert msg["detail"] == "unauthorized"

    # A long-lived JWT in the URL is no longer accepted either.
    with client.websocket_connect("/api/ws/alerts?token=fake.jwt.token") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "error"

    # The flag no longer opens anything (fail-closed).
    original = settings.AUTH_REQUIRED
    settings.AUTH_REQUIRED = False
    try:
        with client.websocket_connect("/api/ws/alerts") as ws:
            msg = ws.receive_json()
            assert msg["type"] == "error"
    finally:
        settings.AUTH_REQUIRED = original

    # Positive path: mint a ticket as an authed user and connect with it.
    from helpers import authed_client
    authed = authed_client()
    ticket = authed.post("/api/stream/ticket").json()["ticket"]
    from app.core.bus import bus as _bus
    with _bus._lock:
        _bus._backlog.clear()
    with authed.websocket_connect(f"/api/ws/alerts?ticket={ticket}") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "connected"
