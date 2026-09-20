"""Audio event pipeline (Level 6 deliverable).

Mic/WAV blocks -> Silero VAD chunks -> speech segments -> faster-whisper
-> keyword match,  PLUS  parallel 1s-window scream classifier.

Emits structured events (bounded deque, same pattern as vision):
  SPEECH_DETECTED / DISTRESS_KEYWORD / DISTRESS_SOUND
VAD/transcriber/classifier are injectable so tests run with zero downloads.
"""
import time
from collections import deque
import numpy as np
from audio_config import AudioConfig, DEFAULT_AUDIO
from vad import SileroVAD
from transcribe import Transcriber
from keywords import match_keywords
from classifier import DistressClassifier


class AudioPipeline:
    def __init__(self, cfg: AudioConfig = DEFAULT_AUDIO, vad=None,
                 transcriber=None, classifier=None, keywords=None):
        self.cfg = cfg
        self.vad = vad or SileroVAD(cfg)
        self.transcriber = transcriber or Transcriber(cfg)
        self.classifier = classifier or DistressClassifier(cfg)
        self.keywords = tuple(keywords) if keywords else cfg.KEYWORDS
        self.events: deque[dict] = deque(maxlen=500)
        self._speech_buf: list[np.ndarray] = []
        self._silence_ms = 0
        self._win_buf: list[np.ndarray] = []
        self._win_ms = 0
        self._chunk_ms = cfg.CHUNK * 1000 / cfg.SR

    def _emit(self, ev: dict):
        ev["t"] = time.time()
        self.events.append(ev)
        return ev

    def _flush_speech(self):
        if not self._speech_buf:
            return []
        audio = np.concatenate(self._speech_buf)
        self._speech_buf = []
        dur_ms = len(audio) * 1000 / self.cfg.SR
        if dur_ms < self.cfg.MIN_SPEECH_MS:
            return []
        out = [self._emit({"type": "SPEECH_DETECTED", "duration_ms": round(dur_ms)})]
        try:
            text = self.transcriber.transcribe(audio)
        except Exception as e:
            return out + [self._emit({"type": "TRANSCRIBE_ERROR", "error": str(e)[:120]})]
        hits = match_keywords(text, self.keywords)
        if hits:
            out.append(self._emit({"type": "DISTRESS_KEYWORD", "text": text, "keywords": hits}))
        return out

    def process_block(self, block: np.ndarray) -> list[dict]:
        """Consume one mic/WAV block (any multiple of CHUNK). Returns new events."""
        cfg = self.cfg
        events: list[dict] = []
        n = len(block) // cfg.CHUNK
        for i in range(n):
            chunk = np.asarray(block[i * cfg.CHUNK:(i + 1) * cfg.CHUNK], dtype=np.float32)
            try:
                p = self.vad.prob(chunk)
            except Exception as e:
                return events + [self._emit({"type": "VAD_ERROR", "error": str(e)[:120]})]
            if p >= cfg.VAD_THRESHOLD:
                self._speech_buf.append(chunk)
                self._silence_ms = 0
            else:
                self._silence_ms += self._chunk_ms
                if self._speech_buf and self._silence_ms >= cfg.MIN_SILENCE_MS:
                    events += self._flush_speech()
                    self._silence_ms = 0
            # Parallel scream window (runs on ALL audio, speech or not)
            self._win_buf.append(chunk)
            self._win_ms += self._chunk_ms
            if self._win_ms >= cfg.WINDOW_MS:
                window = np.concatenate(self._win_buf)
                self._win_buf, self._win_ms = [], 0
                try:
                    s = self.classifier.score(window)
                except Exception as e:
                    events.append(self._emit({"type": "CLASSIFIER_ERROR", "error": str(e)[:120]}))
                    continue
                if s >= cfg.SCREAM_THRESHOLD:
                    events.append(self._emit({"type": "DISTRESS_SOUND", "score": s}))
        return events

    def flush(self) -> list[dict]:
        """Call at end of file/stream to emit any trailing speech."""
        return self._flush_speech()
