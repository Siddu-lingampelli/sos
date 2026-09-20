"""Process-wide alert bus: DB-backed incident firings fan out to dashboards.

Lives outside the API routers so both the HTTP layer (PATCH status changes)
and the background inference thread (stream.py) can publish without import
cycles. Thread-safe: socket bookkeeping happens on the event loop while
publishers from other threads schedule via run_coroutine_threadsafe.
"""
import asyncio


class AlertBus:
    def __init__(self):
        self._subs: set = set()
        self._loop: asyncio.AbstractEventLoop | None = None

    async def connect(self, ws) -> None:
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            pass
        self._subs.add(ws)

    async def disconnect(self, ws) -> None:
        self._subs.discard(ws)

    async def broadcast(self, msg: dict) -> int:
        dead = []
        for ws in list(self._subs):
            try:
                await ws.send_json(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._subs.discard(ws)
        return len(self._subs)

    def broadcast_sync(self, msg: dict) -> None:
        """Fire-and-forget publish safe to call from non-loop threads."""
        loop = self._loop
        if loop is not None and loop.is_running():
            asyncio.run_coroutine_threadsafe(self.broadcast(msg), loop)

    @property
    def subscribers(self) -> int:
        return len(self._subs)


bus = AlertBus()
