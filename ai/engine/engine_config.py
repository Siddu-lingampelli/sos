"""Level 7 tunable weights + thresholds. Tune with test scenarios (Level 10)."""
from dataclasses import dataclass


@dataclass
class EngineConfig:
    # Evidence weights (sum, capped at SCORE_MAX)
    W_FALL_POSSIBLE: float = 30.0
    W_FALL_CONFIRMED: float = 40.0
    W_ABNORMAL_POSTURE: float = 15.0
    W_POST_FALL_INACTIVITY: float = 25.0
    W_DISTRESS_KEYWORD: float = 20.0
    W_DISTRESS_SOUND: float = 20.0
    # Audio evidence counts only while fresh
    AUDIO_WINDOW_SEC: float = 30.0
    SCORE_MAX: float = 100.0
    # Decision thresholds (mirror .env MONITOR_THRESHOLD / ALERT_THRESHOLD)
    MONITOR_THRESHOLD: float = 40.0
    ALERT_THRESHOLD: float = 70.0


DEFAULT_ENGINE = EngineConfig()
