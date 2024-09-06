import os
import sys
import time
from copy import deepcopy
from pathlib import Path, PurePath
from typing import Optional, Dict, List

import cv2
import numpy as np
import torch
from PySide6 import QtCore
from PySide6.QtCore import QObject, Signal, QTimer, QThread
from ultralytics import YOLO

from app.config.camera import CameraConfig
from app.config.grimace import GrimaceConfig
from app.config.pose_top import PoseTopConfig
from app.config.recording import RecordingConfig
from app.config.video_files import VideoFilesConfig
from app.dataflow.qlist import QList
from app.dataflow.qqueue import IQueue
from app.dataflow.qvariable import QVariable
from app.recording.FPSRenderer import FPSRenderer
from app.recording.front_video_pipeline_builder import FrontVideoPipelineBuilder
from app.recording.camera_recorder.dual_camera_recorder import DualCameraRecorder, build_camera_source
from app.recording.recording_context import RecordingContext
from app.recording.top_video_pipeline_builder import TopVideoPipelineBuilder
from app.recording.video_pipeline import VideoPipeline
from app.recording.video_writer import BufferVideoWriter
from grimace.camera_identifier import CameraIdentifier
from grimace.camera_identifier_model import CameraIdentifierModel
from grimace.frame_cropper import FrameCropper
from grimace.frame_cropper_model import FrameCropperModel
from grimace.frame_quality_model import FrameQualityModel
from grimace.frame_quality_scorer import FrameQualityScorer
from grimace.grimace_scorer import GrimaceScorer
from grimace.grimace_scorer_model import GrimaceScoreModel

import logging

from grimace.pose_model import PoseModel
from util.trace import Trace

logger = logging.getLogger("grimace_recorder.app.recording.recording_manager")

bundle_dir = getattr(sys, '_MEIPASS', os.getcwd())
models_folder = Path(os.path.abspath(os.path.join(bundle_dir, 'models')))

demo_model_files = {
    "frame_quality": models_folder / "mock_frame_quality_v2.pt",
    "face_cropper": models_folder / "mock_face_cropper_v2.pt",
    "grimace_scorer": models_folder / "mock_grimace_scorer_v2.pt",
    "camera_identifier": models_folder / "camera_identifier.pt",
    # TODO: Train a demo model for top pose estimation
    "top_pose_estimator": models_folder / "mock_top_pose_estimator.pt",
    "top_pose_keypoints": models_folder / "top_pose_keypoints.txt",
}

super_scorer_model_files = {
    "frame_quality": models_folder / "frame_quality.pt",
    "face_cropper": models_folder / "face_cropper.pt",
    "grimace_scorer": models_folder / "grimace_scorer.pt",
    "camera_identifier": models_folder / "camera_identifier.pt",
    "top_pose_estimator": models_folder / "top_pose_estimator.pt",
    "top_pose_keypoints": models_folder / "top_pose_keypoints.txt",
}

# TODO: After loading config, ready to record despite cameras not found. Also when error in Grimace config
# TODO: When both cameras disconnect at once, they show different errors
#  ("device with serial number ... not found" vs "camera is not conneced"
# TODO: Loaded config with video file cameras, then switched to real camera, applied, then added camera config file, applied
#  The device is controlled by another application. Err: An attempt was made to access an address location which is currently/momentary not accessible

# TODO Currently all queue consumers (BufferVideoWriter, GrimaceResultsWriter, TopPoseEstimatorV1, etc.)
#   are built to be one time use. They are initialized with a queue, and when the queue is closed, they die.
#   Should this be changed? PreviewQueue is a special case, as it is not closed.

# TODO: Top video file still locked after recording stopped


class FileBuilder:
    def __init__(self):
        self.target_directory = None
        self.recording_number = None
        self.timestamp = None
        self.templates = {}

    def set_target_directory(self, target_directory: str) -> 'FileBuilder':
        self.target_directory = target_directory
        return self

    def set_recording_number(self, recording_number: int) -> 'FileBuilder':
        self.recording_number = recording_number
        return self

    def set_timestamp(self, timestamp: str) -> 'FileBuilder':
        self.timestamp = timestamp
        return self

    def set_template(self, name: str, template: str) -> 'FileBuilder':
        self.templates[name] = template
        return self

    def find_next_unused_recording_number(self) -> int:
        # Find the next recording number that does not collide with any existing files
        while True:
            for template_name in self.templates:
                file = self.construct_file(template_name)
                if file is not None and file.exists():
                    self.recording_number += 1
                    break
            # If we didn't break, we found a recording number that does not collide with any files, so we're done
            else:
                break
        return self.recording_number

    def construct_file(self, name: str) -> Path | None:
        template = self.templates.get(name)
        if template is None or self.recording_number is None or self.timestamp is None or self.target_directory is None:
            return None
        filename = template.format(recording_number=self.recording_number, start_time=self.timestamp)
        return Path(self.target_directory) / filename


class VideoWriterBuilder:
    def __init__(self):
        self.video_file: Path | None = None
        self.timestamp_file: Path | None = None

        self.fourcc: int | None = None
        self.width: int | None = None
        self.height: int | None = None
        self.fps: float | None = None

    def set_video_file(self, video_file: Path) -> 'VideoWriterBuilder':
        self.video_file = video_file
        return self

    def set_timestamp_file(self, timestamp_file: Path) -> 'VideoWriterBuilder':
        self.timestamp_file = timestamp_file
        return self

    def set_fourcc(self, fourcc: int) -> 'VideoWriterBuilder':
        self.fourcc = fourcc
        return self

    def set_width(self, width: int) -> 'VideoWriterBuilder':
        self.width = width
        return self

    def set_height(self, height: int) -> 'VideoWriterBuilder':
        self.height = height
        return self

    def set_fps(self, fps: float) -> 'VideoWriterBuilder':
        self.fps = fps
        return self

    def build(self) -> BufferVideoWriter:
        if self.video_file is None:
            raise ValueError("Video file not configured")
        if self.timestamp_file is None:
            raise ValueError("Timestamp file not configured")
        if self.fourcc is None:
            raise ValueError("Video codec not configured")
        if self.width is None:
            raise ValueError("Video width not configured")
        if self.height is None:
            raise ValueError("Video height not configured")
        if self.fps is None:
            raise ValueError("Video FPS not configured")

        video_writer = cv2.VideoWriter(str(self.video_file), self.fourcc, self.fps, (self.width, self.height), isColor=False)
        return BufferVideoWriter(video_writer, 1000, self.timestamp_file)


class RecordingManager(QObject):
    overview_changed_signal = Signal()
    warnings_changed_signal = Signal()
    recording_started_signal = Signal()
    recording_stopped_signal = Signal()
    recording_error_signal = Signal(str)
    analysis_error_signal = Signal(str)
    top_camera_error_signal = Signal(str)
    front_camera_error_signal = Signal(str)

    @Trace.trace(logger)
    def __init__(self, preview_buffer_top: QVariable, preview_buffer_front: QVariable):
        super().__init__()
        self.preview_buffer_top = preview_buffer_top
        self.preview_buffer_front = preview_buffer_front

        self.camera_top_config = CameraConfig()
        self.camera_front_config = CameraConfig()
        self.recording_config = RecordingConfig()
        self.video_files_config = VideoFilesConfig()
        self.grimace_config = GrimaceConfig()
        self.pose_config = PoseTopConfig()

        self.recording_number = 1

        self.top_video_file: Optional[Path] = None
        self.front_video_file: Optional[Path] = None
        self.grimace_results_file: Optional[Path] = None
        self.top_timestamps_file: Optional[Path] = None
        self.front_timestamps_file: Optional[Path] = None
        self.pose_results_file: Optional[Path] = None

        self.frame_quality_scorer = None
        self.face_cropper = None
        self.grimace_scorer = None
        self.top_pose_estimator_model = None

        camera_identifier_model = CameraIdentifierModel(device="cpu")
        # TODO: What is map_location?
        model_weights = torch.load(super_scorer_model_files["camera_identifier"], map_location=lambda storage, loc: storage)
        camera_identifier_model.load_state_dict(model_weights)
        self.camera_identifier = CameraIdentifier(camera_identifier_model)

        self.camera_recorder = DualCameraRecorder(self.camera_identifier)
        self.camera_recorder.setPriority(QThread.Priority.HighestPriority)
        self.camera_recorder.stop_signal.connect(self.stop_recording)
        self.camera_recorder.top_error_signal.connect(self.on_top_camera_error)
        self.camera_recorder.front_error_signal.connect(self.on_front_camera_error)

        self.recording_context = None

        self.grimace_results_list = QList()

        self.top_pose_keypoints = None

        self.top_video_pipeline = None
        self.front_video_pipeline = None

        self.recording_running = False
        self.analysis_running = False

        self.health_timer = QTimer(self)
        self.health_timer.timeout.connect(self.check_health)
        self.health_timer.start(1000)

        self.recording_error: Optional[str] = None
        self.analysis_error: Optional[str] = None
        self.warnings: Dict[str, str] = {}

    @Trace.trace(logger)
    def find_next_recording_number(self, target_directory: str, templates: List[str], timestamp: str, start: int = 1) -> int:
        if start is None:
            start = 1

        # Find the next recording number that does not have a file
        recording_number = start
        while True:
            for template in templates:
                filename = template.format(recording_number=recording_number, start_time=timestamp)
                filepath = Path(target_directory) / filename
                if filepath.exists():
                    recording_number += 1
                    break
            else:
                break
        return recording_number

    @Trace.trace(logger)
    def construct_files(self, video_files_config: VideoFilesConfig):
        naming_mode = video_files_config.naming_mode

        top_video_file_template = video_files_config.top_templates.get(naming_mode)
        front_video_file_template = video_files_config.front_templates.get(naming_mode)
        grimace_results_file_template = video_files_config.grimace_results_templates.get(naming_mode)
        pose_results_file_template = video_files_config.pose_results_templates.get(naming_mode)

        if top_video_file_template is None:
            top_timestamps_template = None
        else:
            top_timestamps_template = str(PurePath(top_video_file_template).with_suffix(".csv"))

        if front_video_file_template is None:
            front_timestamps_template = None
        else:
            front_timestamps_template = str(PurePath(front_video_file_template).with_suffix(".csv"))

        file_builder = FileBuilder()
        file_builder.set_target_directory(video_files_config.target_directory)
        file_builder.set_recording_number(self.recording_number)
        file_builder.set_timestamp(time.strftime("%Y%m%d%H%M%S"))
        file_builder.set_template("top_video", top_video_file_template)
        file_builder.set_template("front_video", front_video_file_template)
        file_builder.set_template("grimace_results", grimace_results_file_template)
        file_builder.set_template("top_timestamps", top_timestamps_template)
        file_builder.set_template("front_timestamps", front_timestamps_template)
        file_builder.set_template("pose_results", pose_results_file_template)

        self.recording_number = file_builder.find_next_unused_recording_number()
        logger.info("Setting recording_number=%s", self.recording_number)

        self.top_video_file = file_builder.construct_file("top_video")
        self.front_video_file = file_builder.construct_file("front_video")
        self.grimace_results_file = file_builder.construct_file("grimace_results")
        self.top_timestamps_file = file_builder.construct_file("top_timestamps")
        self.front_timestamps_file = file_builder.construct_file("front_timestamps")
        self.pose_results_file = file_builder.construct_file("pose_results")

        logger.info("Setting top_video_file=%s", self.top_video_file)
        logger.info("Setting front_video_file=%s", self.front_video_file)
        logger.info("Setting grimace_results_file=%s", self.grimace_results_file)
        logger.info("Setting top_timestamps_file=%s", self.top_timestamps_file)
        logger.info("Setting front_timestamps_file=%s", self.front_timestamps_file)
        logger.info("Setting pose_results_file=%s", self.pose_results_file)

    @Trace.trace(logger)
    def configure_video_files(self, video_files_config: Optional[VideoFilesConfig]):
        self.video_files_config = deepcopy(video_files_config)

        self.construct_files(video_files_config)

        self.overview_changed_signal.emit()

    @Trace.trace(logger)
    def configure_top_camera(self, camera_config: Optional[CameraConfig], start: bool = True):
        if self.recording_running:
            raise ValueError("Cannot change camera configuration while recording")

        self.camera_top_config = deepcopy(camera_config)
        logger.info("Setting Camera Top Config: %s", self.camera_top_config)

        camera_ready = True
        if camera_config.camera_type == "Pylon" and camera_config.camera_id is None:
            camera_ready = False
        elif camera_config.camera_type == "Video File" and camera_config.video_file is None:
            camera_ready = False

        self.stop_preview()

        # Set the camera to None to close the camera source as there's an error when opening the same camera again
        self.camera_recorder.set_top_camera(None)

        if camera_ready:
            source = build_camera_source(camera_config)
            self.camera_recorder.set_top_camera(
                source, start=False
            )
            self.camera_recorder.top_camera.set_video_buffer(FPSRenderer(self.preview_buffer_top))
            self.start_preview()

        self.overview_changed_signal.emit()

    @Trace.trace(logger)
    def configure_front_camera(self, camera_config: Optional[CameraConfig], start: bool = True):
        if self.recording_running:
            raise ValueError("Cannot change camera configuration while recording")

        self.camera_front_config = deepcopy(camera_config)
        logger.info("Setting Camera Front Config: %s", self.camera_front_config)

        camera_ready = True
        if camera_config.camera_type == "Pylon" and camera_config.camera_id is None:
            camera_ready = False
        elif camera_config.camera_type == "Video File" and camera_config.video_file is None:
            camera_ready = False

        self.stop_preview()

        # Set the camera to None to close the camera source as there's an error when opening the same camera again
        self.camera_recorder.set_front_camera(None, start=False)

        if camera_ready:
            source = build_camera_source(camera_config)
            self.camera_recorder.set_front_camera(
                source, start=False
            )
            self.camera_recorder.front_camera.set_video_buffer(FPSRenderer(self.preview_buffer_front))
            self.start_preview()

        self.overview_changed_signal.emit()

    @Trace.trace(logger)
    def configure_recording(self, recording_config: RecordingConfig):
        self.recording_config = deepcopy(recording_config)
        logger.info("Setting Recording Config: %s", self.recording_config)
        self.overview_changed_signal.emit()

    @Trace.trace(logger)
    def configure_grimace(self, grimace_config: GrimaceConfig):
        self.grimace_config = deepcopy(grimace_config)
        logger.info("Setting Analysis Config: %s", self.grimace_config)

        if self.grimace_config.grimace_model == "V1 - HohlBot":
            model_files = super_scorer_model_files
        elif self.grimace_config.grimace_model == "Demo (Fake Mouse)":
            model_files = demo_model_files
        else:
            raise ValueError(f"Unknown model version: {self.grimace_config.grimace_model}")

        if grimace_config is not None and grimace_config.enabled:
            if self.grimace_config.frame_quality_device is not None:
                frame_quality_model = FrameQualityModel(device=grimace_config.frame_quality_device)
                model_weights = torch.load(model_files["frame_quality"], map_location=lambda storage, loc: storage)
                frame_quality_model.load_state_dict(model_weights)
                self.frame_quality_scorer = FrameQualityScorer(frame_quality_model)
            else:
                self.frame_quality_scorer = None

            if self.grimace_config.face_cropper_device is not None:
                face_cropper_model_base = YOLO(model_files["face_cropper"])
                face_cropper_model_base.to(grimace_config.face_cropper_device)
                face_cropper_model = FrameCropperModel(face_cropper_model_base, device=grimace_config.face_cropper_device)
                # TODO: Decide on confidence threshold or make it configurable
                self.face_cropper = FrameCropper(face_cropper_model, padding=0.05, confidence_threshold=0.9)
            else:
                self.face_cropper = None

            if self.grimace_config.grimace_scoring_device is not None:
                grimace_scorer_model = GrimaceScoreModel(device=grimace_config.grimace_scoring_device)
                model_weights = torch.load(model_files["grimace_scorer"], map_location=lambda storage, loc: storage)
                grimace_scorer_model.load_state_dict(model_weights)
                self.grimace_scorer = GrimaceScorer(grimace_scorer_model)
            else:
                self.grimace_scorer = None
        else:
            self.frame_quality_scorer = None
            self.face_cropper = None
            self.grimace_scorer = None

        self.overview_changed_signal.emit()

    @Trace.trace(logger)
    def configure_pose_tracking(self, pose_config: PoseTopConfig):
        self.pose_config = deepcopy(pose_config)
        logger.info("Setting Pose Config: %s", self.pose_config)

        if self.pose_config.pose_model == "V1 - GrimaceBoxTop":
            model_files = super_scorer_model_files
        elif self.pose_config.pose_model == "Demo (Fake Mouse)":
            model_files = demo_model_files
        else:
            raise ValueError(f"Unknown model version: {self.pose_config.pose_model}")

        if self.pose_config is not None and self.pose_config.enabled and self.pose_config.pose_device is not None:
            top_pose_estimator_model_base = YOLO(model_files["top_pose_estimator"])
            top_pose_estimator_model_base.to(self.pose_config.pose_device)
            self.top_pose_estimator_model = PoseModel(top_pose_estimator_model_base, device=self.pose_config.pose_device)

            with open(model_files["top_pose_keypoints"], "r") as f:
                self.top_pose_keypoints = [line.strip() for line in f]
        else:
            self.top_pose_estimator_model = None

        self.overview_changed_signal.emit()

    @Trace.trace(logger)
    def reset_error(self):
        self.recording_error = None
        self.analysis_error = None

    def get_not_ready_reason(self) -> Optional[str]:
        if self.recording_number is None:
            return "Recording number not set"

        if self.camera_top_config is None:
            return "Top camera not configured"

        if self.camera_front_config is None:
            return "Front camera not configured"

        if self.camera_top_config.camera_type == "Pylon" and self.camera_top_config.camera_id is None:
            return "Top camera device not selected"
        elif self.camera_top_config.camera_type == "Video File" and self.camera_top_config.video_file is None:
            return "Top video file not selected"

        if self.camera_front_config.camera_type == "Pylon" and self.camera_front_config.camera_id is None:
            return "Front camera device not selected"
        elif self.camera_front_config.camera_type == "Video File" and self.camera_front_config.video_file is None:
            return "Front video file not selected"

        if self.recording_config is None:
            return "Recording not configured"

        if self.video_files_config is None:
            return "Video files not configured"

        if self.top_video_file is None or self.front_video_file is None:
            return "Video files not properly configured"

        if self.top_timestamps_file is None or self.front_timestamps_file is None:
            return "Video files not properly configured"

        if self.camera_top_config.fps is None:
            return "Top camera FPS not configured"

        if self.camera_front_config.fps is None:
            return "Front camera FPS not configured"

        if self.recording_config.mode is None:
            return "Recording mode not configured"

        if self.recording_config.mode == "Timed" and self.recording_config.duration is None:
            return "Recording duration not configured"

        if self.recording_config.codec is None:
            return "Codec not configured"

        if self.grimace_config.enabled is None:
            return "Grimace scoring not configured"

        if self.grimace_config.enabled:
            if self.grimace_config.grimace_model is None:
                return "Grimace model not configured"
            if self.grimace_config.frame_interval is None:
                return "Frame interval not configured"
            if self.frame_quality_scorer is None:
                return "Frame quality scorer not configured"
            if self.grimace_config.frame_quality_device is None:
                return "Frame quality device not configured"
            if self.grimace_config.face_cropper_device is None:
                return "Face cropper device not configured"
            if self.grimace_config.grimace_scoring_device is None:
                return "Grimace scoring device not configured"
            if self.face_cropper is None:
                return "Face cropper not configured"
            if self.grimace_scorer is None:
                return "Grimace scorer not configured"
            if self.grimace_results_file is None:
                return "Grimace results file not properly configured"

        if self.pose_config.enabled is None:
            return "Pose tracking not configured"

        if self.pose_config.enabled:
            if self.pose_config.pose_model is None:
                return "Pose model not configured"
            if self.pose_config.pose_device is None:
                return "Pose device not configured"
            if self.top_pose_estimator_model is None:
                return "Top pose estimator model not configured"
            if self.top_pose_keypoints is None:
                return "Top pose keypoints not configured"
            if self.pose_results_file is None:
                return "Pose results file not properly configured"

    def get_warnings(self) -> List[str]:
        warnings = []
        if self.analysis_error is not None:
            analysis_warning = (f"An error occurred in the live analysis, so it was stopped.  \n"
                                f"The recording may still continue.  \n"
                                f"Cause: {self.analysis_error}")
            warnings.append(analysis_warning)
        if self.camera_top_config is not None and self.camera_front_config is not None:
            if self.camera_top_config.fps is not None and self.camera_front_config.fps is not None:
                if self.camera_top_config.fps != self.camera_front_config.fps:
                    warnings.append("Top and front camera FPS are different")
        for key, value in self.warnings.items():
            if value is not None:
                warnings.append(value)
        return warnings

    def set_warning(self, key: str, value: str) -> bool:
        prev_value = self.warnings.get(key)
        if prev_value != value:
            self.warnings[key] = value
            logger.warning(value)
            return True
        return False

    def check_health(self):
        warnings_changed = False
        top_video_buffer_fill_level = 0.0
        front_video_buffer_fill_level = 0.0
        grimace_input_buffer_fill_level = 0.0
        grimace_output_buffer_fill_level = 0.0

        # TODO: if the fps drop and then recover, the warning will disappear. Should it stay?
        #  Unless someone is constantly monitoring the warnings, it will be missed.

        analysis_critical = False

        if self.camera_recorder is not None:
            camera_recorder_report = self.camera_recorder.check_health()
            for key, value in camera_recorder_report["warnings"].items():
                warnings_changed |= self.set_warning(key, value)

        if self.top_video_pipeline is not None:
            top_video_pipeline_report = self.top_video_pipeline.check_health(prefix="top_")
            for key, value in top_video_pipeline_report["warnings"].items():
                warnings_changed |= self.set_warning(key, value)

            top_video_buffer_fill_level = top_video_pipeline_report.get("top_video_writer_queue_fill_level", 0.0)
            pose_estimation_results_writer_queue_fill_level = top_video_pipeline_report.get(
                "top_pose_estimation_results_writer_queue_fill_level", 0.0)
            pose_estimation_queue_fill_level = top_video_pipeline_report.get(
                "top_pose_estimation_queue_fill_level", 0.0)

            if (top_video_buffer_fill_level > 0.7 or pose_estimation_results_writer_queue_fill_level > 0.9
                    or pose_estimation_queue_fill_level > 0.9):
                analysis_critical = True

        if self.front_video_pipeline is not None:
            front_video_pipeline_report = self.front_video_pipeline.check_health(prefix="front_")
            for key, value in front_video_pipeline_report["warnings"].items():
                warnings_changed |= self.set_warning(key, value)

            front_video_buffer_fill_level = front_video_pipeline_report.get("front_video_writer_queue_fill_level", 0.0)
            grimace_scorer_queue_fill = front_video_pipeline_report.get("front_grimace_analysis_queue_fill_level", 0.0)
            grimace_results_writer_queue_fill = front_video_pipeline_report.get(
                "front_grimace_results_writer_queue_fill_level", 0.0)

            if (front_video_buffer_fill_level > 0.7 or grimace_scorer_queue_fill > 0.9 or
                    grimace_results_writer_queue_fill > 0.9):
                analysis_critical = True

        if warnings_changed:
            self.warnings_changed_signal.emit()

        if analysis_critical:
            self.on_analysis_error("One or more buffers are critically full")

    def prepare_top_video_processing(self):
        vwb = VideoWriterBuilder()
        vwb.set_video_file(self.top_video_file)
        vwb.set_timestamp_file(self.top_timestamps_file)
        vwb.set_fourcc(cv2.VideoWriter.fourcc(*self.recording_config.codec))
        vwb.set_width(self.camera_recorder.top_camera.get_width())
        vwb.set_height(self.camera_recorder.top_camera.get_height())
        vwb.set_fps(self.camera_top_config.fps)
        video_writer = vwb.build()

        pb = TopVideoPipelineBuilder()
        pb.set_pose_enabled(self.pose_config.enabled)
        pb.set_pose_preview_enabled(self.pose_config.show_preview)
        pb.set_preview_queue(self.preview_buffer_top)

        pb.set_video_writer(video_writer)
        pb.set_pose_estimator_model(self.top_pose_estimator_model)
        pb.set_pose_results_file(self.pose_results_file)
        pb.set_top_pose_keypoints(self.top_pose_keypoints)
        pb.set_target_frame_rate(self.camera_top_config.fps)

        self.top_video_pipeline = pb.build()

    def prepare_front_video_processing(self):
        vwb = VideoWriterBuilder()
        vwb.set_video_file(self.front_video_file)
        vwb.set_timestamp_file(self.front_timestamps_file)
        vwb.set_fourcc(cv2.VideoWriter.fourcc(*self.recording_config.codec))
        vwb.set_width(self.camera_recorder.front_camera.get_width())
        vwb.set_height(self.camera_recorder.front_camera.get_height())
        vwb.set_fps(self.camera_front_config.fps)
        video_writer = vwb.build()

        pb = FrontVideoPipelineBuilder()
        pb.set_grimace_enabled(self.grimace_config.enabled)
        pb.set_preview_queue(self.preview_buffer_front)
        pb.set_results_preview_queue(self.grimace_results_list)

        pb.set_video_writer(video_writer)
        pb.set_frame_quality_scorer(self.frame_quality_scorer)
        pb.set_face_cropper(self.face_cropper)
        pb.set_grimace_scorer(self.grimace_scorer)
        pb.set_frames_per_interval(round(self.grimace_config.frame_interval * self.camera_front_config.fps))
        pb.set_grimace_results_file(self.grimace_results_file)

        self.front_video_pipeline = pb.build()

    @Trace.trace(logger)
    def prepare_recording(self):
        self.configure_video_files(self.video_files_config)

        self.prepare_top_video_processing()
        self.prepare_front_video_processing()

        self.top_video_pipeline.on_analysis_error(self.on_analysis_error)
        self.front_video_pipeline.on_analysis_error(self.on_analysis_error)

        self.top_video_pipeline.on_error(self.on_recording_error)
        self.front_video_pipeline.on_error(self.on_recording_error)

        recording_duration = self.recording_config.duration if self.recording_config.mode == "Timed" else None
        self.recording_context = RecordingContext(recording_duration)

        self.overview_changed_signal.emit()

    @Trace.trace(logger)
    def start_preview(self):
        if self.recording_running:
            logger.warning("Cannot start preview while recording is running")
            return

        self.stop_preview()

        if self.camera_recorder.top_camera is not None or self.camera_recorder.front_camera is not None:
            self.camera_recorder.start()

    @Trace.trace(logger)
    def stop_preview(self):
        if self.recording_running:
            logger.warning("Cannot stop preview while recording is running")
            return

        if self.camera_recorder.running:
            self.camera_recorder.stop()
            self.camera_recorder.wait()

    @Trace.trace(logger)
    def start_recording(self):
        if self.recording_running:
            raise ValueError("Recording already running")

        self.stop_preview()

        self.analysis_error = None
        self.recording_error = None
        self.warnings = {}

        if self.camera_recorder.isRunning():
            self.camera_recorder.stop()
            self.camera_recorder.wait()

        self.recording_running = True
        if self.grimace_config.enabled or self.pose_config.enabled:
            self.analysis_running = True

        # TODO: do sanity checks on the configuration before starting recording

        self.camera_recorder.top_camera.set_video_buffer(self.top_video_pipeline.input_queue)
        self.camera_recorder.front_camera.set_video_buffer(self.front_video_pipeline.input_queue)

        self.camera_recorder.set_recording_context(self.recording_context)

        if self.grimace_config.enabled:
            self.grimace_results_list.clear()

        self.top_video_pipeline.start()
        self.front_video_pipeline.start()

        self.camera_recorder.start()

        self.overview_changed_signal.emit()
        self.recording_started_signal.emit()

    @Trace.trace(logger)
    def stop_recording(self, start_preview: bool = True):
        if not self.recording_running:
            return

        # Stop the recorder to stop the flow of frames through the pipeline
        # The other parts of the pipeline will stop themselves when they're done processing the frames
        self.camera_recorder.stop()
        self.camera_recorder.wait()

        self.camera_recorder.top_camera.set_video_buffer(None)
        self.camera_recorder.front_camera.set_video_buffer(None)

        # TODO: Does this order make sense?
        self.camera_recorder.set_recording_context(None)
        self.recording_context.stop()

        # TODO: Do some kind of warning if it timed out
        # TODO: Some kind of loading screen would also be nice
        if not self.top_video_pipeline.wait(2000):
            logger.error("Top video pipeline did not stop after 2 seconds")
            self.top_video_pipeline.stop()
            if not self.top_video_pipeline.wait(2000):
                logger.error("Top video pipeline did not stop after notifying and another 2 seconds")

        if not self.front_video_pipeline.wait(2000):
            logger.error("Front video pipeline did not stop after 2 seconds")
            self.front_video_pipeline.stop()
            if not self.front_video_pipeline.wait(2000):
                logger.error("Front video pipeline did not stop after notifying and another 2 seconds")

        self.recording_running = False
        self.analysis_running = False

        # TODO: I think this was meant to increment the recording number, but that's a bit gross
        self.configure_video_files(self.video_files_config)

        self.camera_recorder.top_camera.set_video_buffer(FPSRenderer(self.preview_buffer_top))
        self.camera_recorder.front_camera.set_video_buffer(FPSRenderer(self.preview_buffer_front))

        if start_preview:
            self.start_preview()

        self.overview_changed_signal.emit()
        self.recording_stopped_signal.emit()

    @Trace.trace(logger, level=logging.WARNING)
    def on_recording_error(self, error: str):
        self.force_stop_recording()
        self.recording_error = error
        self.recording_error_signal.emit(error)

    @Trace.trace(logger, level=logging.WARNING)
    def on_analysis_error(self, error: str):
        self.force_stop_analysis()
        self.analysis_error = error
        self.analysis_error_signal.emit(error)
        self.warnings_changed_signal.emit()

    @Trace.trace(logger, level=logging.WARNING)
    def on_top_camera_error(self, error: str):
        if self.recording_running:
            self.force_stop_recording(kick_top_camera=True)
            self.recording_error = "Top Camera Error: " + error
            self.recording_error_signal.emit(self.recording_error)
        else:
            self.force_stop_recording(kick_top_camera=True)
        self.top_camera_error_signal.emit(error)

    @Trace.trace(logger, level=logging.WARNING)
    def on_front_camera_error(self, error: str):
        if self.recording_running:
            self.force_stop_recording(kick_front_camera=True)
            self.recording_error = "Front Camera Error: " + error
            self.recording_error_signal.emit(self.recording_error)
        else:
            self.force_stop_recording(kick_front_camera=True)
        self.front_camera_error_signal.emit(error)

    @Trace.trace(logger, level=logging.WARNING)
    def force_stop_analysis(self):
        # Only stop grimace analysis so the recording, which is much more important, may still be able to finish
        self.top_video_pipeline.stop_analysis()
        self.front_video_pipeline.stop_analysis()

        self.analysis_running = False

    def kick_top_camera(self):
        top_camera_config = deepcopy(self.camera_top_config)
        top_camera_config.camera_id = None
        self.configure_top_camera(top_camera_config, start=False)

    def kick_front_camera(self):
        front_camera_config = deepcopy(self.camera_front_config)
        front_camera_config.camera_id = None
        self.configure_front_camera(front_camera_config, start=False)

    @Trace.trace(logger, level=logging.WARNING)
    def force_stop_recording(self, kick_top_camera: bool = False, kick_front_camera: bool = False, start_preview: bool = True):
        """
        Last resort to stop recording. This will stop the recording and all analysis, and try to restart the cameras.
        TODO: Find a better solution for removing the faulty camera. Maybe just remove both in any case
        :param kick_top_camera:
        :param kick_front_camera:
        :param start_preview:
        :return:
        """
        if self.camera_recorder is not None:
            self.camera_recorder.stop()

        if self.top_video_pipeline is not None:
            self.top_video_pipeline.stop()

        if self.front_video_pipeline is not None:
            self.front_video_pipeline.stop()

        # Wait for the pipelines to stop. Stopping without timeout.
        # If the application doesn't respond, the user can decide to force close the application
        # or wait if the results are too important.
        if self.camera_recorder is not None:
            self.camera_recorder.wait()

        if self.top_video_pipeline is not None:
            self.top_video_pipeline.wait()

        if self.front_video_pipeline is not None:
            self.front_video_pipeline.wait()

        if self.camera_recorder is not None:
            if self.camera_recorder.top_camera is not None:
                self.camera_recorder.top_camera.set_video_buffer(None)
                self.camera_recorder.set_top_camera(None, start=False)

            if self.camera_recorder.front_camera is not None:
                self.camera_recorder.front_camera.set_video_buffer(None)
                self.camera_recorder.set_front_camera(None, start=False)

            self.camera_recorder.set_recording_context(None)

        self.recording_running = False
        self.analysis_running = False

        # Try to remove the faulty camera while trying to reinstate the working camera.
        if kick_top_camera:
            self.kick_top_camera()
        else:
            try:
                self.configure_top_camera(self.camera_top_config)
            except Exception as e:
                self.on_top_camera_error(str(e))

        if kick_front_camera:
            self.kick_front_camera()
        else:
            try:
                self.configure_front_camera(self.camera_front_config)
            except Exception as e:
                self.on_front_camera_error(str(e))

        self.configure_video_files(self.video_files_config)

        if start_preview:
            self.start_preview()
