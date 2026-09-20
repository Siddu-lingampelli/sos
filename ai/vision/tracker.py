"""ByteTrack-backed person tracker with per-track temporal history.

Uses ultralytics built-in ByteTrack (model.track persist=True) so IDs are
stable across frames — exactly what Level 4 requires:
  YOLO Pose -> Person Detection -> ByteTrack -> Persistent Person ID
"""
import os
import time
from collections import deque, defaultdict
import cv2
import numpy as np
import torch
from ultralytics import YOLO

from config import FallConfig, DEFAULT

try:
    torch.set_num_threads(max(1, os.cpu_count() or 4))
    torch.set_num_interop_threads(1)
except Exception:
    pass


def _kp_center(kp, idxs, min_conf):
    pts = []
    for i in idxs:
        if i < len(kp):
            p = kp[i]
            c = p[2] if len(p) > 2 else 1.0
            if c >= min_conf:
                pts.append((p[0], p[1]))
    if not pts:
        return None
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def torso_angle_deg(kp, min_conf=0.4):
    """Angle of shoulder->hip vector from vertical. 0=upright, 90=lying."""
    sh = _kp_center(kp, [5, 6], min_conf)
    hip = _kp_center(kp, [11, 12], min_conf)
    if sh is None or hip is None:
        return None
    dx = hip[0] - sh[0]
    dy = hip[1] - sh[1]
    if abs(dy) < 1e-6 and abs(dx) < 1e-6:
        return None
    # angle from vertical axis
    import math
    return math.degrees(math.atan2(abs(dx), abs(dy)))


class PersonTracker:
    def __init__(self, model_path="yolo11n-pose.pt", cfg: FallConfig = DEFAULT):
        self.model = YOLO(model_path)
        self.cfg = cfg
        self.history: dict[int, deque] = defaultdict(lambda: deque(maxlen=cfg.HISTORY_LEN))
        self.last_seen: dict[int, float] = {}
        self._untracked_seq = -1  # unique temp IDs for detections without ByteTrack ID

    def process(self, frame: np.ndarray):
        t0 = time.time()
        h, w = frame.shape[:2]
        # Pre-shrink huge frames (phone 1080p) — YOLO letterbox cost dominates on CPU
        scale = 1.0
        frame_in = frame
        if max(h, w) > self.cfg.INFER_WIDTH:
            scale = self.cfg.INFER_WIDTH / max(h, w)
            frame_in = cv2.resize(frame, (int(w * scale), int(h * scale)))
        results = self.model.track(
            frame_in, persist=True, verbose=False,
            conf=self.cfg.BOX_CONF, tracker="bytetrack.yaml",
            imgsz=self.cfg.IMGSZ,
        )
        latency = time.time() - t0
        persons = []
        now = time.time()

        for r in results:
            boxes = r.boxes
            kps = r.keypoints
            if boxes is None or len(boxes) == 0:
                continue
            ids = boxes.id.cpu().numpy().tolist() if boxes.id is not None else [None] * len(boxes)
            for i in range(len(boxes)):
                try:
                    box = boxes[i].xyxy[0].cpu().numpy().tolist()
                    conf = float(boxes[i].conf[0].cpu().numpy())
                    scale_inv = 1.0 / scale
                    x1, y1, x2, y2 = [c * scale_inv for c in box] if scale != 1.0 else box
                    bw, bh = max(1.0, x2 - x1), max(1.0, y2 - y1)
                    cx_raw, cy_raw = (x1 + x2) / 2 / w, (y1 + y2) / 2 / h
                    
                    if ids[i] is not None:
                        tid = int(ids[i])
                    else:
                        # SPATIAL RESURRECTION: ByteTrack often loses IDs when
                        # people fall because their shape changes drastically.
                        # We rescue the ID by finding the closest recent track.
                        best_tid = None
                        best_dist = 0.2  # Maximum normalized distance to rescue
                        for past_tid, hist in self.history.items():
                            if not hist or (now - self.last_seen.get(past_tid, 0)) > 1.5:
                                continue
                            last_cx, last_cy = hist[-1].get("cx", cx_raw), hist[-1].get("cy", cy_raw)
                            import math
                            dist = math.hypot(cx_raw - last_cx, cy_raw - last_cy)
                            if dist < best_dist:
                                best_dist = dist
                                best_tid = past_tid
                        
                        if best_tid is not None:
                            tid = best_tid
                        else:
                            tid = self._untracked_seq
                            self._untracked_seq -= 1

                    kp = kps.data[i].cpu().numpy().tolist() if kps is not None and len(kps.data) > i else []
                    if scale != 1.0:
                        # Map coords back to the original full-size frame
                        kp = [[p[0] * scale_inv, p[1] * scale_inv] + p[2:] for p in kp]
                        
                except (IndexError, AttributeError):
                    continue
                    
                hip = _kp_center(kp, [11, 12], self.cfg.KP_CONF)
                ang = torso_angle_deg(kp, self.cfg.KP_CONF)
                
                entry = {
                    "box": [x1, y1, x2, y2], "confidence": conf, "keypoints": kp,
                    "track_id": tid, "cx": cx_raw, "cy": cy_raw,
                    "hip_y": (hip[1] / h) if hip else None,
                    "angle": ang, "aspect": bw / bh, "t": now,
                    "fw": w, "fh": h,
                }
                self.history[tid].append(entry)
                self.last_seen[tid] = now
                persons.append(entry)

        # prune tracks unseen for >5s
        stale = [tid for tid, t in self.last_seen.items() if now - t > 5.0]
        for tid in stale:
            self.history.pop(tid, None)
            self.last_seen.pop(tid, None)

        return persons, latency

    def track_history(self, tid: int):
        return list(self.history.get(tid, []))
