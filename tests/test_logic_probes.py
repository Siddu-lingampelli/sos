"""Adversarial regression probes (20yr-tester suite): hostile inputs must not
crash the pipeline or fire false events. No mic, no downloads."""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai", "audio")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai", "vision")))

from audio_config import AudioConfig
from classifier import DistressClassifier
from visualizer import Visualizer

SR = 16000


def _sine(freq=2000, amp=0.4):
    t = np.arange(SR) / SR
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def test_scream_needs_sustain_single_blip_silent():
    c = DistressClassifier(AudioConfig())
    assert c.score(_sine()) < AudioConfig().SCREAM_THRESHOLD  # one hot window must NOT fire


def test_scream_fires_on_second_consecutive_window():
    c = DistressClassifier(AudioConfig())
    c.score(_sine())
    assert c.score(_sine()) >= AudioConfig().SCREAM_THRESHOLD


def test_fan_rumble_never_fires():
    c = DistressClassifier(AudioConfig())
    scores = [c.score(_sine(freq=100, amp=0.5)) for _ in range(5)]
    assert max(scores) < AudioConfig().SCREAM_THRESHOLD, scores


def test_visualizer_survives_malformed_persons():
    viz = Visualizer()
    img = np.zeros((240, 320, 3), np.uint8)
    hostile = [{"track_id": 1}, {"box": None}, {"box": ["a", "b", "c", "d"]},
               {"box": [1, 2]}, {"box": [10, 10, 50, 50]}]
    assert viz.draw(img, hostile, 30.0, 0.01).shape == (240, 320, 3)
