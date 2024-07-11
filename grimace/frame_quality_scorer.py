import time
from typing import List

import cv2
import numpy as np
import torch

from grimace.frame_quality_model import FrameQualityModel
from grimace.preprocessing.image import crop_image_to_square, average_channels

class FrameQualityScorer:
    def __init__(self, frame_quality_model: FrameQualityModel):
        self.frame_quality_model = frame_quality_model
        self.last_inference_times = [0] * 10
        self.last_inference_time_index = 0

    def preprocess(self, frame: np.ndarray):
        frame = crop_image_to_square(frame)
        frame = cv2.resize(frame, (224, 224), interpolation=cv2.INTER_LINEAR)
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
        start = time.time()
        output = self.frame_quality_model(frame.unsqueeze(0))
        elapsed = time.time() - start
        self.last_inference_times[self.last_inference_time_index] = elapsed
        self.last_inference_time_index = (self.last_inference_time_index + 1) % 10
        #if self.last_inference_time_index == 0:
        #    print(f"Average inference time: {sum(self.last_inference_times) / 10:.4f}")
        return output.squeeze(dim=1).detach().cpu().item()

    def score_batch(self, frames: List[np.ndarray]) -> np.ndarray:
        frames = torch.stack([self.preprocess(frame) for frame in frames])
        return self.frame_quality_model(frames).squeeze(dim=1).detach().cpu().numpy()
