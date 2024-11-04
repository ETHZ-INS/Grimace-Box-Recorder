import logging
import os
import sys
from pathlib import Path

import torch
from ultralytics import YOLO

from grimace.frame_cropper import FrameCropper
from grimace.frame_cropper_model import FrameCropperModel
from grimace.frame_quality_model import FrameQualityModel
from grimace.frame_quality_scorer import FrameQualityScorer
from grimace.grimace_scorer import GrimaceScorer
from grimace.grimace_scorer_model import GrimaceScoreModel
from util.trace import Trace

logger = logging.getLogger("grimace_box."+__name__)

bundle_dir = getattr(sys, '_MEIPASS', os.getcwd())
models_folder = Path(os.path.abspath(os.path.join(bundle_dir, 'models')))

demo_model_files = {
    "frame_quality": models_folder / "mock_frame_quality_v2.pt",
    "face_cropper": models_folder / "mock_face_cropper_v2.pt",
    "grimace_scorer": models_folder / "mock_grimace_scorer_v2.pt",
}

real_model_files = {
    "frame_quality": models_folder / "frame_quality.pt",
    "face_cropper": models_folder / "face_cropper.pt",
    "grimace_scorer": models_folder / "grimace_scorer.pt",
}


class GrimaceAnalyzerBuilder:
    @Trace.trace(logger)
    def __init__(self):
        self.model_version = None
        self.model_files = None

        self.frame_quality_device = None
        self.face_cropper_device = None
        self.grimace_scorer_device = None

    @Trace.trace(logger)
    def set_model_version(self, model_version: str) -> 'GrimaceAnalyzerBuilder':
        self.model_version = model_version
        self.model_files = demo_model_files if model_version == "Demo (Fake Mouse)" else real_model_files
        return self

    @Trace.trace(logger)
    def set_devices(self, frame_quality_device: str, face_cropper_device: str, grimace_scorer_device: str) -> 'GrimaceAnalyzerBuilder':
        self.frame_quality_device = frame_quality_device
        self.face_cropper_device = face_cropper_device
        self.grimace_scorer_device = grimace_scorer_device
        return self

    @Trace.trace(logger)
    def build_frame_quality_scorer(self):
        if self.model_version is None:
            raise ValueError("model_version is not set")
        if self.model_files is None:
            raise ValueError("model_files is not set")
        if self.frame_quality_device is None:
            raise ValueError("frame_quality_device is not set")

        frame_quality_model = FrameQualityModel(device=self.frame_quality_device)
        weights_file = self.model_files["frame_quality"]
        model_weights = torch.load(weights_file, map_location=lambda storage, loc: storage)
        frame_quality_model.load_state_dict(model_weights)
        frame_quality_scorer = FrameQualityScorer(frame_quality_model)
        return frame_quality_scorer

    @Trace.trace(logger)
    def build_face_cropper(self):
        if self.model_version is None:
            raise ValueError("model_version is not set")
        if self.model_files is None:
            raise ValueError("model_files is not set")
        if self.face_cropper_device is None:
            raise ValueError("face_cropper_device is not set")

        face_cropper_model_base = YOLO(self.model_files["face_cropper"])
        face_cropper_model_base.to(self.face_cropper_device)
        face_cropper_model = FrameCropperModel(face_cropper_model_base,
                                               device=self.face_cropper_device)
        # TODO: Decide on confidence threshold or make it configurable
        face_cropper = FrameCropper(face_cropper_model, padding=0.05, confidence_threshold=0.9)
        return face_cropper

    @Trace.trace(logger)
    def build_grimace_scorer(self):
        if self.model_version is None:
            raise ValueError("model_version is not set")
        if self.model_files is None:
            raise ValueError("model_files is not set")
        if self.grimace_scorer_device is None:
            raise ValueError("grimace_scorer_device is not set")

        grimace_scorer_model = GrimaceScoreModel(device=self.grimace_scorer_device)
        weights_file = self.model_files["grimace_scorer"]
        model_weights = torch.load(weights_file, map_location=lambda storage, loc: storage)
        grimace_scorer_model.load_state_dict(model_weights)
        grimace_scorer = GrimaceScorer(grimace_scorer_model)
        return grimace_scorer
