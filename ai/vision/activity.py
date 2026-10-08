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
    # Filter to trailing window
    if pts:
        t_last = pts[-1][0]
        pts = [p for p in pts if p[0] >= t_last - window_sec]
    if len(pts) < 2:
        return "still"
    import math
    dt = max(1e-3, pts[-1][0] - pts[0][0])
    v = math.hypot(pts[-1][1] - pts[0][1], pts[-1][2] - pts[0][2]) / dt

    # Hysteresis thresholds with proper separation
    # Still: < 0.03, Walking: 0.03-0.20, Running: >= 0.20
    # Higher thresholds reduce false movement on standing jitter
    if v < 0.03:
        return "still"
    if v < 0.20:
        return "walking"
    return "running"


class ActivityLog:
    def __init__(self, cfg: FallConfig = DEFAULT):
        self.cfg = cfg
        self._last: dict[int, dict] = {}

    def _fall_event(self, tid: int, previous: str | None, current: str, snap: dict) -> dict:
        evidence = snap.get("fall_evidence") or {}
        score = evidence.get("score")
        angle = evidence.get("angle")
        aspect = evidence.get("aspect")
        velocity = evidence.get("hip_velocity")
        score_text = f" score={score:.0f}%" if isinstance(score, (int, float)) else ""
        # Add angle info for better debugging
        angle_text = f" angle={angle:.0f}°" if angle is not None else ""
        text = (
            f"Person #{tid}: {previous} -> {current}{score_text}{angle_text}"
            if previous is not None
            else f"Person #{tid} entered view as {current}{score_text}{angle_text}"
        )
        event = {"tag": "FALL", "text": text}
        if previous is not None:
            event.update({"track_id": tid, "from": previous, "to": current})
        if isinstance(score, (int, float)):
            event["score"] = score
        if angle is not None:
            event["angle"] = angle
        if aspect is not None:
            event["aspect"] = aspect
        if velocity is not None:
            event["hip_velocity"] = velocity
        return event

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
            # Add standing still event for initial entry
            out.append({"tag": "MOVE", "text": f"Person #{tid} standing still"})
            if cur["fall"] in ("POSSIBLE_FALL", "FALL_CONFIRMED"):
                out.append(self._fall_event(tid, None, cur["fall"], snap))
        else:
            if cur["fall"] != prev["fall"]:
                out.append(self._fall_event(tid, prev["fall"], cur["fall"], snap))
            if cur["inact"] != prev["inact"]:
                out.append({"tag": "STILL",
                            "text": f"Person #{tid}: {prev['inact']} -> {cur['inact']}"})
            # Movement transitions - now includes standing still with better naming
            if cur["move"] != prev["move"]:
                if cur["move"] == "still":
                    out.append({"tag": "MOVE", "text": f"Person #{tid} standing still"})
                elif cur["move"] == "walking":
                    out.append({"tag": "MOVE", "text": f"Person #{tid} walking"})
                elif cur["move"] == "running":
                    out.append({"tag": "MOVE", "text": f"Person #{tid} running"})
        self._last[tid] = cur
        return out

    def prune(self, active_tids) -> None:
        active = set(active_tids)
        for tid in [t for t in self._last if t not in active]:
            self._last.pop(tid, None)
