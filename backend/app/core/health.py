"""Process-wide component health registry (Level 9 failure handling).

Both the vision inference threads and the audio service publish their state
here. The HTTP health endpoints and the operator dashboard read it back, so a
camera/audio/DB failure becomes a visible system state instead of a silent
thread death.
"""
import threading
import time


class HealthRegistry:
    def __init__(self):
        self._lock = threading.Lock()
        self._components: dict[str, dict] = {}

    def set(self, name: str, status: str, detail: str = "") -> None:
        """status: 'ok' | 'degraded' | 'down'."""
        with self._lock:
            self._components[name] = {
                "status": status,
                "detail": detail,
                "updated_at": time.time(),
            }

    def clear(self, name: str) -> None:
        with self._lock:
            self._components.pop(name, None)

    def snapshot(self) -> dict[str, dict]:
        with self._lock:
            return {k: dict(v) for k, v in self._components.items()}

    def overall(self) -> str:
        states = [c["status"] for c in self.snapshot().values()]
        if "down" in states:
            return "down"
        if "degraded" in states:
            return "degraded"
        return "ok"


health = HealthRegistry()