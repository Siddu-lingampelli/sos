"""Level 4 fall-detector unit tests (no DB, no camera)."""
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai", "vision")))

from fall_detector import FallDetector
from config import FallConfig


def _person(angle, aspect, tid=7):
    return {"track_id": tid, "angle": angle, "aspect": aspect, "hip_y": 0.5, "t": time.time()}


def test_single_bend_does_not_trigger():
    fd = FallDetector(FallConfig(CONFIRM_FRAMES=3, RECOVERY_FRAMES=2, FALL_VERTICAL_VELOCITY=99))
    hist = [_person(5, 0.5) for _ in range(5)]
    assert fd.update(_person(5, 0.5), hist) == "NORMAL"
    # one horizontal frame only -> still NORMAL
    hist.append(_person(80, 1.5))
    assert fd.update(_person(80, 1.5), hist) == "NORMAL"


def test_persistent_horizontal_triggers_possible_fall():
    fd = FallDetector(FallConfig(CONFIRM_FRAMES=2, RECOVERY_FRAMES=2, FALL_VERTICAL_VELOCITY=99))
    hist = [_person(5, 0.5) for _ in range(5)]
    fd.update(_person(5, 0.5), hist)
    hist.append(_person(80, 1.5))
    fd.update(_person(80, 1.5), hist)
    hist.append(_person(80, 1.5))
    assert fd.update(_person(80, 1.5), hist) == "POSSIBLE_FALL"
    assert any(e["to"] == "POSSIBLE_FALL" for e in fd.events)


def test_jwt_expiry_claim():
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
    from app.core.security import create_access_token, decode_access_token
    tok = create_access_token({"sub": "test@example.com"})
    payload = decode_access_token(tok)
    assert payload is not None and payload["sub"] == "test@example.com"
    assert "exp" in payload
