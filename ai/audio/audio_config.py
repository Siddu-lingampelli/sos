"""Level 6 tunable thresholds — do NOT hard-code in logic. Tune with test audio."""
from dataclasses import dataclass, field


@dataclass
class AudioConfig:
    SR: int = 16000
    CHUNK: int = 512  # 32ms @16kHz — Silero VAD native frame
    # --- Silero VAD ---
    VAD_THRESHOLD: float = 0.5
    MIN_SPEECH_MS: int = 250
    MIN_SILENCE_MS: int = 300
    # --- faster-whisper ---
    WHISPER_SIZE: str = "tiny"  # tiny/base/small; CPU: tiny recommended
    WHISPER_DEVICE: str = "cpu"
    # --- distress keywords (configurable, matched case-insensitive) ---
    KEYWORDS: tuple = ("help", "emergency", "please help", "someone help")
    # --- scream/distress classifier (heuristic spectral gate) ---
    SCREAM_RMS_GATE: float = 0.05      # min loudness to even consider
    SCREAM_CENTROID_HZ: float = 1500.0  # screams carry high-frequency energy
    SCREAM_MIN_MS: int = 400            # must sustain this long
    SCREAM_THRESHOLD: float = 0.6       # score 0..1 above which we emit
    WINDOW_MS: int = 1000               # classifier analysis window


DEFAULT_AUDIO = AudioConfig()
