import cv2
import time
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
        self.frame_time = 1.0 / max_fps
        self.cap = cv2.VideoCapture(source)

        if not self.cap.isOpened():
            raise ValueError(f"Unable to open video source: {source}")

        # Try to get source dimensions
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

    def read_frames(self) -> Generator[Tuple[bool, Optional[cv2.typing.MatLike]], None, None]:
        """
        Yield frames from the camera/video while maintaining max_fps bounds.
        """
        last_frame_time = time.time()

        while True:
            ret, frame = self.cap.read()
            if not ret:
                # Video ended or camera disconnected
                yield False, None
                break

            # FPS throttling
            current_time = time.time()
            elapsed = current_time - last_frame_time
            if elapsed < self.frame_time:
                time.sleep(self.frame_time - elapsed)

            last_frame_time = time.time()
            yield True, frame

    def release(self):
        """Release the camera resource."""
        self.cap.release()
