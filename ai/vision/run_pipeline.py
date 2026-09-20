import argparse
import time
import cv2
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from camera import CameraStream
from tracker import PersonTracker
from fall_detector import FallDetector
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

    try:
        for ret, frame in stream.read_frames():
            if not ret or frame is None:
                print("\n[*] End of video stream.")
                break

            current_time = time.time()
            elapsed = current_time - last_frame_time
            if elapsed > 0:
                current_fps = (alpha * (1.0 / elapsed)) + ((1 - alpha) * current_fps)
            last_frame_time = current_time

            persons, latency = tracker.process(frame)
            for p in persons:
                fall.update(p, tracker.track_history(p.get("track_id", -1)))
            fall.prune(tracker.history.keys())

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
        print("[*] Pipeline shutdown complete.")


if __name__ == "__main__":
    main()
