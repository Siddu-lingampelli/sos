"""Level 4 tunable thresholds — do NOT hard-code in logic. Tune with test videos."""
from dataclasses import dataclass


@dataclass
class FallConfig:
    # Torso angle (deg from vertical): 0=upright, 90=horizontal
    FALL_ANGLE_THRESHOLD: float = 55.0
    # BBox aspect w/h above which posture looks horizontal
    FALL_ASPECT_THRESHOLD: float = 1.1
    # Sudden hip-center drop (normalized by frame height per second) to qualify as "rapid"
    FALL_VERTICAL_VELOCITY: float = 0.35
    # Consecutive horizontal frames to go POSSIBLE_FALL -> FALL_CONFIRMED
    CONFIRM_FRAMES: int = 8
    # Frames of upright + movement to go FALL_* -> RECOVERED -> NORMAL
    RECOVERY_FRAMES: int = 10
    # Max history per track
    HISTORY_LEN: int = 30
    # Minimum keypoint confidence to trust a joint
    KP_CONF: float = 0.4
    # Minimum YOLO box confidence
    BOX_CONF: float = 0.15


DEFAULT = FallConfig()
