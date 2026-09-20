"""Local distress/scream classifier (Level 6 prototype).

Pure-numpy spectral gate — no model download, runs anywhere:
  scream ~= loud (RMS gate) + high-pitched (spectral centroid + HF ratio)
           + sustained (caller feeds WINDOW_MS blocks; score smooths over time)

Score 0..1. Tune SCREAM_* in audio_config.py with real test audio.
A pretrained HF emotion/arousal model can replace this later behind the
same .score() interface.
"""
import numpy as np
from audio_config import AudioConfig, DEFAULT_AUDIO


class DistressClassifier:
    def __init__(self, cfg: AudioConfig = DEFAULT_AUDIO):
        self.cfg = cfg
        self._smooth = 0.0

    @staticmethod
    def _features(audio: np.ndarray, sr: int):
        rms = float(np.sqrt(np.mean(audio ** 2) + 1e-12))
        if rms < 1e-9:
            return rms, 0.0, 0.0
        mag = np.abs(np.fft.rfft(audio * np.hanning(len(audio))))
        freqs = np.fft.rfftfreq(len(audio), 1.0 / sr)
        centroid = float(np.sum(freqs * mag) / (np.sum(mag) + 1e-12))
        hf = float(np.sum(mag[freqs >= 2000]) / (np.sum(mag) + 1e-12))
        return rms, centroid, hf

    def score(self, audio: np.ndarray) -> float:
        """Distress score 0..1 for one WINDOW_MS block (smoothed)."""
        cfg = self.cfg
        audio = np.asarray(audio, dtype=np.float32)
        need = int(cfg.SR * cfg.WINDOW_MS / 1000)
        if len(audio) < need:
            audio = np.pad(audio, (0, need - len(audio)))
        else:
            audio = audio[:need]

        rms, centroid, hf = self._features(audio, cfg.SR)
        if rms < cfg.SCREAM_RMS_GATE:
            raw = 0.0
        else:
            loud = min(1.0, rms / (cfg.SCREAM_RMS_GATE * 4))
            pitch = min(1.0, max(0.0, centroid / (cfg.SCREAM_CENTROID_HZ * 2)))
            raw = 0.5 * loud + 0.3 * pitch + 0.2 * hf
        # EMA smoothing ~ SCREAM_MIN_MS sustain requirement
        alpha = min(1.0, cfg.WINDOW_MS / max(1, cfg.SCREAM_MIN_MS))
        self._smooth = alpha * raw + (1 - alpha) * self._smooth
        return round(float(self._smooth), 3)

    def reset(self):
        self._smooth = 0.0
