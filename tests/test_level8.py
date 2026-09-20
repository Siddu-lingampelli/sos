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
        n = await bus.broadcast({"type": "incident", "id": 7})
        assert n == 2
        assert a.sent[0]["id"] == 7 and b.sent[0]["id"] == 7
        await bus.disconnect(a)
        await bus.broadcast({"type": "ping"})
        assert len(a.sent) == 1 and len(b.sent) == 2
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
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    with client.websocket_connect("/api/ws/alerts") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "connected"
