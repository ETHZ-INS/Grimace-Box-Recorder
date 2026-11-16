import logging
import os
import sys
from pathlib import Path
from typing import List

from ultralytics import YOLO

from grimace.no_pose_model import NoPoseModel
from grimace.pose_model import PoseModel
from util.trace import Trace

logger = logging.getLogger("grimace_box."+__name__)

bundle_dir = getattr(sys, '_MEIPASS', os.getcwd())
models_folder = Path(os.path.abspath(os.path.join(bundle_dir, 'models')))

demo_model_files = {
    "top_pose_estimator": models_folder / "mock_top_pose_estimator.pt",
    "top_pose_keypoints": models_folder / "top_pose_keypoints.txt",
}

real_model_files = {
    "top_pose_estimator": models_folder / "top_pose_estimator.pt",
    "top_pose_keypoints": models_folder / "top_pose_keypoints.txt",
}


class PoseEstimatorBuilder:
    @Trace.trace(logger)
    def __init__(self):
        self.model_version = None
        self.model_files = None

        self.pose_estimation_device = None

    @Trace.trace(logger)
    def set_model_version(self, model_version: str) -> 'PoseEstimatorBuilder':
        self.model_version = model_version
        self.model_files = demo_model_files if model_version == "Demo (Fake Mouse)" else real_model_files
        return self

    @Trace.trace(logger)
    def set_device(self, pose_estimation_device: str) -> 'PoseEstimatorBuilder':
        self.pose_estimation_device = pose_estimation_device
        return self

    @Trace.trace(logger)
    def build_pose_estimator_model(self):
        if self.model_version is None:
            raise ValueError("model_version is not set")
        if self.model_files is None:
            raise ValueError("model_files is not set")
        if self.pose_estimation_device is None:
            raise ValueError("frame_quality_device is not set")

        if self.model_version == "No Pose Estimation":
            return NoPoseModel()

        top_pose_estimator_model_base = YOLO(self.model_files["top_pose_estimator"])
        top_pose_estimator_model_base.to(self.pose_estimation_device)
        top_pose_estimator_model = PoseModel(top_pose_estimator_model_base, device=self.pose_estimation_device)

        return top_pose_estimator_model

    @Trace.trace(logger)
    def get_pose_keypoints(self) -> List[str]:
        if self.model_version is None:
            raise ValueError("model_version is not set")
        if self.model_files is None:
            raise ValueError("model_files is not set")

        with open(self.model_files["top_pose_keypoints"], "r") as f:
            top_pose_keypoints = [line.strip() for line in f]

        return top_pose_keypoints
