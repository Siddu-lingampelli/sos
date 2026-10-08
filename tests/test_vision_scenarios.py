"""Level 10 scenario checks for the Level 3-7 fixes (no camera, no DB).

Each function is one scenario from SOS_PLAN.md section 10.1, asserting the
decision the pipeline should reach. These are the false-positive cases the
plan calls out explicitly (kneeling, intentional lying) plus the positive ones.

Level 10.2: These tests now also collect metrics for evaluation.
"""
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "ai", "vision"))
sys.path.insert(0, os.path.join(_HERE, "..", "ai", "engine"))

# Level 10.2 metrics support
try:
    from metrics_collector import MetricsCollector, Outcome
    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False
    MetricsCollector = None
    Outcome = None

from config import FallConfig
from fall_detector import FallDetector
from inactivity import InactivityMonitor
from fusion import EmergencyEngine


def _kp(head=None, ankles=None):
    """Build a 17-keypoint list; pass (y, conf) or None to leave low-conf."""
    kps = [[0, 0, 0.0]] * 17
    if head is not None:
        kps[0] = [100.0, head[0], head[1]]
    if ankles is not None:
        kps[15] = [100.0, ankles[0], ankles[1]]
        kps[16] = [110.0, ankles[0], ankles[1]]
    return kps


def _person(**kw):
    base = {"track_id": 1, "angle": 10.0, "aspect": 0.6, "t": time.time(),
            "box": [0, 0, 100, 300], "keypoints": []}
    base.update(kw)
    return base


# --- Test 10.2 Metrics Collection ------------------------------

# Global metrics collector for Level 10.2 evaluation
_metrics_collector = None

def _get_metrics_collector():
    global _metrics_collector
    if _metrics_collector is None and METRICS_ENABLED:
        _metrics_collector = MetricsCollector()
        _metrics_collector.start_run()
    return _metrics_collector

def _record_scenario_metrics(name, expected, actual, confidence=None, latency=None):
    """Record metrics for Level 10.2 evaluation."""
    if not METRICS_ENABLED:
        return
    collector = _get_metrics_collector()
    if collector and Outcome:
        collector.add_scenario(
            name=name,
            expected=expected,
            actual=actual,
            confidence=confidence,
            latency_ms=latency
        )

# --- Test B/C: normal activity must not alert ------------------------------

def test_standing_person_never_falls():
    fd = FallDetector(FallConfig())
    t0 = time.time()
    states = []
    for i in range(10):
        p = _person(track_id=1, angle=6.0, aspect=0.45, t=t0 + i * 0.1,
                    box=[0, 0, 120, 400], keypoints=_kp(head=(10, 0.9), ankles=(390, 0.9)))
        state = fd.update(p, [])
        states.append(state)

    # Record metrics for Level 10.2
    if METRICS_ENABLED and Outcome:
        fall_detected = any(s != "NORMAL" for s in states)
        _record_scenario_metrics(
            name="Normal Standing",
            expected=Outcome.NO_ALERT,
            actual=Outcome.ALERT if fall_detected else Outcome.NO_ALERT
        )

    assert all(s == "NORMAL" for s in states), f"frame states: {states}"


def test_kneeling_is_not_treated_as_a_fall():
    """Plan 4.5: kneeling must be a false-positive test, not an alert."""
    fd = FallDetector(FallConfig())
    t0 = time.time()
    for i in range(10):
        # Crouched: head high, ankles low, torso still mostly upright.
        p = _person(track_id=1, angle=18.0, aspect=0.85, t=t0 + i * 0.1,
                    box=[0, 0, 170, 100], keypoints=_kp(head=(5, 0.9), ankles=(95, 0.9)))
        assert fd.update(p, []) == "NORMAL", f"frame {i} -> {p['fall_state']}"


def test_intentional_lying_without_a_fall_transition_is_a_no_alert():
    """Plan 7.6: lying down + no fall transition + no audio = no emergency.

    Someone already horizontal accumulates fall+posture evidence (30+15=45),
    which is MONITORING, not an alert. The absence of a rapid drop is what
    keeps them below the threshold, and no incident is ever created.
    """
    eng = EmergencyEngine()
    t0 = time.time()
    fd = FallDetector(FallConfig())
    scores = []
    states = []
    for i in range(6):
        p = _person(track_id=1, angle=85.0, aspect=1.4, t=t0 + i * 0.1,
                    box=[0, 0, 400, 100])
        fd.update(p, [])
        score, state, ev = eng.update(1, p)
        scores.append(score)
        states.append(state)

    incident = eng.pop_incident()

    # Record metrics for Level 10.2
    if METRICS_ENABLED and Outcome:
        _record_scenario_metrics(
            name="Intentional Lying",
            expected=Outcome.NO_ALERT,
            actual=Outcome.ALERT if incident else Outcome.NO_ALERT,
            confidence=max(scores) / 100.0 if scores else 0.0
        )

    # Horizontal persistence registers, but never as a rapid drop.
    assert p["fall_evidence"]["rapid_drop"] is False
    # The decisive property: no alert, no incident, ever.
    assert state == "MONITORING", f"lying down scored {state}"
    assert incident is None


# --- Test A: walking --------------------------------------------------------

def test_walking_horizontally_is_not_horizontal_posture():
    fd = FallDetector(FallConfig())
    p = _person(angle=5.0, aspect=0.5)
    fd.update(p, [])
    assert p["fall_evidence"]["horizontal"] is False


# --- Test E: fall + inactivity must alert -----------------------------------

def test_fall_then_inactivity_produces_possible_emergency():
    cfg = FallConfig(OBSERVATION_DURATION_SEC=0.0, INACTIVITY_THRESHOLD=0.02,
                     RECOVERY_FACTOR=3.0, MOVEMENT_WINDOW_SEC=3.0)
    fd, mon, eng = FallDetector(cfg), InactivityMonitor(cfg), EmergencyEngine()
    t0 = time.time()

    start_time = time.time()

    # Motionless history: the person is down and not moving at all.
    still = [
        {"t": t0 - 1.0, "cx": 0.50, "cy": 0.60, "keypoints": [], "fh": 640},
        {"t": t0, "cx": 0.50, "cy": 0.60, "keypoints": [], "fh": 640},
    ]
    # Fall confirmed first.
    p = _person(track_id=1, angle=88.0, aspect=1.8, t=t0)
    fd.update(p, [])
    p["fall_state"] = "FALL_CONFIRMED"
    mon.update(1, still, "FALL_CONFIRMED")
    mon.update(1, still, "FALL_CONFIRMED")
    assert mon.state[1] == "INACTIVE"

    score, state, ev = eng.update(1, {"fall_state": "FALL_CONFIRMED", "inact_state": "INACTIVE",
                                      "angle": 88.0, "aspect": 1.8})
    signals = {s for s, _ in ev}

    incident = eng.pop_incident()
    latency_ms = (time.time() - start_time) * 1000

    # Record metrics for Level 10.2
    if METRICS_ENABLED and Outcome:
        _record_scenario_metrics(
            name="Fall + Inactivity",
            expected=Outcome.ALERT,
            actual=Outcome.ALERT if incident else Outcome.NO_ALERT,
            confidence=score / 100.0,
            latency=latency_ms
        )

    assert "FALL_DETECTED" in signals
    assert "POST_FALL_INACTIVITY" in signals
    assert state == "POSSIBLE_EMERGENCY"
    assert incident is not None


# --- Test D: fall + quick recovery must clear ------------------------------

def test_fall_then_quick_recovery_clears_the_emergency():
    cfg = FallConfig(OBSERVATION_DURATION_SEC=0.0, INACTIVITY_THRESHOLD=0.02,
                     RECOVERY_FACTOR=3.0, MOVEMENT_WINDOW_SEC=3.0)
    mon = InactivityMonitor(cfg)
    t0 = time.time()
    # Large movement: the person is getting up.
    moving = [
        {"t": t0 - 0.3, "cx": 0.20, "cy": 0.60, "keypoints": [], "fh": 640},
        {"t": t0, "cx": 0.50, "cy": 0.40, "keypoints": [], "fh": 640},
    ]
    mon.update(1, moving, "FALL_CONFIRMED")
    assert mon.state[1] == "OBSERVING"
    assert mon.update(1, moving, "FALL_CONFIRMED") == "IDLE"
    assert any(e["type"] == "RECOVERY_DETECTED" for e in mon.events)
    assert not any(e["type"] == "POSSIBLE_EMERGENCY" for e in mon.events)


# --- Test G: fall + distress audio stacks evidence -------------------------

def test_distress_audio_adds_to_a_fall_score():
    eng = EmergencyEngine()
    vision = {"fall_state": "FALL_CONFIRMED", "inact_state": "IDLE", "angle": 80.0, "aspect": 1.5}
    s_no_audio, st_no, _ = eng.update(1, vision)
    # Fall alone (40 + 15 posture) is MONITORING, never an emergency by itself.
    assert (s_no_audio, st_no) == (55.0, "MONITORING")
    assert eng.pop_incident() is None

    eng.audio_event("DISTRESS_KEYWORD", "help")
    s_audio, st_audio, ev_audio = eng.update(1, vision)
    assert s_audio > s_no_audio
    assert st_audio == "POSSIBLE_EMERGENCY"  # 55 + 20 = 75
    assert "DISTRESS_KEYWORD" in {sig for sig, _ in ev_audio}
    assert eng.pop_incident() is not None
