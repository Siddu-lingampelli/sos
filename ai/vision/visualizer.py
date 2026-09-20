import cv2
import numpy as np

class Visualizer:
    def __init__(self):
        # Setup standard COCO 17 keypoint connections for plotting the skeleton
        self.skeleton = [
            (15, 13), (13, 11), (16, 14), (14, 12), (11, 12), (5, 11), 
            (6, 12), (5, 6), (5, 7), (6, 8), (7, 9), (8, 10), (1, 2), 
            (0, 1), (0, 2), (1, 3), (2, 4), (3, 5), (4, 6)
        ]
        self.keypoint_colors = (0, 255, 0)
        self.bone_colors = (255, 0, 0)

    STATE_COLORS = {
        "NORMAL": (0, 200, 0),
        "POSSIBLE_FALL": (0, 165, 255),
        "FALL_CONFIRMED": (0, 0, 255),
        "RECOVERED": (255, 0, 0),
    }

    def draw(self, frame: np.ndarray, persons: list, fps: float, latency: float) -> np.ndarray:
        """
        Draws bounding boxes, skeletons, and telemetry onto the frame.
        """
        out_frame = frame.copy()
        h, w = out_frame.shape[:2]
        
        # Draw detections
        for person in persons:
            # Box — color by fall state (Level 4)
            x1, y1, x2, y2 = map(int, person["box"])
            state = person.get("fall_state", "NORMAL")
            color = self.STATE_COLORS.get(state, (0, 0, 255))
            cv2.rectangle(out_frame, (x1, y1), (x2, y2), color, 2)
            tid = person.get("track_id", -1)
            ang = person.get("angle")
            ang_txt = f"{ang:.0f}d" if ang is not None else "?"
            cv2.putText(out_frame, f"ID{tid} {state} {ang_txt}", (x1, max(0, y1 - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
            # Level 5: observation / inactivity badge
            ist = person.get("inact_state", "IDLE")
            if ist == "OBSERVING":
                el = person.get("inact_elapsed", 0.0)
                cv2.putText(out_frame, f"OBSERVING {el:.0f}s", (x1, y2 + 18),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 165, 255), 2)
            elif ist == "INACTIVE":
                cv2.putText(out_frame, "INACTIVE - POSSIBLE EMERGENCY", (x1, y2 + 18),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
            
            # Keypoints & Skeleton
            keypoints = person.get("keypoints", [])
            if not keypoints:
                continue

            # Draw bones
            for link in self.skeleton:
                try:
                    pt1 = keypoints[link[0]]
                    pt2 = keypoints[link[1]]
                    
                    # Verify keypoints confidence > 0.5 if confidence exists
                    conf1 = pt1[2] if len(pt1) > 2 else 1.0
                    conf2 = pt2[2] if len(pt2) > 2 else 1.0
                    
                    if conf1 > 0.5 and conf2 > 0.5:
                        cv2.line(out_frame, 
                                 (int(pt1[0]), int(pt1[1])), 
                                 (int(pt2[0]), int(pt2[1])), 
                                 self.bone_colors, 2)
                except IndexError:
                    continue
            
            # Draw keypoints
            for pt in keypoints:
                conf = pt[2] if len(pt) > 2 else 1.0
                if conf > 0.5:
                    cv2.circle(out_frame, (int(pt[0]), int(pt[1])), 4, self.keypoint_colors, -1)

        # Draw UI Overlay (Telemetry)
        cv2.rectangle(out_frame, (0, 0), (w, 40), (0, 0, 0), -1)
        
        cv2.putText(out_frame, f"SilentSOS - L4 Track+Fall", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(out_frame, f"FPS: {fps:.1f}", (w - 250, 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(out_frame, f"Latency: {latency*1000:.1f}ms", (w - 140, 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        return out_frame
