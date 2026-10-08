"""Temporal fall-detection state machine (Level 4).

States: NORMAL -> POSSIBLE_FALL -> FALL_CONFIRMED -> RECOVERED -> NORMAL
Uses torso angle, bbox aspect, and hip vertical velocity over history window.
"""
from collections import defaultdict, deque
from config import FallConfig, DEFAULT
from pose_geometry import head_ankle_span

# --- config hook ---
# Re-exported for callers that still import it from here; the real default
# lives in FallConfig so it can be tuned without touching logic.
UPRIGHT_EXIT_FRAMES = DEFAULT.UPRIGHT_EXIT_FRAMES


class FallDetector:
    def __init__(self, cfg: FallConfig = DEFAULT):
        self.cfg = cfg
        self.state: dict[int, str] = defaultdict(lambda: "NORMAL")
        self.counters: dict[int, int] = defaultdict(int)
        self.upright_streak: dict[int, int] = defaultdict(int)
        self.events: deque[dict] = deque(maxlen=500)  # bounded: no leak on 24/7 runs

    def _hip_velocity(self, hist):
        """Steepest meaningful hip-y descent per second in the recent window.

        A fall takes ~0.4 s, but a fixed 8-frame window at DETECT_STRIDE 3 and
        ~15 fps spans ~1.6 s, so averaging that whole window divides a real fall
        by roughly four and drops it under FALL_VERTICAL_VELOCITY. Averaging a
        short window instead would dilute it with the stationary period that
        follows the impact.

        So: take the steepest descent inside a short trailing window, and ignore
        any pair whose total drop is smaller than MIN_DROP_FRAC of the frame.
        The displacement floor is what keeps pose jitter and a slow sit-down
        from registering as a rapid drop — a genuine fall moves the hip a large
        fraction of the frame height, noise does not.

        Sign is preserved: standing up is negative (hip y decreases upward).
        """
        pts = [(e["t"], e["hip_y"]) for e in hist[-self.cfg.VELOCITY_WINDOW_FRAMES:]
               if e.get("hip_y") is not None]
        if len(pts) < 2:
            return 0.0

        best = 0.0
        for i in range(len(pts) - 1):
            t0, y0 = pts[i]
            for j in range(i + 1, len(pts)):
                t1, y1 = pts[j]
                dt = t1 - t0
                if dt < 1e-3:
                    continue
                drop = y1 - y0  # +ve = moving down in image coords
                if drop < self.cfg.MIN_DROP_FRAC:
                    continue  # too small to be a fall, whatever the rate says
                best = max(best, drop / dt)

        if best > 0:
            return best
        # No qualifying descent: report the net movement so a person getting up
        # reads as negative rather than 0.
        (t0, y0), (t1, y1) = pts[0], pts[-1]
        dt = max(1e-3, t1 - t0)
        return (y1 - y0) / dt

    def _fall_evidence(self, angle, aspect, span, velocity, state: str):
        """Return a 0-100 fall-likelihood score and the evidence behind it."""
        angle_component = 0.0
        if angle is not None:
            angle_component = max(0.0, min(1.0, (angle - 20.0) / 70.0))
        aspect_component = max(0.0, min(1.0, (aspect - 0.5) / 1.0))
        velocity_component = 0.0
        if self.cfg.FALL_VERTICAL_VELOCITY > 0:
            velocity_component = max(0.0, min(1.0, velocity / self.cfg.FALL_VERTICAL_VELOCITY))

        if span is None:
            # Head/ankles not confident enough to trust (common for a crumpled
            # body). Redistribute the span weight across the signals we do
            # have rather than scoring a known fall as weaker.
            score = round(100.0 * (0.5 * angle_component + 0.3 * aspect_component
                                   + 0.2 * velocity_component), 1)
        else:
            # Low span -> lying down. Map span 0 -> 1, span >= 0.5 -> 0.
            span_component = max(0.0, min(1.0, 1.0 - (span / 0.5)))
            score = round(100.0 * (0.4 * angle_component + 0.25 * aspect_component
                                   + 0.25 * span_component + 0.1 * velocity_component), 1)

        # Horizontal posture is true when angle is high *or* aspect is wide *or*
        # the head-to-ankle span collapses. The span check is the kneeling fix:
        # a kneeling person still spans most of their height, so this never
        # fires for a crouch.
        horizontal = (
            (angle is not None and angle >= self.cfg.FALL_ANGLE_THRESHOLD)
            or aspect >= self.cfg.FALL_ASPECT_THRESHOLD
            or (span is not None and span < self.cfg.HORIZONTAL_SPAN_RATIO)
        )

        return {
            "angle": angle,
            "aspect": round(aspect, 3),
            "span": round(span, 3) if span is not None else None,
            "hip_velocity": round(velocity, 3),
            "horizontal": horizontal,
            "rapid_drop": velocity >= self.cfg.FALL_VERTICAL_VELOCITY,
            "score": score,
            "state": state,
        }

    def update(self, person: dict, hist: list[dict]):
        tid = person.get("track_id", -1)
        ang = person.get("angle")
        try:
            aspect = float(person.get("aspect") or 0)
        except (TypeError, ValueError):
            aspect = 0.0
        vel = self._hip_velocity(hist[-8:] if len(hist) >= 8 else hist)
        st = self.state[tid]
        span = head_ankle_span(person.get("keypoints") or [], self.cfg.KP_CONF)
        if span is not None and person.get("box"):
            # Normalize by bounding-box height so the value is resolution- and
            # distance-independent: ~1.0 standing, well under 0.45 lying down.
            _x1, _y1, _x2, y2 = person["box"]
            box_h = max(1.0, y2 - _y1)
            span = span / box_h
        evidence = self._fall_evidence(ang, aspect, span, vel, st)
        horizontal = evidence["horizontal"]
        rapid_drop = evidence["rapid_drop"]

        if st == "NORMAL":
            if horizontal and rapid_drop:
                self._set(tid, "POSSIBLE_FALL", person, evidence, reason="rapid-drop+horizontal")
            elif horizontal:
                # need persistence: count horizontal frames
                self.counters[tid] += 1
                if self.counters[tid] >= self.cfg.CONFIRM_FRAMES:
                    self._set(tid, "POSSIBLE_FALL", person, evidence, reason="persistent-horizontal")
            else:
                self.counters[tid] = 0
        elif st == "POSSIBLE_FALL":
            if horizontal:
                self.counters[tid] += 1
                self.upright_streak[tid] = 0
                if self.counters[tid] >= self.cfg.CONFIRM_FRAMES:
                    self._set(tid, "FALL_CONFIRMED", person, evidence, reason="confirmed-temporal")
            else:
                # Require consecutive upright frames — a single flicker
                # frame (brief bend / missed keypoints) must not flip state
                self.upright_streak[tid] += 1
                if self.upright_streak[tid] >= self.cfg.UPRIGHT_EXIT_FRAMES:
                    self.counters[tid] = 0
                    self.upright_streak[tid] = 0
                    self._set(tid, "NORMAL", person, evidence, reason="stood-back-up")
        elif st == "FALL_CONFIRMED":
            if not horizontal:
                self.counters[tid] += 1
                if self.counters[tid] >= self.cfg.RECOVERY_FRAMES:
                    self._set(tid, "RECOVERED", person, evidence, reason="recovered-after-fall")
            else:
                self.counters[tid] = 0
        elif st == "RECOVERED":
            self.counters[tid] += 1
            if self.counters[tid] >= self.cfg.RECOVERY_FRAMES:
                self._set(tid, "NORMAL", person, evidence, reason="cooldown-done")
            elif horizontal and rapid_drop:
                self._set(tid, "POSSIBLE_FALL", person, evidence, reason="second-fall")

        person["fall_state"] = self.state[tid]
        person["fall_score"] = evidence["score"]
        person["hip_velocity"] = round(vel, 3)
        person["fall_evidence"] = evidence
        # Carry span forward so the visualizer can show why the detector
        # decided "horizontal". It's handy when debugging kneeling false
        # positives or curled-fall false negatives.
        person["head_ankle_span_norm"] = round(span, 3) if span is not None else None
        return self.state[tid]

    def _set(self, tid, new_state, person, evidence, reason):
        old = self.state[tid]
        self.state[tid] = new_state
        evidence["state"] = new_state
        self.counters[tid] = 0
        if new_state in ("POSSIBLE_FALL", "FALL_CONFIRMED", "RECOVERED"):
            self.events.append({
                "track_id": tid, "from": old, "to": new_state,
                "reason": reason, "t": person.get("t"),
                "angle": person.get("angle"), "aspect": person.get("aspect"),
                "hip_velocity": person.get("hip_velocity"),
                "fall_score": evidence["score"],
            })

    def reset_track(self, tid: int):
        self.state.pop(tid, None)
        self.counters.pop(tid, None)
        self.upright_streak.pop(tid, None)

    def prune(self, active_tids) -> None:
        """Drop state for tracks the tracker no longer holds (prevents leak)."""
        active = set(active_tids)
        for tid in [t for t in self.state if t not in active]:
            self.reset_track(tid)
