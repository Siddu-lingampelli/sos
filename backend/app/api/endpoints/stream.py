"""MJPEG video stream with shared per-source inference (singleton).

Fixes the Level-4 audit gap: previously every HTTP client created its own
CameraStream + YOLO model. Now one background thread per camera source feeds
all viewers from a shared latest-JPEG buffer.
"""
import cv2
import time
import sys
import os
import threading
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

ai_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../ai"))
if ai_path not in sys.path:
    sys.path.append(ai_path)
vision_path = os.path.join(ai_path, "vision")
if vision_path not in sys.path:
    sys.path.append(vision_path)

try:
    from camera import CameraStream
    from tracker import PersonTracker
    from fall_detector import FallDetector
    from inactivity import InactivityMonitor
    from visualizer import Visualizer
    from config import DEFAULT
    AI_AVAILABLE = True
except ImportError as e:
    AI_AVAILABLE = False
    print(f"WARNING: Could not import AI vision modules: {e}")

router = APIRouter()

_lock = threading.Lock()
_states: dict[str, dict] = {}


def _inference_loop(source_key: str, vid_source):
    st = _states[source_key]
    stream = CameraStream(source=vid_source, max_fps=15)
    tracker = PersonTracker(model_path=os.path.join(vision_path, "yolo11n-pose.pt"), cfg=DEFAULT)
    fall = FallDetector(cfg=DEFAULT)
    inact = InactivityMonitor(cfg=DEFAULT)
    viz = Visualizer()
    last = time.time()
    fps = 0.0
    stride = max(1, DEFAULT.DETECT_STRIDE)
    last_persons: list = []
    last_latency = 0.0
    n = 0
    try:
        for ret, frame in stream.read_frames():
            if not ret or frame is None or st.get("stop"):
                break
            n += 1
            now = time.time()
            dt = now - last
            if dt > 0:
                fps = 0.1 * (1.0 / dt) + 0.9 * fps
            last = now
            if n % stride == 1:
                # Heavy YOLO inference only on stride frames
                persons, last_latency = tracker.process(frame)
                for p in persons:
                    tid = p.get("track_id", -1)
                    hist = tracker.track_history(tid)
                    fall.update(p, hist)
                    inact.update(tid, hist, p.get("fall_state", "NORMAL"))
                    p.update(inact.info(tid, hist))
                fall.prune(tracker.history.keys())
                inact.prune(tracker.history.keys())
                last_persons = persons
            out = viz.draw(frame, last_persons, fps, last_latency)
            h, w = out.shape[:2]
            if w > DEFAULT.STREAM_WIDTH:
                scale = DEFAULT.STREAM_WIDTH / w
                out = cv2.resize(out, (DEFAULT.STREAM_WIDTH, int(h * scale)))
            ok, buf = cv2.imencode('.jpg', out, [cv2.IMWRITE_JPEG_QUALITY, DEFAULT.JPEG_QUALITY])
            if ok:
                with _lock:
                    st["jpg"] = buf.tobytes()
    finally:
        stream.release()
        with _lock:
            _states.pop(source_key, None)


def _ensure_source(source: str):
    with _lock:
        if source in _states:
            return
        vid_source = int(source) if source.isdigit() else source
        st: dict = {"jpg": None, "stop": False}
        _states[source] = st
        t = threading.Thread(target=_inference_loop, args=(source, vid_source), daemon=True)
        st["thread"] = t
        t.start()


def generate_frames(source: str):
    if not AI_AVAILABLE:
        return
    _ensure_source(source)
    served = False
    idle = 0
    while True:
        with _lock:
            st = _states.get(source)
            jpg = st["jpg"] if st else None
        if jpg is not None:
            served = True
            idle = 0
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpg + b'\r\n')
        else:
            idle += 1
        if st is None and (served or idle > 15 * 10):
            # Camera thread died (disconnect) — close connection so the
            # browser <img onError> fires instead of hanging on last frame
            break
        time.sleep(1 / 15)


@router.get("/video")
def video_feed(source: str = ""):
    """MJPEG stream. Pass ?source=http://phone-ip:8080/video. Laptop webcam (0) not used."""
    if not AI_AVAILABLE:
        from fastapi.responses import JSONResponse
        return JSONResponse({"error": "AI modules missing"}, status_code=503)
    if not source:
        from fastapi.responses import JSONResponse
        return JSONResponse({"error": "No camera source — pass ?source=http://phone-ip:8080/video"}, status_code=400)
    return StreamingResponse(generate_frames(source), media_type="multipart/x-mixed-replace; boundary=frame")
