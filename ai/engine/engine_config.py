"""Level 7 tunable weights + thresholds. Tune with test scenarios (Level 10).

Environment overrides (so .env tuning actually applies to standalone runs):
  SOS_MONITOR_THRESHOLD, SOS_ALERT_THRESHOLD, SOS_AUDIO_WINDOW_SEC
"""
import os
from dataclasses import dataclass


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@dataclass
class EngineConfig:
    # Evidence weights (sum, capped at SCORE_MAX)
    W_FALL_POSSIBLE: float = 30.0
    W_FALL_CONFIRMED: float = 40.0
    W_ABNORMAL_POSTURE: float = 15.0
    W_POST_FALL_INACTIVITY: float = 25.0
    W_DISTRESS_KEYWORD: float = 20.0
    W_DISTRESS_SOUND: float = 20.0
    # Audio evidence counts only while fresh. Short on purpose: a stale shout
    # must not stack onto fresh vision evidence and push a weak signal over
    # the alert threshold.
    AUDIO_WINDOW_SEC: float = 10.0
    SCORE_MAX: float = 100.0
    # Decision thresholds (mirror .env MONITOR_THRESHOLD / ALERT_THRESHOLD)
    MONITOR_THRESHOLD: float = 40.0
    ALERT_THRESHOLD: float = 70.0
    # Score must dip this far below the fire-time peak before a second
    # incident may fire without a full recovery to NORMAL (anti-spam).
    REARM_DROP: float = 15.0


DEFAULT_ENGINE = EngineConfig(
    MONITOR_THRESHOLD=_env_float("SOS_MONITOR_THRESHOLD", 40.0),
    ALERT_THRESHOLD=_env_float("SOS_ALERT_THRESHOLD", 70.0),
    AUDIO_WINDOW_SEC=_env_float("SOS_AUDIO_WINDOW_SEC", 10.0),
)
