import argparse
import time
import cv2
import os

from camera import CameraStream
from detector import PoseDetector
from visualizer import Visualizer

def main():
    parser = argparse.ArgumentParser(description="SilentSOS Level 3 Vision Pipeline")
    parser.add_argument("--source", type=str, default="0", help="Camera index (0) or video path")
    parser.add_argument("--fps", type=int, default=30, help="Target FPS")
    parser.add_argument("--output", type=str, default="", help="Path to save output video (optional)")
    parser.add_argument("--headless", action="store_true", help="Run without UI window")
    args = parser.parse_args()

    source = int(args.source) if args.source.isdigit() else args.source

    print(f"[*] Initializing vision pipeline on source: {source}")
    stream = CameraStream(source=source, max_fps=args.fps)
    detector = PoseDetector(model_path="yolo11n-pose.pt")
    visualizer = Visualizer()

    writer = None
    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        # Using 4cc string expansion which is universally safer for OpenCV
        fourcc = cv2.VideoWriter_fourcc(*'mp4v') # type: ignore
        fps = stream.fps if stream.fps > 0 else args.fps
        writer = cv2.VideoWriter(args.output, fourcc, fps, (stream.width, stream.height))
        print(f"[*] Saving output to {args.output}")

    print("[*] Starting inference loop. Press 'q' to quit.")
    
    last_frame_time = time.time()
    current_fps = 0.0
    alpha = 0.1 # EMA alpha for smoothing FPS

    try:
        for ret, frame in stream.read_frames():
            if not ret or frame is None:
                print("\n[*] End of video stream.")
                break

            # Calculate FPS via Exponential Moving Average (EMA)
            current_time = time.time()
            elapsed = current_time - last_frame_time
            if elapsed > 0:
                instant_fps = 1.0 / elapsed
                current_fps = (alpha * instant_fps) + ((1 - alpha) * current_fps)
            last_frame_time = current_time

            # Process frame
            persons, latency = detector.process_frame(frame)
            
            # Visualize
            out_frame = visualizer.draw(frame, persons, current_fps, latency)

            if writer:
                writer.write(out_frame)

            if not args.headless:
                cv2.imshow("SilentSOS - Level 3", out_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    except KeyboardInterrupt:
        print("\n[*] Interrupted by user.")
    finally:
        stream.release()
        if writer:
            writer.release()
        cv2.destroyAllWindows()
        print("[*] Pipeline shutdown complete.")

if __name__ == "__main__":
    main()
