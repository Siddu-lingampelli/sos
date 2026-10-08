"""Process-wide alert bus: DB-backed incident firings fan out to dashboards.

Lives outside the API routers so both the HTTP layer (PATCH status changes)
and the background inference thread (stream.py) can publish without import
cycles. Thread-safe: socket bookkeeping happens on the event loop while
publishers from other threads schedule via run_coroutine_threadsafe.
"""
import asyncio
import threading
from collections import deque


class AlertBus:
    def __init__(self, backlog_size: int = 50):
        self._subs: set = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._lock = threading.Lock()
        # Messages published before any socket connects (e.g. a startup
        # incident) are kept here and replayed to the next subscriber, so
        # they don't vanish into a log line.
        self._backlog: deque[dict] = deque(maxlen=backlog_size)

    async def connect(self, ws) -> None:
        self._loop = asyncio.get_running_loop()
        pending: list = []
        with self._lock:
            self._subs.add(ws)
            if self._backlog:
                pending = list(self._backlog)
                self._backlog.clear()
        for msg in pending:
            try:
                await ws.send_json(msg)
            except Exception:
                break
        try:
            await ws.send_json({"type": "connected", "subscribers": len(self._subs)})
        except Exception:
            return

    async def disconnect(self, ws) -> None:
        with self._lock:
            self._subs.discard(ws)

    async def broadcast(self, msg: dict) -> int:
        dead = []
        subs_snapshot = list(self._subs)
        for ws in subs_snapshot:
            try:
                await ws.send_json(msg)
            except Exception:
                dead.append(ws)
        if dead:
            with self._lock:
                for ws in dead:
                    self._subs.discard(ws)
        return len(self._subs)

    def broadcast_sync(self, msg: dict) -> asyncio.Future | None:
        """Fire-and-forget publish safe to call from non-loop threads.

        Returns the future so callers can observe exceptions if needed.
        """
        loop = self._loop
        if loop is not None and loop.is_running():
            fut = asyncio.run_coroutine_threadsafe(self.broadcast(msg), loop)
            # Observe exceptions in this thread to avoid "Future exception was never retrieved" warnings
            fut.add_done_callback(lambda f: f.exception())
            return fut
        # No socket connected yet (or loop not ready) — park the message for
        # the next subscriber instead of silently dropping it.
        with self._lock:
            self._backlog.append(msg)
        print(f"[bus] queued (no subscribers yet): {msg.get('type')}")
        return None

    @property
    def subscribers(self) -> int:
        with self._lock:
            return len(self._subs)


bus = AlertBus()
