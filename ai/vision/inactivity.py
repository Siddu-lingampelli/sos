"""Post-fall inactivity & temporal verification (Level 5).

Sits on top of FallDetector (Level 4):
  FALL_CONFIRMED/POSSIBLE_FALL -> start observation window
  window + motionless          -> INACTIVE -> POSSIBLE_EMERGENCY event
  window + movement/get-up     -> RECOVERED (cancel), OBSERVATION_TIMEOUT logged

Per-track states: IDLE -> OBSERVING -> INACTIVE | RECOVERED -> IDLE
Emits structured events for Level 7 engine + backend storage:
  OBSERVATION_STARTED / INACTIVITY_CONFIRMED / POSSIBLE_EMERGENCY /
  RECOVERY_DETECTED / OBSERVATION_TIMEOUT
"""
import time
from collections import defaultdict, deque
import numpy as np
from config import FallConfig, DEFAULT

FALL_STATES = ("POSSIBLE_FALL", "FALL_CONFIRMED")


def movement_score(hist, window_sec=3.0):
    """Normalized movement per second over the trailing window.

    Combines bbox-centroid drift + mean keypoint displacement.
    Returns ~0 for a motionless person, larger when moving.
    """
    if len(hist) < 2:
        return 0.0
    t_end = hist[-1].get("t", 0)
    win = [e for e in hist if t_end - e.get("t", 0) <= window_sec]
    if len(win) < 2:
        win = hist[-2:]
    dt = max(1e-3, win[-1].get("t", 0) - win[0].get("t", 0))

    # Centroid drift
    c0 = np.array([win[0].get("cx", 0), win[0].get("cy", 0)])
    c1 = np.array([win[-1].get("cx", 0), win[-1].get("cy", 0)])
    centroid = float(np.linalg.norm(c1 - c0)) / dt

    # Mean keypoint displacement (first vs last frame in window)
    kp0 = win[0].get("keypoints", [])
    kp1 = win[-1].get("keypoints", [])
    disp = []
    for a, b in zip(kp0, kp1):
        ca = a[2] if len(a) > 2 else 1.0
        cb = b[2] if len(b) > 2 else 1.0
        if ca >= 0.4 and cb >= 0.4:
            disp.append(abs(a[0] - b[0]) + abs(a[1] - b[1]))
    keypoints = (sum(disp) / len(disp) / dt) if disp else 0.0

    return round(0.5 * centroid + 0.5 * keypoints, 4)


class InactivityMonitor:
    def __init__(self, cfg: FallConfig = DEFAULT):
        self.cfg = cfg
        self.state: dict[int, str] = defaultdict(lambda: "IDLE")
        self.obs_start: dict[int, float] = {}
        self.events: deque[dict] = deque(maxlen=500)

    def update(self, tid: int, hist: list, fall_state: str) -> str:
        now = time.time()
        st = self.state[tid]

        if st == "IDLE":
            if fall_state in FALL_STATES:
                self.state[tid] = "OBSERVING"
                self.obs_start[tid] = now
                self.events.append({"type": "OBSERVATION_STARTED", "track_id": tid,
                                    "t": now, "trigger": fall_state})
            return self.state[tid]

        if st == "OBSERVING":
            # Fall detector says person recovered on their own -> cancel
            if fall_state in ("NORMAL", "RECOVERED"):
                self._finish(tid, "IDLE", "RECOVERY_DETECTED", now)
                return self.state[tid]
            move = movement_score(hist, self.cfg.MOVEMENT_WINDOW_SEC)
            elapsed = now - self.obs_start.get(tid, now)
            if move >= self.cfg.INACTIVITY_THRESHOLD * self.cfg.RECOVERY_FACTOR:
                self._finish(tid, "IDLE", "RECOVERY_DETECTED", now, extra={"move": move})
            elif elapsed >= self.cfg.OBSERVATION_DURATION_SEC:
                if move < self.cfg.INACTIVITY_THRESHOLD:
                    self.state[tid] = "INACTIVE"
                    self.events.append({"type": "INACTIVITY_CONFIRMED", "track_id": tid,
                                        "t": now, "move": move, "elapsed": round(elapsed, 1)})
                    self.events.append({"type": "POSSIBLE_EMERGENCY", "track_id": tid,
                                        "t": now, "reason": "fall+prolonged-inactivity"})
                else:
                    self._finish(tid, "IDLE", "OBSERVATION_TIMEOUT", now,
                                 extra={"move": move, "elapsed": round(elapsed, 1)})
            return self.state[tid]

        if st == "INACTIVE":
            move = movement_score(hist, self.cfg.MOVEMENT_WINDOW_SEC)
            if move >= self.cfg.INACTIVITY_THRESHOLD * self.cfg.RECOVERY_FACTOR \
                    or fall_state in ("NORMAL", "RECOVERED"):
                self._finish(tid, "IDLE", "RECOVERY_DETECTED", now, extra={"move": move})
            return self.state[tid]

        return st  # RECOVERED transient not used here; IDLE covers it

    def _finish(self, tid, new_state, ev_type, now, extra=None):
        self.state[tid] = new_state
        self.obs_start.pop(tid, None)
        ev = {"type": ev_type, "track_id": tid, "t": now}
        if extra:
            ev.update(extra)
        self.events.append(ev)

    def info(self, tid: int, hist: list) -> dict:
        """Snapshot for the visualizer: state + elapsed + current movement."""
        st = self.state.get(tid, "IDLE")
        elapsed = 0.0
        if st == "OBSERVING":
            elapsed = time.time() - self.obs_start.get(tid, time.time())
        return {"inact_state": st,
                "inact_elapsed": round(elapsed, 1),
                "inact_move": movement_score(hist, self.cfg.MOVEMENT_WINDOW_SEC)}

    def prune(self, active_tids) -> None:
        active = set(active_tids)
        for tid in [t for t in self.state if t not in active]:
            self.state.pop(tid, None)
            self.obs_start.pop(tid, None)
