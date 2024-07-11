from grimace.frame_cropper import FrameCropper
from grimace.frame_quality_model import FrameQualityModel


class FrameExtractor:
    def __init__(self, frame_quality_model: FrameQualityModel, frame_cropper: FrameCropper):
        self.frame_quality_model = frame_quality_model
        self.frame_cropper = frame_cropper

