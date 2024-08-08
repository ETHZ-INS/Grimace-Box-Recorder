from typing import List, Optional

import numpy as np

from grimace.frame_cropper_model import FrameCropperModel
from grimace.preprocessing.bounding_box import square_bounding_box, pad_bounding_box, crop_image_to_bounding_box


class FrameCropper:
    def __init__(self, frame_cropper_model: FrameCropperModel, confidence_threshold: float = 0.5, padding: float = 0.):
        self.frame_cropper_model = frame_cropper_model
        self.confidence_threshold = confidence_threshold
        self.padding = padding

    def postprocess(self, frame: np.ndarray, bounding_box: np.ndarray) -> np.ndarray:
        bounding_box = bounding_box[1:]
        bounding_box[0] = bounding_box[0] * frame.shape[1]
        bounding_box[1] = bounding_box[1] * frame.shape[0]
        bounding_box[2] = bounding_box[2] * frame.shape[1]
        bounding_box[3] = bounding_box[3] * frame.shape[0]
        bounding_box = bounding_box.astype(int)

        bounding_box = square_bounding_box(bounding_box)
        bounding_box = pad_bounding_box(bounding_box, self.padding)

        image = crop_image_to_bounding_box(frame, bounding_box)

        return image

    def crop(self, frame: np.ndarray) -> Optional[np.ndarray]:
        bounding_box = self.frame_cropper_model.get_bounding_box(frame)
        #bounding_box = np.array([1.0, 128.0/1280.0, 0.0, 1152.0/1280.0, 1.0])

        if bounding_box[0] < self.confidence_threshold:
            return None

        return self.postprocess(frame, bounding_box)

    def crop_batch(self, frames: List[np.ndarray]) -> List[Optional[np.ndarray]]:
        bounding_boxes = self.frame_cropper_model.get_bounding_boxes(frames)

        return [self.postprocess(frame, bounding_box) if bounding_box[0] >= self.confidence_threshold else None
                for frame, bounding_box in zip(frames, bounding_boxes)]



