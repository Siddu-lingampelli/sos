"""Local speech-to-text via faster-whisper (lazy-load, tiny model on CPU)."""
import numpy as np
from audio_config import AudioConfig, DEFAULT_AUDIO


class Transcriber:
    def __init__(self, cfg: AudioConfig = DEFAULT_AUDIO):
        self.cfg = cfg
        self.model = None

    def _load(self):
        from faster_whisper import WhisperModel
        self.model = WhisperModel(self.cfg.WHISPER_SIZE, device=self.cfg.WHISPER_DEVICE,
                                  compute_type="int8")

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe a mono float32 @16kHz speech segment -> lowercase text."""
        if self.model is None:
            self._load()
        segments, _info = self.model.transcribe(audio, beam_size=1, vad_filter=False)
        return " ".join(s.text for s in segments).strip().lower()
