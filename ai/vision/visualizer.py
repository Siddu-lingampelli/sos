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

    def draw(self, frame: np.ndarray, persons: list, fps: float, latency: float) -> np.ndarray:
        """
        Draws bounding boxes, skeletons, and telemetry onto the frame.
        """
        h, w = frame.shape[:2]
        
        # Draw detections
        for person in persons:
            # Box
            x1, y1, x2, y2 = map(int, person["box"])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            
            # Keypoints & Skeleton
            keypoints = person.get("keypoints", [])
            if not keypoints:
                continue

            # Draw bones
            for link in self.skeleton:
                pt1 = keypoints[link[0]]
                pt2 = keypoints[link[1]]
                
                # Check confidence threshold (index 2 is confidence)
                if pt1[2] > 0.5 and pt2[2] > 0.5:
                    cv2.line(frame, 
                             (int(pt1[0]), int(pt1[1])), 
                             (int(pt2[0]), int(pt2[1])), 
                             self.bone_colors, 2)
            
            # Draw keypoints
            for pt in keypoints:
                if pt[2] > 0.5:
                    cv2.circle(frame, (int(pt[0]), int(pt[1])), 4, self.keypoint_colors, -1)

        # Draw UI Overlay (Telemetry)
        # Background bar
        cv2.rectangle(frame, (0, 0), (w, 40), (0, 0, 0), -1)
        
        # Telemetry text
        cv2.putText(frame, f"SilentSOS - Level 3 Vision Pipeline", (10, 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"FPS: {fps:.1f}", (w - 250, 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Latency: {latency*1000:.1f}ms", (w - 140, 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        return frame
