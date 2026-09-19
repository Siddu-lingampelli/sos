import time
import numpy as np
from ultralytics import YOLO

class PoseDetector:
    def __init__(self, model_path: str = "yolo11n-pose.pt"):
        """
        Initialize the YOLO Pose model.
        YOLO11n-pose is fast and accurate enough for real-time edge processing.
        """
        self.model = YOLO(model_path)
        
    def process_frame(self, frame: np.ndarray) -> tuple[list, float]:
        """
        Run inference on a single frame.
        :param frame: standard BGR numpy array from OpenCV.
        :return: (list of persons, latency_in_seconds)
        """
        start_time = time.time()
        
        # YOLO inference (verbose=False to avoid console spam per frame)
        results = self.model(frame, verbose=False)
        latency = time.time() - start_time
        
        persons = []
        
        for result in results:
            boxes = result.boxes
            keypoints = result.keypoints
            
            if boxes is not None and keypoints is not None:
                for i in range(len(boxes)):
                    # Get box coordinates [x1, y1, x2, y2]
                    box = boxes[i].xyxy[0].cpu().numpy().tolist()
                    conf = float(boxes[i].conf[0].cpu().numpy())
                    
                    # Keypoints shape: (17, 3) -> [x, y, confidence] for the i-th person
                    try:
                        kp = keypoints[i].data[0].cpu().numpy().tolist()
                    except IndexError:
                        continue
                    
                    persons.append({
                        "box": box,
                        "confidence": conf,
                        "keypoints": kp
                    })
                    
        return persons, latency
