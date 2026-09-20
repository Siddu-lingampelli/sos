import argparse
import time
import cv2
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "engine")))

from camera import CameraStream
from tracker import PersonTracker
from fall_detector import FallDetector
from inactivity import InactivityMonitor
from fusion import EmergencyEngine
from visualizer import Visualizer
from config import DEFAULT


def main():
    parser = argparse.ArgumentParser(description="SilentSOS Level 4 Track + Fall Pipeline")
    parser.add_argument("--source", type=str, default="0", help="Camera index (0) or video path")
    parser.add_argument("--fps", type=int, default=30, help="Target FPS")
    parser.add_argument("--output", type=str, default="", help="Path to save output video (optional)")
    parser.add_argument("--headless", action="store_true", help="Run without UI window")
    args = parser.parse_args()

    source = int(args.source) if args.source.isdigit() else args.source

    print(f"[*] Initializing L4 pipeline on source: {source}")
    stream = CameraStream(source=source, max_fps=args.fps)
    tracker = PersonTracker(model_path="yolo11n-pose.pt", cfg=DEFAULT)
    fall = FallDetector(cfg=DEFAULT)
    inact = InactivityMonitor(cfg=DEFAULT)
    engine = EmergencyEngine()
    visualizer = Visualizer()

    writer = None
    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # type: ignore
        fps = stream.fps if stream.fps > 0 else args.fps
        writer = cv2.VideoWriter(args.output, fourcc, fps, (stream.width, stream.height))
        print(f"[*] Saving output to {args.output}")

    print("[*] Starting inference loop. Press 'q' to quit.")

    last_frame_time = time.time()
    current_fps = 0.0
    alpha = 0.1
    stride = max(1, DEFAULT.DETECT_STRIDE)
    last_persons: list = []
    last_latency = 0.0
    n = 0

    try:
        for ret, frame in stream.read_frames():
            if not ret or frame is None:
                print("\n[*] End of video stream.")
                break
            n += 1

            current_time = time.time()
            elapsed = current_time - last_frame_time
            if elapsed > 0:
                current_fps = (alpha * (1.0 / elapsed)) + ((1 - alpha) * current_fps)
            last_frame_time = current_time

            if n % stride == 1:
                persons, last_latency = tracker.process(frame)
                for p in persons:
                    tid = p.get("track_id", -1)
                    hist = tracker.track_history(tid)
                    fall.update(p, hist)
                    inact.update(tid, hist, p.get("fall_state", "NORMAL"))
                    p.update(inact.info(tid, hist))
                    score, estate, _ev = engine.update(tid, p)
                    p["eng_score"] = score
                    p["eng_state"] = estate
                fall.prune(tracker.history.keys())
                inact.prune(tracker.history.keys())
                engine.prune(tracker.history.keys())
                while True:
                    inc = engine.pop_incident()
                    if inc is None:
                        break
                    print(f"   🚨 POSSIBLE EMERGENCY track={inc['track_id']} "
                          f"conf={inc['confidence']:.0%} ev={inc['event_type']}")
                last_persons = persons
            persons, latency = last_persons, last_latency

            out_frame = visualizer.draw(frame, persons, current_fps, latency)

            if writer:
                writer.write(out_frame)

            if not args.headless:
                cv2.imshow("SilentSOS - Level 4", out_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    except KeyboardInterrupt:
        print("\n[*] Interrupted by user.")
    finally:
        stream.release()
        if writer:
            writer.release()
        cv2.destroyAllWindows()
        print(f"[*] Fall events this run: {len(fall.events)}")
        for e in list(fall.events)[-10:]:
            print("   ", e)
        print(f"[*] Inactivity events this run: {len(inact.events)}")
        for e in list(inact.events)[-10:]:
            print("   ", e)
        print("[*] Pipeline shutdown complete.")


if __name__ == "__main__":
    main()
