"""Level 7 fusion tests: weights, thresholds, edge-trigger, expiry, recovery."""
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai", "engine")))

from fusion import EmergencyEngine
from engine_config import EngineConfig

V_UPRIGHT = {"fall_state": "NORMAL", "inact_state": "IDLE", "angle": 5.0, "aspect": 0.5}
V_FALL = {"fall_state": "FALL_CONFIRMED", "inact_state": "IDLE", "angle": 80.0, "aspect": 1.5}
V_FALL_STILL = {"fall_state": "FALL_CONFIRMED", "inact_state": "INACTIVE", "angle": 80.0, "aspect": 1.5}


def test_fall_alone_is_monitoring_not_emergency():
    e = EmergencyEngine()
    score, state, ev = e.update(1, V_FALL)
    assert state == "MONITORING", (score, state)  # 40 + 15 = 55
    assert e.pop_incident() is None


def test_fall_plus_inactivity_fires_once():
    e = EmergencyEngine()
    e.update(1, V_FALL_STILL)
    score, state, ev = e.update(1, V_FALL_STILL)
    assert state == "POSSIBLE_EMERGENCY", (score, state)  # 40+15+25 = 80
    inc = e.pop_incident()
    assert inc and inc["confidence"] == score / 100.0
    assert "Fall" in inc["event_type"] and "Inactivity" in inc["event_type"]
    e.update(1, V_FALL_STILL)
    assert e.pop_incident() is None  # edge-triggered: no duplicates


def test_keyword_boost_crosses_threshold():
    e = EmergencyEngine()
    e.update(2, V_FALL)
    e.audio_event("DISTRESS_KEYWORD", "help")
    score, state, ev = e.update(2, V_FALL)  # 55 + 20 = 75
    assert state == "POSSIBLE_EMERGENCY", (score, state)


def test_stale_audio_ignored_and_audio_alone_safe():
    e = EmergencyEngine()
    e._audio.append({"t": time.time() - 3600, "kind": "DISTRESS_KEYWORD", "detail": "help"})
    score, state, _ = e.update(3, V_UPRIGHT)
    assert (score, state) == (0.0, "NORMAL")
    e.audio_event("DISTRESS_SOUND", "scream")
    score, state, _ = e.update(4, V_UPRIGHT)  # 20 alone < MONITOR
    assert state == "NORMAL" and e.pop_incident() is None


def test_recovery_clears_and_rearms():
    e = EmergencyEngine()
    e.update(5, V_FALL_STILL)
    assert e.pop_incident() is not None
    score, state, _ = e.update(5, V_UPRIGHT)
    assert (score, state) == (0.0, "NORMAL")
    e.update(5, V_FALL_STILL)  # second emergency must fire again
    assert e.pop_incident() is not None


def test_score_capped():
    e = EmergencyEngine(EngineConfig(W_FALL_CONFIRMED=90.0, W_ABNORMAL_POSTURE=90.0))
    score, _, _ = e.update(6, V_FALL)
    assert score == 100.0


def test_hovering_at_threshold_does_not_spam_incidents():
    """A score parked at/above ALERT fires once, not once per frame."""
    e = EmergencyEngine()
    e.update(7, V_FALL_STILL)
    assert e.pop_incident() is not None
    for _ in range(5):
        e.update(7, V_FALL_STILL)
        assert e.pop_incident() is None


def test_second_fall_after_partial_recovery_fires_again():
    """Fall (80) → partial recovery to MONITORING (55) → fall again (80):
    the dip exceeds REARM_DROP, so the second emergency fires."""
    e = EmergencyEngine()
    e.update(8, V_FALL_STILL)
    assert e.pop_incident() is not None
    score, state, _ = e.update(8, V_FALL)  # 55, MONITORING
    assert (score, state) == (55.0, "MONITORING")
    assert e.pop_incident() is None  # no new incident yet
    score, state, _ = e.update(8, V_FALL_STILL)  # back to 80
    assert state == "POSSIBLE_EMERGENCY"
    assert e.pop_incident() is not None  # second fall fires


def test_audio_window_is_short():
    """A shout older than AUDIO_WINDOW_SEC no longer stacks onto vision."""
    e = EmergencyEngine(EngineConfig(AUDIO_WINDOW_SEC=10.0))
    e._audio.append({"t": time.time() - 11, "kind": "DISTRESS_KEYWORD", "detail": "help"})
    score, _, ev = e.update(9, V_FALL)
    assert score == 55.0
    assert "DISTRESS_KEYWORD" not in {s for s, _ in ev}
