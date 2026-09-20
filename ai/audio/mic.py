"""Audio input: live microphone (sounddevice) + recorded WAV files (stdlib).

Both yield mono float32 @16kHz blocks. sounddevice is imported lazily so the
module (and tests) load fine on machines without a mic or the package.
"""
import queue
import wave
import numpy as np
from audio_config import AudioConfig, DEFAULT_AUDIO


class MicStream:
    def __init__(self, cfg: AudioConfig = DEFAULT_AUDIO):
        self.cfg = cfg
        self.q: queue.Queue = queue.Queue(maxsize=64)
        self.stream = None

    def _cb(self, indata, frames, t, status):
        try:
            self.q.put_nowait(indata[:, 0].astype(np.float32).copy())
        except queue.Full:
            pass  # drop oldest-block overflow; realtime over completeness

    def start(self, device=None):
        import sounddevice as sd
        self.stream = sd.InputStream(samplerate=self.cfg.SR, channels=1,
                                     dtype="float32", blocksize=self.cfg.CHUNK,
                                     callback=self._cb, device=device)
        self.stream.start()

    def read(self, timeout=1.0):
        try:
            return self.q.get(timeout=timeout)
        except queue.Empty:
            return None

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    @staticmethod
    def list_devices():
        import sounddevice as sd
        return sd.query_devices()


class WavSource:
    """Recorded-audio input for tests/demos. Requires 16-bit PCM mono WAV."""

    def __init__(self, path: str, cfg: AudioConfig = DEFAULT_AUDIO):
        self.cfg = cfg
        wf = wave.open(path, "rb")
        if wf.getsampwidth() != 2 or wf.getnchannels() != 1:
            raise ValueError("Only 16-bit mono WAV supported for Level 6 prototype")
        if wf.getframerate() != cfg.SR:
            raise ValueError(f"WAV must be {cfg.SR}Hz (got {wf.getframerate()}Hz)")
        raw = wf.readframes(wf.getnframes())
        wf.close()
        self.audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        self.pos = 0

    def read(self, timeout=1.0):
        if self.pos >= len(self.audio):
            return None
        blk = self.audio[self.pos:self.pos + self.cfg.CHUNK]
        self.pos += self.cfg.CHUNK
        if len(blk) < self.cfg.CHUNK:
            blk = np.pad(blk, (0, self.cfg.CHUNK - len(blk)))
        return blk

    def stop(self):
        pass
