"""Keypoint geometry helpers shared by the tracker and the fall detector.

Kept separate from tracker.py so the fall detector can use them without
pulling in torch, ultralytics, and the YOLO model weights.
"""
import math


def kp_center(kp, idxs, min_conf):
    """Mean (x, y) of the listed COCO keypoints, ignoring low-confidence ones.

    Returns None when no listed joint is confident enough to trust.
    """
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
    sh = kp_center(kp, [5, 6], min_conf)
    hip = kp_center(kp, [11, 12], min_conf)
    if sh is None or hip is None:
        return None
    dx = hip[0] - sh[0]
    dy = hip[1] - sh[1]
    if abs(dy) < 1e-6 and abs(dx) < 1e-6:
        return None
    return math.degrees(math.atan2(abs(dx), abs(dy)))


def head_ankle_span(kp, min_conf):
    """Vertical head-to-ankle distance in pixels, or None if untrustworthy.

    A standing person's head and ankles span nearly their full bounding-box
    height; a lying person's span collapses. Unlike bbox aspect, this
    separates "lying down" from "crouching", because a kneeling person still
    spans most of their height.
    """
    head = kp_center(kp, [0], min_conf)
    ankle = kp_center(kp, [15, 16], min_conf)
    if head is None or ankle is None:
        return None
    return abs(ankle[1] - head[1])


def boxes_overlap(a, b, iou_thresh: float = 0.3) -> bool:
    """True when two [x1, y1, x2, y2] boxes overlap above the IoU threshold."""
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
        return False
    inter = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
    area_a = max(1.0, (ax2 - ax1) * (ay2 - ay1))
    area_b = max(1.0, (bx2 - bx1) * (by2 - by1))
    return inter / (area_a + area_b - inter) > iou_thresh
