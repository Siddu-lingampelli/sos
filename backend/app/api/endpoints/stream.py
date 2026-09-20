import cv2
import time
import sys
import os
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ...core.config import settings

# Inject the ai/ directory to Python path so we can import the vision modules
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
    from visualizer import Visualizer
    from config import DEFAULT
    AI_AVAILABLE = True
except ImportError as e:
    AI_AVAILABLE = False
    print(f"WARNING: Could not import AI vision modules: {e}")

router = APIRouter()

def generate_frames(source: str):
    if not AI_AVAILABLE:
        yield b'AI Modules missing'
        return

    # Attempt to convert source to int if it's a digit (for usb webcams)
    vid_source = int(source) if source.isdigit() else source

    stream = CameraStream(source=vid_source, max_fps=15) # 15 FPS max for web streaming performance
    tracker = PersonTracker(model_path=os.path.join(vision_path, "yolo11n-pose.pt"), cfg=DEFAULT)
    fall = FallDetector(cfg=DEFAULT)
    visualizer = Visualizer()
    
    last_frame_time = time.time()
    current_fps = 0.0
    alpha = 0.1

    try:
        for ret, frame in stream.read_frames():
            if not ret or frame is None:
                break
            
            # FPS Calculation
            current_time = time.time()
            elapsed = current_time - last_frame_time
            if elapsed > 0:
                current_fps = (alpha * (1.0 / elapsed)) + ((1 - alpha) * current_fps)
            last_frame_time = current_time

            # Detection + tracking + fall state
            persons, latency = tracker.process(frame)
            for p in persons:
                fall.update(p, tracker.track_history(p.get("track_id", -1)))
            
            # Visualizer
            out_frame = visualizer.draw(frame, persons, current_fps, latency)
            
            # Encode frame to JPEG
            ret, buffer = cv2.imencode('.jpg', out_frame)
            if not ret:
                continue
                
            frame_bytes = buffer.tobytes()
            # Yield in multipart MJPEG format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    finally:
        stream.release()

@router.get("/video")
def video_feed(source: str = "0"):
    """
    Returns an MJPEG stream of the AI processed camera feed.
    Pass ?source=http://... or ?source=0 
    """
    return StreamingResponse(
        generate_frames(source), 
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
