"""Level 4 tunable thresholds — do NOT hard-code in logic. Tune with test videos.

Environment overrides (SOS_ prefix) so operators can tune without editing
code, and so standalone runs honor the same knobs as the backend:
  SOS_DETECT_STRIDE, SOS_IMGSZ, SOS_INFER_WIDTH, SOS_OBSERVATION_DURATION_SEC,
  SOS_INACTIVITY_THRESHOLD, SOS_BOX_CONF, SOS_KP_CONF
"""
import os
from dataclasses import dataclass


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@dataclass
class FallConfig:
    # Torso angle (deg from vertical): 0=upright, 90=horizontal
    FALL_ANGLE_THRESHOLD: float = 55.0
    # BBox aspect w/h above which posture looks horizontal
    FALL_ASPECT_THRESHOLD: float = 0.9
    # Head-to-ankle vertical span over bbox height. A standing person is near
    # 1.0; a lying person is a small fraction of their box height. Used to
    # separate "lying down" from "crouching" which aspect alone cannot tell.
    HORIZONTAL_SPAN_RATIO: float = 0.45
    # Sudden hip-center drop (normalized by frame height per second) to qualify as "rapid"
    FALL_VERTICAL_VELOCITY: float = 0.20
    # Hip drop below this fraction of frame height is pose jitter, not a fall.
    # Without this floor, a slow sit-down or a noisy keypoint reads as a
    # "rapid drop" purely because the rate over a short window looks high.
    MIN_DROP_FRAC: float = 0.12
    # Trailing frames considered for velocity. Keep short: a fall is ~0.4 s,
    # so a wide window dilutes the impact with the stillness that follows it.
    VELOCITY_WINDOW_FRAMES: int = 5
    # Consecutive horizontal frames to go POSSIBLE_FALL -> FALL_CONFIRMED
    CONFIRM_FRAMES: int = 3
    # Frames of upright + movement to go FALL_* -> RECOVERED -> NORMAL
    RECOVERY_FRAMES: int = 4
    # Consecutive upright frames required before leaving POSSIBLE_FALL
    UPRIGHT_EXIT_FRAMES: int = 2
    # Max history per track
    HISTORY_LEN: int = 30
    # Minimum keypoint confidence to trust a joint (lower for fallen people)
    KP_CONF: float = 0.25
    # Minimum YOLO box confidence (balanced: 0.25 ignores most wires, but catches crumpled fallen bodies)
    BOX_CONF: float = 0.25
    # Inference image size (smaller = faster on CPU)
    IMGSZ: int = 320
    # Downscale huge camera frames (1080p phones) before YOLO, scale boxes back
    INFER_WIDTH: int = 640
    # Run YOLO every Nth frame, reuse last result in between (big CPU saver)
    DETECT_STRIDE: int = 4
    # Max width of streamed/drawn frame (downscaled before JPEG encode)
    STREAM_WIDTH: int = 512
    # JPEG quality for MJPEG stream (lower = less bandwidth/CPU)
    JPEG_QUALITY: int = 60
    # --- Level 5: post-fall observation + inactivity ---
    # Seconds to watch a fallen person before judging inactivity
    OBSERVATION_DURATION_SEC: float = 10.0
    # Movement score per second below which the person counts as motionless
    # (normalized frame units; tune with test videos)
    INACTIVITY_THRESHOLD: float = 0.02
    # Movement above threshold * this factor cancels observation (recovery)
    RECOVERY_FACTOR: float = 3.0
    # Seconds of history used for the movement score
    MOVEMENT_WINDOW_SEC: float = 3.0


DEFAULT = FallConfig(
    DETECT_STRIDE=_env_int("SOS_DETECT_STRIDE", 4),
    IMGSZ=_env_int("SOS_IMGSZ", 320),
    INFER_WIDTH=_env_int("SOS_INFER_WIDTH", 640),
    BOX_CONF=_env_float("SOS_BOX_CONF", 0.25),
    KP_CONF=_env_float("SOS_KP_CONF", 0.25),
    OBSERVATION_DURATION_SEC=_env_float("SOS_OBSERVATION_DURATION_SEC", 10.0),
    INACTIVITY_THRESHOLD=_env_float("SOS_INACTIVITY_THRESHOLD", 0.02),
)
