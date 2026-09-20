"""Level 5 inactivity monitor tests (no DB, no camera)."""
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai", "vision")))

from inactivity import InactivityMonitor, movement_score
from config import FallConfig


def _hist(still=True, n=5):
    dx = 0.0 if still else 0.05
    return [{"track_id": 1, "cx": 0.5 + i * dx, "cy": 0.5,
             "keypoints": [[100 + i * (0 if still else 5), 100, 0.9]], "t": time.time() + i * 0.1}
            for i in range(n)]


def test_movement_score_still_vs_moving():
    assert movement_score(_hist(still=True)) < movement_score(_hist(still=False))


def test_observation_to_emergency():
    cfg = FallConfig(OBSERVATION_DURATION_SEC=0.2, INACTIVITY_THRESHOLD=5.0,
                     RECOVERY_FACTOR=3.0, MOVEMENT_WINDOW_SEC=3.0)
    m = InactivityMonitor(cfg)
    h = _hist(still=True)
    assert m.update(1, h, "FALL_CONFIRMED") == "OBSERVING"
    time.sleep(0.25)
    h.append(_hist(still=True, n=1)[0])
    assert m.update(1, h, "FALL_CONFIRMED") == "INACTIVE"
    types = [e["type"] for e in m.events]
    assert "POSSIBLE_EMERGENCY" in types


def test_recovery_cancels_observation():
    cfg = FallConfig(OBSERVATION_DURATION_SEC=30.0, INACTIVITY_THRESHOLD=0.02,
                     RECOVERY_FACTOR=3.0, MOVEMENT_WINDOW_SEC=3.0)
    m = InactivityMonitor(cfg)
    m.update(1, _hist(still=True), "FALL_CONFIRMED")
    assert m.update(1, _hist(still=False, n=8), "FALL_CONFIRMED") == "IDLE"
    assert any(e["type"] == "RECOVERY_DETECTED" for e in m.events)
