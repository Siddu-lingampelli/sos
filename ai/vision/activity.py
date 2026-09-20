"""Live activity narration (feeds the dashboard logs).

Turns per-track state into human-readable transition events:
  TRACK: Person #3 entered view
  MOVE:  Person #3 walking | running
  FALL:  Person #3 NORMAL -> POSSIBLE_FALL
  STILL: Person #3 OBSERVING | INACTIVE

Only transitions emit — a steady scene stays quiet. Shared by run_pipeline
(terminal) and the backend stream (WebSocket -> dashboard logs).
"""
from config import FallConfig, DEFAULT


def speed_class(hist, window_sec: float = 1.0) -> str:
    """walking / running / still from trailing centroid velocity (norm units/s)."""
    pts = [(e.get("t", 0), e.get("cx"), e.get("cy")) for e in hist
           if e.get("cx") is not None and e.get("cy") is not None]
    pts = [p for p in pts if pts and p[0] >= pts[-1][0] - window_sec]
    if len(pts) < 2:
        return "still"
    import math
    dt = max(1e-3, pts[-1][0] - pts[0][0])
    v = math.hypot(pts[-1][1] - pts[0][1], pts[-1][2] - pts[0][2]) / dt
    if v < 0.02:
        return "still"
    if v < 0.15:
        return "walking"
    return "running"


class ActivityLog:
    def __init__(self, cfg: FallConfig = DEFAULT):
        self.cfg = cfg
        self._last: dict[int, dict] = {}

    def update(self, tid: int, snap: dict, hist: list) -> list[dict]:
        """snap: {fall_state, inact_state}. Returns new activity events."""
        out: list[dict] = []
        prev = self._last.get(tid)
        move = speed_class(hist)
        cur = {"fall": snap.get("fall_state", "NORMAL"),
               "inact": snap.get("inact_state", "IDLE"),
               "move": move}
        if prev is None:
            out.append({"tag": "TRACK", "text": f"Person #{tid} entered view"})
        else:
            if cur["fall"] != prev["fall"]:
                out.append({"tag": "FALL",
                            "text": f"Person #{tid}: {prev['fall']} -> {cur['fall']}"})
            if cur["inact"] != prev["inact"]:
                out.append({"tag": "STILL",
                            "text": f"Person #{tid}: {prev['inact']} -> {cur['inact']}"})
            if cur["move"] != prev["move"] and cur["move"] in ("walking", "running"):
                out.append({"tag": "MOVE", "text": f"Person #{tid} {cur['move']}"})
        self._last[tid] = cur
        return out

    def prune(self, active_tids) -> None:
        active = set(active_tids)
        for tid in [t for t in self._last if t not in active]:
            self._last.pop(tid, None)
