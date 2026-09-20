"""Emergency Confidence Engine (Level 7) — the central decision layer.

Fuses per-track vision state (Level 4 fall + Level 5 inactivity) with
fresh audio distress events (Level 6) into a 0–100 score:

  FALL_CONFIRMED       +40 (strong visual evidence)
  POSSIBLE_FALL        +30
  ABNORMAL_POSTURE     +15 (torso horizontal / wide bbox)
  POST_FALL_INACTIVITY +25 (observation window judged motionless)
  DISTRESS_KEYWORD     +20 (heard within AUDIO_WINDOW_SEC)
  DISTRESS_SOUND       +20 (scream within AUDIO_WINDOW_SEC)
  RECOVERY             clears vision evidence -> score collapses

States per track: NORMAL (<MONITOR) / MONITORING (>=MONITOR) /
POSSIBLE_EMERGENCY (>=ALERT, edge-triggered incident, re-arms below MONITOR).
"""
import time
from collections import defaultdict, deque
from engine_config import EngineConfig, DEFAULT_ENGINE


class EmergencyEngine:
    def __init__(self, cfg: EngineConfig = DEFAULT_ENGINE):
        self.cfg = cfg
        self.score: dict[int, float] = defaultdict(float)
        self.state: dict[int, str] = defaultdict(lambda: "NORMAL")
        self._fired: dict[int, bool] = defaultdict(bool)
        self._audio: deque[dict] = deque(maxlen=200)  # {t, kind, detail}
        self._pending: deque[dict] = deque(maxlen=100)  # fired incident payloads

    # ---- inputs ----

    def audio_event(self, kind: str, detail: str = "") -> None:
        """kind: 'DISTRESS_KEYWORD' | 'DISTRESS_SOUND'. Call from audio loop."""
        self._audio.append({"t": time.time(), "kind": kind, "detail": detail})

    def _fresh_audio(self, kind: str) -> list[dict]:
        now = time.time()
        return [a for a in self._audio if a["kind"] == kind and now - a["t"] <= self.cfg.AUDIO_WINDOW_SEC]

    # ---- per-track update ----

    def update(self, tid: int, vision: dict) -> tuple[float, str, list]:
        """vision: {fall_state, inact_state, angle, aspect}. Returns (score, state, evidence)."""
        cfg = self.cfg
        ev: list[tuple[str, float]] = []
        fall = vision.get("fall_state", "NORMAL")
        inact = vision.get("inact_state", "IDLE")
        ang = vision.get("angle")
        aspect = vision.get("aspect", 0) or 0

        if fall == "FALL_CONFIRMED":
            ev.append(("FALL_DETECTED", cfg.W_FALL_CONFIRMED))
        elif fall == "POSSIBLE_FALL":
            ev.append(("FALL_DETECTED", cfg.W_FALL_POSSIBLE))
        if (ang is not None and ang >= 55.0) or aspect >= 1.1:
            ev.append(("ABNORMAL_POSTURE", cfg.W_ABNORMAL_POSTURE))
        if inact == "INACTIVE":
            ev.append(("POST_FALL_INACTIVITY", cfg.W_POST_FALL_INACTIVITY))
        for a in self._fresh_audio("DISTRESS_KEYWORD"):
            ev.append(("DISTRESS_KEYWORD", cfg.W_DISTRESS_KEYWORD))
            break  # count once no matter how many utterances in window
        for a in self._fresh_audio("DISTRESS_SOUND"):
            ev.append(("DISTRESS_SOUND", cfg.W_DISTRESS_SOUND))
            break

        score = round(min(cfg.SCORE_MAX, sum(w for _, w in ev)), 1)
        if score >= cfg.ALERT_THRESHOLD:
            state = "POSSIBLE_EMERGENCY"
        elif score >= cfg.MONITOR_THRESHOLD:
            state = "MONITORING"
        else:
            state = "NORMAL"

        self.score[tid] = score
        self.state[tid] = state

        if state == "POSSIBLE_EMERGENCY" and not self._fired[tid]:
            self._fired[tid] = True
            self._pending.append({
                "track_id": tid,
                "event_type": self._label(ev),
                "confidence": score / 100.0,
                "evidence": [{"signal": s, "points": w} for s, w in ev],
                "timestamp": time.time(),
            })
        elif state == "NORMAL":
            self._fired[tid] = False  # re-arm after full recovery

        return score, state, ev

    @staticmethod
    def _label(ev: list) -> str:
        kinds = [s for s, _ in ev]
        parts = []
        if "FALL_DETECTED" in kinds:
            parts.append("Fall")
        if "POST_FALL_INACTIVITY" in kinds:
            parts.append("Prolonged Inactivity")
        if "DISTRESS_KEYWORD" in kinds or "DISTRESS_SOUND" in kinds:
            parts.append("Distress Audio")
        return " + ".join(parts) if parts else "Monitoring"

    # ---- outputs ----

    def pop_incident(self) -> dict | None:
        """Newest unfetched POSSIBLE_EMERGENCY payload, or None."""
        return self._pending.popleft() if self._pending else None

    def prune(self, active_tids) -> None:
        active = set(active_tids)
        for tid in [t for t in self.state if t not in active]:
            self.state.pop(tid, None)
            self.score.pop(tid, None)
            self._fired.pop(tid, None)
