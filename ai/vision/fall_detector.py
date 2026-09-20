"""Temporal fall-detection state machine (Level 4).

States: NORMAL -> POSSIBLE_FALL -> FALL_CONFIRMED -> RECOVERED -> NORMAL
Uses torso angle, bbox aspect, and hip vertical velocity over history window.
"""
from collections import defaultdict
from config import FallConfig, DEFAULT


class FallDetector:
    def __init__(self, cfg: FallConfig = DEFAULT):
        self.cfg = cfg
        self.state: dict[int, str] = defaultdict(lambda: "NORMAL")
        self.counters: dict[int, int] = defaultdict(int)
        self.events: list[dict] = []  # structured fall events for Level 5/engine

    def _hip_velocity(self, hist):
        """Normalized hip-y drop per second over recent history."""
        pts = [(e["t"], e["hip_y"]) for e in hist if e.get("hip_y") is not None]
        if len(pts) < 3:
            return 0.0
        (t0, y0), (t1, y1) = pts[0], pts[-1]
        dt = max(1e-3, t1 - t0)
        return (y1 - y0) / dt  # +ve = moving down in image coords

    def update(self, person: dict, hist: list[dict]):
        tid = person.get("track_id", -1)
        ang = person.get("angle")
        aspect = person.get("aspect", 0)
        vel = self._hip_velocity(hist[-8:] if len(hist) >= 8 else hist)
        horizontal = (
            (ang is not None and ang >= self.cfg.FALL_ANGLE_THRESHOLD)
            or aspect >= self.cfg.FALL_ASPECT_THRESHOLD
        )
        rapid_drop = vel >= self.cfg.FALL_VERTICAL_VELOCITY
        st = self.state[tid]

        if st == "NORMAL":
            if horizontal and rapid_drop:
                self._set(tid, "POSSIBLE_FALL", person, reason="rapid-drop+horizontal")
            elif horizontal:
                # need persistence: count horizontal frames
                self.counters[tid] += 1
                if self.counters[tid] >= self.cfg.CONFIRM_FRAMES:
                    self._set(tid, "POSSIBLE_FALL", person, reason="persistent-horizontal")
            else:
                self.counters[tid] = 0
        elif st == "POSSIBLE_FALL":
            if horizontal:
                self.counters[tid] += 1
                if self.counters[tid] >= self.cfg.CONFIRM_FRAMES:
                    self._set(tid, "FALL_CONFIRMED", person, reason="confirmed-temporal")
            else:
                # brief horizontal then upright => false alarm / bending
                self.counters[tid] = 0
                self._set(tid, "RECOVERED", person, reason="stood-back-up")
        elif st == "FALL_CONFIRMED":
            if not horizontal:
                self.counters[tid] += 1
                if self.counters[tid] >= self.cfg.RECOVERY_FRAMES:
                    self._set(tid, "RECOVERED", person, reason="recovered-after-fall")
            else:
                self.counters[tid] = 0
        elif st == "RECOVERED":
            self.counters[tid] += 1
            if self.counters[tid] >= self.cfg.RECOVERY_FRAMES:
                self._set(tid, "NORMAL", person, reason="cooldown-done")
            elif horizontal and rapid_drop:
                self._set(tid, "POSSIBLE_FALL", person, reason="second-fall")

        person["fall_state"] = self.state[tid]
        person["hip_velocity"] = round(vel, 3)
        return self.state[tid]

    def _set(self, tid, new_state, person, reason):
        old = self.state[tid]
        self.state[tid] = new_state
        self.counters[tid] = 0
        if new_state in ("POSSIBLE_FALL", "FALL_CONFIRMED", "RECOVERED"):
            self.events.append({
                "track_id": tid, "from": old, "to": new_state,
                "reason": reason, "t": person.get("t"),
                "angle": person.get("angle"), "aspect": person.get("aspect"),
            })

    def reset_track(self, tid: int):
        self.state.pop(tid, None)
        self.counters.pop(tid, None)
