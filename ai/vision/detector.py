import time
import numpy as np
import warnings
from ultralytics import YOLO

# Suppress ultralytics excessive logging if desired
warnings.filterwarnings("ignore", category=UserWarning)

class PoseDetector:
    def __init__(self, model_path: str = "yolo11n-pose.pt"):
        """
        Initialize the YOLO Pose model.
        """
        self.model = YOLO(model_path)
        
    def process_frame(self, frame: np.ndarray) -> tuple[list, float]:
        """
        Run inference on a single frame.
        :param frame: numpy array from OpenCV.
        :return: (list of persons, latency_in_seconds)
        """
        start_time = time.time()
        
        # verbose=False prevents console logging every frame
        # conf=0.15 makes the AI highly sensitive to compressed IP camera feeds
        results = self.model(frame, verbose=False, conf=0.15)
        latency = time.time() - start_time
        
        persons = []
        
        for result in results:
            boxes = result.boxes
            keypoints = result.keypoints
            
            # Keypoints might exist even if no boxes are detected, check length
            if boxes is not None and keypoints is not None and len(boxes) > 0:
                for i in range(len(boxes)):
                    try:
                        box = boxes[i].xyxy[0].cpu().numpy().tolist()
                        conf = float(boxes[i].conf[0].cpu().numpy())
                        
                        # keypoints.data has shape (num_persons, 17, 3), safe extraction
                        kp = keypoints.data[i].cpu().numpy().tolist()
                        
                        persons.append({
                            "box": box,
                            "confidence": conf,
                            "keypoints": kp
                        })
                    except (IndexError, AttributeError):
                        # Catch potential format deviations safely out of loop
                        continue
                    
        return persons, latency
