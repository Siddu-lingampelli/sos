import cv2
import time
import numpy as np
from typing import Generator, Tuple, Optional

class CameraStream:
    def __init__(self, source: str | int = 0, max_fps: int = 30):
        """
        Initialize video capture.
        :param source: 0 for webcam, or a path to a video file.
        :param max_fps: Target FPS to prevent processing unneeded frames.
        """
        self.source = source
        self.max_fps = max_fps
        self.frame_time = 1.0 / max_fps if max_fps > 0 else 0
        
        # Ensure string sources that are pure digits drop down to integer to connect correctly
        if isinstance(self.source, str) and self.source.isdigit():
            self.source = int(self.source)
            
        self.cap = cv2.VideoCapture(self.source)

        if not self.cap.isOpened():
            print(f"Warning: Unable to open video source: {source}")

        # Basic dimensions
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        # Identify if we're dealing with a live cam
        self.is_live = isinstance(self.source, int)

    def read_frames(self) -> Generator[Tuple[bool, Optional[np.ndarray]], None, None]:
        """
        Yield frames from the camera/video.
        """
        last_frame_time = time.time()

        while True:
            ret, frame = self.cap.read()
            if not ret:
                yield False, None
                break
                
            current_time = time.time()
            elapsed = current_time - last_frame_time
            
            # Throttle if processing recorded video so it doesn't run at 1000 FPS
            if not self.is_live and self.max_fps > 0:
                if elapsed < self.frame_time:
                    time.sleep(self.frame_time - elapsed)
                    
            last_frame_time = time.time()
            yield True, frame

    def release(self):
        """Release the camera resource."""
        if self.cap:
            self.cap.release()
