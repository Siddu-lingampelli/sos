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
from pose_geometry import boxes_overlap, kp_center, torso_angle_deg

try:
    import cv2
    cv2.setNumThreads(1)
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
except Exception:
    pass


# Geometry helpers now live in pose_geometry.py so the fall detector can share
# them without importing torch/ultralytics. The private aliases keep existing
# `_kp_center(...)` call sites in this module working.
_kp_center = kp_center


class PersonTracker:
    def __init__(self, model_path="yolo11n-pose.pt", cfg: FallConfig = DEFAULT):
        self.model = YOLO(model_path)
        self.cfg = cfg
        self.history: dict[int, deque] = defaultdict(lambda: deque(maxlen=cfg.HISTORY_LEN))
        self.last_seen: dict[int, float] = {}
        self._untracked_seq = -1  # unique temp IDs for detections without ByteTrack ID
        self._temp_tracks: dict[tuple[int, int], int] = {}
        self._temp_ttl: dict[int, float] = {}

    def process(self, frame: np.ndarray):
        t0 = time.time()
        h, w = frame.shape[:2]
        if not h or not w:
            return [], time.time() - t0  # degenerate frame — skip, don't divide by zero
        # Pre-shrink huge frames (phone 1080p) — YOLO letterbox cost dominates on CPU
        scale = 1.0
        frame_in = frame
        if max(h, w) > self.cfg.INFER_WIDTH:
            scale = self.cfg.INFER_WIDTH / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            frame_in = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
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

            # First pass: collect geometry for every detection, and note which
            # tracks ByteTrack already claimed. Rescue must never hand an ID to
            # a detection that sits on top of an already-matched person, or the
            # same human ends up with two live tracks and duplicated fall
            # state.
            raw = []
            claimed: set[int] = set()
            for i in range(len(boxes)):
                try:
                    box = boxes[i].xyxy[0].cpu().numpy().tolist()
                    conf = float(boxes[i].conf[0].cpu().numpy())
                    scale_inv = 1.0 / scale
                    x1, y1, x2, y2 = [c * scale_inv for c in box] if scale != 1.0 else box
                    bw, bh = max(1.0, x2 - x1), max(1.0, y2 - y1)
                    raw.append({
                        "box": [x1, y1, x2, y2], "confidence": conf,
                        "bw": bw, "bh": bh,
                        "cx": (x1 + x2) / 2 / w, "cy": (y1 + y2) / 2 / h,
                    })
                    if ids[i] is not None:
                        claimed.add(int(ids[i]))
                except (IndexError, AttributeError):
                    raw.append(None)

            rescued: set[int] = set()
            temp_used_this_frame: set[int] = set()

            for i in range(len(boxes)):
                geo = raw[i]
                if geo is None:
                    continue
                try:
                    x1, y1, x2, y2 = geo["box"]
                    bw, bh = geo["bw"], geo["bh"]
                    cx_raw, cy_raw = geo["cx"], geo["cy"]
                    conf = geo["confidence"]

                    if ids[i] is not None:
                        tid = int(ids[i])
                    else:
                        # SPATIAL RESURRECTION: ByteTrack often loses IDs when
                        # people fall because their shape changes drastically.
                        # We rescue the ID by finding the closest recent track.
                        # The eligibility window matches the 5 s history prune
                        # below: a track occluded for 2-5 s still exists and
                        # must still be rescuable, or a fall through a brief
                        # occlusion resets its state and is missed.
                        best_tid = None
                        best_dist = 0.2  # Maximum normalized distance to rescue
                        for past_tid, hist in self.history.items():
                            if not hist or (now - self.last_seen.get(past_tid, 0)) > 5.0:
                                continue
                            # Don't steal an ID ByteTrack already assigned this
                            # frame, and don't hand the same ID to two
                            # untracked detections in one frame.
                            if past_tid in claimed or past_tid in rescued:
                                continue
                            last_cx, last_cy = hist[-1].get("cx", cx_raw), hist[-1].get("cy", cy_raw)
                            # Reject if the past track's last box overlaps this
                            # detection: that means the other person is standing
                            # right there, not that this detection is a dropped
                            # version of that person.
                            lbox = hist[-1].get("box")
                            if lbox and boxes_overlap(lbox, [x1, y1, x2, y2]):
                                continue
                            import math
                            dist = math.hypot(cx_raw - last_cx, cy_raw - last_cy)
                            if dist < best_dist:
                                best_dist = dist
                                best_tid = past_tid

                        if best_tid is not None:
                            tid = best_tid
                            rescued.add(tid)
                        else:
                            # Keep a stable negative ID per spatial position for a
                            # short while so a person ByteTrack never manages to
                            # track at all still accumulates history instead of
                            # resetting their fall state every frame.
                            tid = self._temp_id_for(cx_raw, cy_raw, now, skip=temp_used_this_frame)
                            rescued.add(tid)
                        temp_used_this_frame.add(tid)

                    kp = kps.data[i].cpu().numpy().tolist() if kps is not None and len(kps.data) > i else []
                    if scale != 1.0:
                        # Map coords back to the original full-size frame using numpy for speed
                        import numpy as _np
                        if kp:
                            kp_np = _np.array(kp)
                            kp_np[:, :2] *= scale_inv
                            kp = kp_np.tolist()

                except (IndexError, AttributeError):
                    continue

                hip = _kp_center(kp, [11, 12], self.cfg.KP_CONF)
                ang = torso_angle_deg(kp, self.cfg.KP_CONF)

                entry = {
                    "box": [x1, y1, x2, y2], "confidence": conf, "keypoints": kp,
                    "track_id": tid, "cx": cx_raw, "cy": cy_raw,
                    "hip_y": (hip[1] / h) if hip and h else None,
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

    def _temp_id_for(self, cx: float, cy: float, now: float, skip: set | None = None) -> int:
        """Return a stable temp ID for an untracked detection.

        ByteTrack's tracker may never assign an ID to a person (e.g. a heavy
        occlusion at entry). Without this, a fresh negative ID is minted every
        frame and the fall detector resets that person every frame, so a fall
        by a person who is never successfully tracked becomes undetectable.

        A detection within TEMP_CELL of a recent temp track reuses its ID;
        stale cells are expired after TEMP_TTL. `skip` holds temp IDs already
        handed out earlier in the same frame, so two people standing in
        adjacent cells never merge into one track.
        """
        # Snap to a coarse grid so a jittery centroid maps to the same cell.
        key = (int(cx * 10), int(cy * 10))
        # First expire stale temp tracks
        expired_keys = []
        for (kx, ky), tid in list(self._temp_tracks.items()):
            if now - self._temp_ttl.get(tid, 0) > self._TEMP_TTL_SEC:
                expired_keys.append((kx, ky))
        for ek in expired_keys:
            tid = self._temp_tracks.pop(ek, None)
            if tid is not None:
                self._temp_ttl.pop(tid, None)

        # Nearest live cell within the neighbourhood wins (first-match could
        # merge two different people when both sit within ±1 cell).
        best_tid = None
        best_dist = 2  # cells; neighbourhood radius is 1, so 2 always loses
        best_key = None
        skip = skip or set()
        for (kx, ky), tid in self._temp_tracks.items():
            if tid in skip:
                continue  # already claimed by another detection this frame
            d = max(abs(kx - key[0]), abs(ky - key[1]))
            if d <= 1 and d < best_dist:
                best_dist = d
                best_tid = tid
                best_key = (kx, ky)
        if best_tid is not None:
            self._temp_ttl[best_tid] = now
            if best_key != key:
                # Move the ID to the current cell and drop the stale key so
                # the grid map cannot accumulate dead entries for one track.
                self._temp_tracks.pop(best_key, None)
                self._temp_tracks[key] = best_tid
            return best_tid

        tid = self._untracked_seq
        self._untracked_seq -= 1
        self._temp_tracks[key] = tid
        self._temp_ttl[tid] = now
        return tid

    _TEMP_TTL_SEC = 1.5

    def track_history(self, tid: int):
        return list(self.history.get(tid, []))
