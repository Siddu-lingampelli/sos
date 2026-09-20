"""Activity narration tests (no camera needed)."""
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai", "vision")))

from activity import ActivityLog, speed_class


def _hist(dx_per_frame=0.0, n=10, step=0.1):
    t = time.time()
    return [{"cx": 0.3 + i * dx_per_frame, "cy": 0.5, "t": t + i * step} for i in range(n)]


def test_speed_classes():
    assert speed_class(_hist(0.0)) == "still"
    assert speed_class(_hist(0.02)) == "walking"  # 0.2 units/s
    assert speed_class(_hist(0.08)) == "running"  # 0.8 units/s
    assert speed_class([]) == "still"


def test_entered_once_then_transitions():
    log = ActivityLog()
    h = _hist()
    evs = log.update(1, {"fall_state": "NORMAL", "inact_state": "IDLE"}, h)
    assert [e["tag"] for e in evs] == ["TRACK"]
    assert log.update(1, {"fall_state": "NORMAL", "inact_state": "IDLE"}, h) == []
    evs = log.update(1, {"fall_state": "POSSIBLE_FALL", "inact_state": "IDLE"}, h)
    assert ("FALL", "Person #1: NORMAL -> POSSIBLE_FALL") in [(e["tag"], e["text"]) for e in evs]
    evs = log.update(1, {"fall_state": "POSSIBLE_FALL", "inact_state": "OBSERVING"}, h)
    assert any(e["tag"] == "STILL" for e in evs)


def test_move_emits_only_on_change_to_motion():
    log = ActivityLog()
    log.update(2, {"fall_state": "NORMAL", "inact_state": "IDLE"}, _hist())
    evs = log.update(2, {"fall_state": "NORMAL", "inact_state": "IDLE"}, _hist(0.02))
    assert any(e["text"] == "Person #2 walking" for e in evs)
    assert log.update(2, {"fall_state": "NORMAL", "inact_state": "IDLE"}, _hist(0.02)) == []


def test_prune_forgets_tracks():
    log = ActivityLog()
    log.update(3, {"fall_state": "NORMAL", "inact_state": "IDLE"}, _hist())
    log.prune([])
    evs = log.update(3, {"fall_state": "NORMAL", "inact_state": "IDLE"}, _hist())
    assert [e["tag"] for e in evs] == ["TRACK"]
