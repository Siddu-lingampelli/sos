"""Level 4 tunable thresholds — do NOT hard-code in logic. Tune with test videos."""
from dataclasses import dataclass


@dataclass
class FallConfig:
    # Torso angle (deg from vertical): 0=upright, 90=horizontal
    FALL_ANGLE_THRESHOLD: float = 55.0
    # BBox aspect w/h above which posture looks horizontal
    FALL_ASPECT_THRESHOLD: float = 0.9
    # Sudden hip-center drop (normalized by frame height per second) to qualify as "rapid"
    FALL_VERTICAL_VELOCITY: float = 0.20
    # Consecutive horizontal frames to go POSSIBLE_FALL -> FALL_CONFIRMED
    CONFIRM_FRAMES: int = 3
    # Frames of upright + movement to go FALL_* -> RECOVERED -> NORMAL
    RECOVERY_FRAMES: int = 4
    # Max history per track
    HISTORY_LEN: int = 30
    # Minimum keypoint confidence to trust a joint (lower for fallen people)
    KP_CONF: float = 0.25
    # Minimum YOLO box confidence (balanced: 0.25 ignores most wires, but catches crumpled fallen bodies)
    BOX_CONF: float = 0.25
    # Inference image size (smaller = faster on CPU)
    IMGSZ: int = 416
    # Downscale huge camera frames (1080p phones) before YOLO, scale boxes back
    INFER_WIDTH: int = 640
    # Run YOLO every Nth frame, reuse last result in between (big CPU saver)
    DETECT_STRIDE: int = 3
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


DEFAULT = FallConfig()
