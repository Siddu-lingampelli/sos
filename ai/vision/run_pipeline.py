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

    # Determine numeric or string source
    source = int(args.source) if args.source.isdigit() else args.source

    print(f"[*] Initializing vision pipeline on source: {source}")
    stream = CameraStream(source=source, max_fps=args.fps)
    detector = PoseDetector(model_path="yolo11n-pose.pt")
    visualizer = Visualizer()

    # Video Writer setup if output is requested
    writer = None
    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v') # type: ignore
        fps = stream.fps if stream.fps > 0 else args.fps
        writer = cv2.VideoWriter(args.output, fourcc, fps, (stream.width, stream.height))
        print(f"[*] Saving output to {args.output}")

    print("[*] Starting inference loop. Press 'q' to quit.")
    
    frame_count = 0
    start_time = time.time()
    current_fps = 0.0

    try:
        for ret, frame in stream.read_frames():
            if not ret or frame is None:
                print("\n[*] End of video stream.")
                break

            # Process frame
            persons, latency = detector.process_frame(frame)
            
            # FPS Calculation
            frame_count += 1
            if frame_count % 10 == 0:
                elapsed = time.time() - start_time
                current_fps = 10 / elapsed
                start_time = time.time()

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
