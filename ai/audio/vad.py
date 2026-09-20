"""Silero VAD wrapper (local, no cloud). Lazy-loads torch.hub model on first use.

Input: 512-sample float32 chunks @16kHz. Output: speech probability 0..1.
Segmentation (speech start/stop) lives in pipeline.py — this stays a pure
per-chunk scorer so tests can substitute a FakeVAD.
"""
import numpy as np
from audio_config import AudioConfig, DEFAULT_AUDIO


class SileroVAD:
    def __init__(self, cfg: AudioConfig = DEFAULT_AUDIO):
        self.cfg = cfg
        self.model = None

    def _load(self):
        import torch
        self.model, _utils = torch.hub.load(repo_or_dir="snakers4/silero-vad",
                                            model="silero_vad", force_reload=False)
        self.model.eval()

    def reset(self):
        if self.model is not None:
            try:
                self.model.reset_states()
            except Exception:
                pass

    def prob(self, chunk: np.ndarray) -> float:
        """Speech probability for one 512-sample chunk."""
        if self.model is None:
            self._load()
        import torch
        with torch.no_grad():
            return float(self.model(torch.from_numpy(chunk), self.cfg.SR).item())
