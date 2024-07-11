import time
from typing import List

import cv2
import numpy as np
import torch

from grimace.grimace_scorer_model import GrimaceScoreModel


class GrimaceScorer:
    def __init__(self, grimace_scorer_model: GrimaceScoreModel):
        self.grimace_scorer_model = grimace_scorer_model

    def preprocess(self, frame: np.ndarray):
        frame = cv2.resize(frame, (224, 224), interpolation=cv2.INTER_LINEAR)
        if frame.ndim == 2 or frame.shape[2] == 1:
            frame = np.stack([frame] * 3, axis=2)
        frame = frame.astype(np.float32)
        frame /= 255.0
        frame = frame.transpose(2, 0, 1)
        frame = torch.tensor(frame)
        frame = (frame - 0.5175) / 0.14
        return frame

    def score(self, frame: np.ndarray) -> np.ndarray:
        frame = self.preprocess(frame)
        output = self.grimace_scorer_model(frame.unsqueeze(0)).detach().cpu().numpy()
        predictions = np.argmax(output, axis=2)
        return predictions.squeeze()

    def score_batch(self, frames: List[np.ndarray]) -> np.ndarray:
        frames = torch.stack([self.preprocess(frame) for frame in frames])
        output = self.grimace_scorer_model(frames).detach().cpu().numpy()
        predictions = np.argmax(output, axis=2)
        return predictions.squeeze()
