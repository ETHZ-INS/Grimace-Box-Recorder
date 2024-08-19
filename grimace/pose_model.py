import dataclasses
from dataclasses import dataclass
from typing import List

import cv2
import numpy as np
import torch
from ultralytics import YOLO


@dataclass(slots=True)
class Point:
    conf: float
    x: float
    y: float


@dataclass(slots=True)
class Instance:
    conf: float
    box: np.ndarray
    pose: List[Point] = dataclasses.field(default_factory=list)


def get_best_instance(result) -> Instance | None:
    result = result.cpu().numpy()
    confidences = result.boxes.conf

    if len(confidences) == 0:
        return None

    best_index = np.argmax(confidences)
    box_conf = result.boxes.conf[best_index]
    box_coords = result.boxes.xyxyn[best_index]

    if result.keypoints is None:
        pose = []
    else:
        pose_confs = result.keypoints.conf[best_index]
        pose_coords = result.keypoints.xyn[best_index]
        pose = [Point(conf, coords[0], coords[1]) for conf, coords in zip(pose_confs, pose_coords)]

    return Instance(box_conf, box_coords, pose)


class PoseModel:
    def __init__(self, model: YOLO, device: str = "cuda"):
        self.model = model
        self.device = torch.device(device)

    def get_instance(self, frame: np.ndarray) -> Instance | None:
        results = self.model(frame, verbose=False, device=self.device)
        return get_best_instance(results[0])

    def get_instances(self, frames: List[np.ndarray]) -> List[Instance | None]:
        results = self.model(frames, verbose=False, device=self.device)
        return [get_best_instance(result) for result in results]
