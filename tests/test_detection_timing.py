"""Timing realism checks for the Level 4 fall detector.

The audit found hip velocity was averaged over a fixed 8-frame window, which at
DETECT_STRIDE 3 and ~15 fps spans ~1.6 s and diluted a 0.4 s fall below
threshold. These tests reproduce that exact frame cadence.
"""
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "ai", "vision"))

from config import FallConfig
from fall_detector import FallDetector


def _hist(t0, y_by_t, stride_sec):
    return [{"hip_y": y, "t": t0 + dt} for dt, y in y_by_t]


def test_real_fall_at_production_cadence_is_detected_as_rapid_drop():
    """15 fps camera, DETECT_STRIDE 3 -> inference every ~0.2 s.

    A person standing, falling over ~0.4 s, then lying still. The pipeline
    evaluates on every stride frame, so at the frame just after impact the
    steepest descent must clear FALL_VERTICAL_VELOCITY (0.20/s).
    """
    cfg = FallConfig()
    fd = FallDetector(cfg)
    t0 = time.time()

    # Standing at hip_y 0.25, dropping to 0.65 across two stride frames.
    series = [(0.0, 0.25), (0.2, 0.25), (0.4, 0.62), (0.6, 0.65)]
    hist = _hist(t0, series, 0.2)

    vel = fd._hip_velocity(hist)
    assert vel >= cfg.FALL_VERTICAL_VELOCITY, (
        f"a real 0.4 s fall produced {vel:.3f}/s, below the "
        f"{cfg.FALL_VERTICAL_VELOCITY}/s threshold"
    )


def test_velocity_window_is_long_enough_to_see_the_impact():
    """The trailing window must span a whole fall, not just its aftermath."""
    cfg = FallConfig()
    # A 0.4 s fall at 0.2 s per inference frame spans ~2 frames; the window
    # needs headroom for a slower camera cadence.
    assert cfg.VELOCITY_WINDOW_FRAMES >= 3
    # And it must stay short, or a long fall dilutes back below threshold.
    assert cfg.VELOCITY_WINDOW_FRAMES <= 8


def test_person_standing_still_is_not_a_rapid_drop():
    cfg = FallConfig()
    fd = FallDetector(cfg)
    t0 = time.time()
    hist = _hist(t0, [(i * 0.2, 0.30) for i in range(8)], 0.2)
    assert fd._hip_velocity(hist) == 0.0


def test_slow_sit_down_is_not_treated_as_a_fall():
    """Sitting down over 2 s is a normal action, not a fall."""
    cfg = FallConfig()
    fd = FallDetector(cfg)
    t0 = time.time()
    hist = _hist(t0, [(0.0, 0.30), (0.2, 0.34), (0.4, 0.38), (0.6, 0.42),
                      (0.8, 0.45), (1.0, 0.47)], 0.2)
    vel = fd._hip_velocity(hist)
    assert vel < cfg.FALL_VERTICAL_VELOCITY, (
        f"a 2 s sit-down read as {vel:.3f}/s rapid drop"
    )


def test_standing_up_after_a_fall_is_a_rise_not_a_drop():
    """Hip y decreases in image coords when standing up; sign must not flip."""
    cfg = FallConfig()
    fd = FallDetector(cfg)
    t0 = time.time()
    hist = _hist(t0, [(0.0, 0.65), (0.2, 0.60), (0.4, 0.45), (0.6, 0.30)], 0.2)
    assert fd._hip_velocity(hist) < 0, "standing up should be negative velocity"
