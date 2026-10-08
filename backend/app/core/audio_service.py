"""Global audio service for the backend.

Runs the Level 6 AudioPipeline in a background thread connected to the
server's default microphone. Dispatches detected distress audio to:
1. All active EmergencyEngines (to fuse with vision and boost scores).
2. The WebSocket AlertBus (to show live audio events in dashboard logs).
"""
import sys
import os
import threading
import time

from .bus import bus
from .health import health

ai_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../ai"))
if ai_path not in sys.path:
    sys.path.append(ai_path)
audio_path = os.path.join(ai_path, "audio")
if audio_path not in sys.path:
    sys.path.append(audio_path)

try:
    from audio_config import AudioConfig
    from pipeline import AudioPipeline
    from mic import MicStream
    AUDIO_AVAILABLE = True
except ImportError as e:
    AUDIO_AVAILABLE = False
    print(f"WARNING: Could not import AI audio modules: {e}")
    health.set("audio", "down", f"import failed: {e}")

_lock = threading.Lock()
_engines = []
_thread = None
_running = False

def register_engine(engine):
    with _lock:
        if engine not in _engines:
            _engines.append(engine)

def unregister_engine(engine):
    with _lock:
        if engine in _engines:
            _engines.remove(engine)

def _audio_loop():
    print("[audio] Starting global mic stream...")
    # .env knobs (AUDIO_KEYWORDS, WHISPER_MODEL_SIZE) take effect here so the
    # example env actually does something.
    try:
        from .config import settings
        keywords = settings.audio_keywords
        whisper_size = settings.WHISPER_MODEL_SIZE
    except Exception as exc:  # noqa: BLE001
        print(f"[audio] could not read settings: {exc}")
        keywords, whisper_size = None, None
    cfg = AudioConfig()
    if whisper_size:
        cfg.WHISPER_SIZE = whisper_size
    print(f"[audio] distress keywords: {keywords or cfg.KEYWORDS}")
    pipe = AudioPipeline(cfg, keywords=keywords)
    try:
        src = MicStream(cfg)
        src.start()
        health.set("audio", "ok", "listening")
    except Exception as e:
        print(f"[audio] Failed to start microphone: {e}")
        health.set("audio", "down", f"mic start failed: {e}")
        bus.broadcast_sync({"type": "system", "component": "audio",
                            "status": "down", "detail": str(e)})
        return

    while _running:
        blk = src.read(timeout=0.5)
        if blk is None:
            continue
            
        try:    
            events = pipe.process_block(blk)
        except Exception as e:
            print(f"[audio] pipeline error: {e}")
            health.set("audio", "degraded", f"pipeline error: {e}")
            continue
            
        for ev in events:
            kind = ev["type"]
            detail = ""
            if kind == "DISTRESS_KEYWORD":
                detail = f"keywords: {', '.join(ev.get('keywords', []))}"
                bus.broadcast_sync({"type": "activity", "tag": "AUDIO", "text": f"Distress keyword: {ev.get('text', '')}"})
            elif kind == "DISTRESS_SOUND":
                detail = f"score: {ev.get('score', 0)}"
                bus.broadcast_sync({"type": "activity", "tag": "AUDIO", "text": f"Distress sound (scream) detected! {detail}"})
            elif kind == "SPEECH_DETECTED":
                bus.broadcast_sync({"type": "activity", "tag": "AUDIO", "text": "Speech detected"})
            
            # Fan out to all active vision engines
            if kind in ("DISTRESS_KEYWORD", "DISTRESS_SOUND"):
                with _lock:
                    for eng in _engines:
                        eng.audio_event(kind, detail)

    src.stop()
    print("[audio] Stream stopped.")

def start_audio_service():
    global _thread, _running
    if not AUDIO_AVAILABLE:
        print("WARNING: Audio unavailable, skipping service start.")
        health.set("audio", "down", "audio modules unavailable")
        return
    with _lock:
        if not _running:
            _running = True
            _thread = threading.Thread(target=_audio_loop, daemon=True)
            _thread.start()

def stop_audio_service():
    global _running
    with _lock:
        _running = False
