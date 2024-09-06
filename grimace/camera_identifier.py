import time
from typing import List

import cv2
import numpy as np
import torch

from grimace.camera_identifier_model import CameraIdentifierModel
from grimace.frame_quality_model import FrameQualityModel
from grimace.preprocessing.image import crop_image_to_square, average_channels


class CameraIdentifier:
    def __init__(self, camera_identifier_model: CameraIdentifierModel):
        self.camera_identifier_model = camera_identifier_model

    def preprocess(self, frame: np.ndarray):
        frame = crop_image_to_square(frame)
        frame = cv2.resize(frame, (64, 64), interpolation=cv2.INTER_LINEAR)
        if frame.ndim == 2:
            frame = frame[:, :, np.newaxis]
        elif frame.shape[2] > 1:
            frame = average_channels(frame)
        frame = frame.astype(np.float32)
        frame /= 255.0
        frame = frame.transpose(2, 0, 1)
        frame = torch.tensor(frame)
        frame = (frame - 0.6901) / 0.1750
        return frame

    def score(self, frame: np.ndarray) -> float:
        frame = self.preprocess(frame)
        output = self.camera_identifier_model(frame.unsqueeze(0))
        return output.squeeze(dim=1).detach().cpu().item()

    def score_batch(self, frames: List[np.ndarray]) -> np.ndarray:
        frames = torch.stack([self.preprocess(frame) for frame in frames])
        return self.camera_identifier_model(frames).squeeze(dim=1).detach().cpu().numpy()
