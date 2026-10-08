import cv2
import time
import numpy as np
from typing import Generator, Tuple, Optional

class CameraStream:
    # Consecutive failed reads tolerated on a live source before we give up.
    # A single dropped frame is routine (USB hiccup, Wi-Fi jitter); treating it
    # as fatal killed the whole inference thread on a single glitch.
    MAX_LIVE_READ_FAILURES = 10
    # Reconnect cycles before a live source is declared dead: callers get
    # (False, None) and stop instead of spinning at 20 Hz forever on a camera
    # that will never come back.
    MAX_LIVE_RECONNECTS = 5
    # Seconds to wait before re-opening a dead live capture.
    RECONNECT_DELAY_SEC = 2.0
    # A live cap.read() that blocks longer than this is treated as a stall
    # (dead RTSP socket). Used by read_with_timeout(), not read_frames().
    READ_TIMEOUT_SEC = 10.0

    def watch_for_stall(self, last_frame_at: list, stop: list) -> None:
        """Daemon helper: mark stop[0] when no frame arrived for READ_TIMEOUT.

        Run in a side thread next to a blocking read_frames() loop. The loop
        writes time.time() into last_frame_at[0] per frame; if the capture
        wedges inside cap.read(), this fires and the loop can break out and
        reconnect instead of hanging the inference thread forever.
        """
        import threading as _t
        def _watch():
            while not stop[0]:
                _t.Event().wait(2.0)
                if stop[0]:
                    return
                if time.time() - last_frame_at[0] > self.READ_TIMEOUT_SEC:
                    stop[0] = True
                    return
        _t.Thread(target=_watch, daemon=True).start()

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

        # Identify if we're dealing with a live cam or a pre-recorded file format
        if isinstance(self.source, int):
            self.is_live = True
        elif isinstance(self.source, str) and self.source.lower().startswith(('rtsp://', 'http://', 'https://')):
            self.is_live = True
        else:
            self.is_live = False

        self._open()

    def _open(self):
        """(Re)open the capture and refresh the cached stream properties."""
        self.cap = cv2.VideoCapture(self.source)

        if not self.cap.isOpened():
            print(f"Warning: Unable to open video source: {self.source}")

        # Basic dimensions
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

        if self.is_live:
            # Drop stale buffered frames so live inference never lags behind realtime
            try:
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            except Exception:
                pass

    def read_frames(self) -> Generator[Tuple[bool, Optional[np.ndarray]], None, None]:
        """
        Yield frames from the camera/video.

        A recorded file ends the stream when it runs out. A live source is
        reconnected after a run of failed reads, so a camera that drops out
        comes back on its own instead of killing the inference thread.

        A hard stall (cap.read() blocking forever on a dead RTSP socket)
        cannot be detected from inside this loop, so read_with_timeout()
        exists for callers that need a guarantee: it runs the blocking read
        on a daemon thread and reports failure after READ_TIMEOUT_SEC.
        """
        last_frame_time = time.time()
        failures = 0
        reconnects = 0

        while True:
            ret, frame = self.cap.read()
            if not ret:
                # End of a file is final; a live dropout is worth retrying.
                if not self.is_live:
                    yield False, None
                    break

                failures += 1
                if failures > self.MAX_LIVE_READ_FAILURES:
                    reconnects += 1
                    if reconnects > self.MAX_LIVE_RECONNECTS:
                        print(f"[camera] {self.source} dead after "
                              f"{reconnects} reconnects — giving up")
                        try:
                            self.cap.release()
                        except Exception:
                            pass
                        yield False, None
                        break
                    print(f"[camera] {self.source} unreadable after "
                          f"{failures} attempts, reconnecting")
                    self.cap.release()
                    time.sleep(self.RECONNECT_DELAY_SEC)
                    self._open()
                    failures = 0
                time.sleep(0.05)
                continue

            failures = 0
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
