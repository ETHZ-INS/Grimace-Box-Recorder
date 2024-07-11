from typing import List

import numpy as np
import torch
from ultralytics import YOLO


def best_box_to_array(result) -> np.ndarray:
    result = result.cpu().numpy()
    confidences = result.boxes.conf
    coordinates = result.boxes.xyxyn

    if len(confidences) == 0 or len(coordinates) == 0:
        return np.zeros(5, dtype=np.float32)

    best_box_index = np.argmax(confidences)
    best_box_confidence = confidences[best_box_index]
    best_box = coordinates[best_box_index]

    return np.concatenate([[best_box_confidence], best_box], axis=0)


class FrameCropperModel:
    def __init__(self, model: YOLO, device: str = "cuda"):
        self.model = model
        self.device = torch.device(device)

    def get_bounding_box(self, frame: np.ndarray) -> np.ndarray:
        results = self.model(frame, verbose=False, device=self.device)
        return best_box_to_array(results[0])

    def get_bounding_boxes(self, frames: List[np.ndarray]) -> np.ndarray:
        results = self.model(frames, verbose=False, device=self.device)
        return np.stack([best_box_to_array(result) for result in results])
