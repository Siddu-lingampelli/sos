"""Level 6 audio tests (no mic, no downloads — fakes for VAD/whisper)."""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai", "audio")))

from audio_config import AudioConfig
from keywords import match_keywords
from classifier import DistressClassifier
from pipeline import AudioPipeline

SR = 16000


def _sine(freq=2000, secs=1.0, amp=0.4):
    t = np.arange(int(SR * secs)) / SR
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)


class FakeVAD:
    def __init__(self, probs):
        self.probs = list(probs)

    def prob(self, chunk):
        return self.probs.pop(0) if self.probs else 0.0

    def reset(self):
        pass


class FakeTranscriber:
    def __init__(self, text):
        self.text = text

    def transcribe(self, audio):
        return self.text


def _pipe(vad_probs, text="hello world", **cfg_kw):
    cfg = AudioConfig(**cfg_kw)
    return AudioPipeline(cfg, vad=FakeVAD(vad_probs), transcriber=FakeTranscriber(text))


def test_keyword_match_basic_and_phrase():
    assert match_keywords("PLEASE HELP me", ("help", "please help")) == ["help", "please help"]
    assert match_keywords("just helpful advice", ("help",)) == []  # word boundary
    assert match_keywords("this is an emergency!", ("emergency",)) == ["emergency"]


def test_classifier_scream_vs_silence():
    cfg = AudioConfig()
    c = DistressClassifier(cfg)
    loud = [_sine(2000, 1.0, 0.4) for _ in range(3)]
    scores = [c.score(w) for w in loud]
    assert scores[-1] >= cfg.SCREAM_THRESHOLD, scores
    c.reset()
    assert c.score(np.zeros(SR, dtype=np.float32)) == 0.0


def test_classifier_short_beep_stays_low():
    cfg = AudioConfig()
    c = DistressClassifier(cfg)
    # single loud window then silence: smoothing keeps single-window spike bounded
    s1 = c.score(_sine(2000, 1.0, 0.5))
    assert s1 < 1.0


def test_pipeline_speech_and_keyword_events():
    probs = [0.9] * 10 + [0.05] * 12  # speech then silence -> flush
    p = _pipe(probs, text="someone please help me", MIN_SILENCE_MS=300)
    evs = []
    # feed chunk by chunk (content irrelevant — FakeVAD drives segmentation)
    for i in range(22):
        evs += p.process_block(np.zeros(512, dtype=np.float32))
    types = [e["type"] for e in evs]
    assert "SPEECH_DETECTED" in types, types
    assert "DISTRESS_KEYWORD" in types, types
    kw = [e for e in evs if e["type"] == "DISTRESS_KEYWORD"][0]
    assert "please help" in kw["keywords"] and "someone help" not in kw["keywords"]


def test_pipeline_distress_sound_path():
    cfg = AudioConfig()
    # VAD silent, classifier loud -> DISTRESS_SOUND without any speech events
    p = AudioPipeline(cfg, vad=FakeVAD([0.0] * 200), transcriber=FakeTranscriber("zzz"))
    evs = []
    for _ in range(4):
        evs += p.process_block(_sine(2200, 1.0, 0.5))
    assert any(e["type"] == "DISTRESS_SOUND" for e in evs), [e["type"] for e in evs]
    assert not any(e["type"] == "SPEECH_DETECTED" for e in evs)
