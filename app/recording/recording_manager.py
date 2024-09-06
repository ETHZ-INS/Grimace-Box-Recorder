import os
import sys
import time
from copy import deepcopy
from pathlib import Path, PurePath
from typing import Optional, Dict, List, Literal

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
from app.recording.camera_recorder.source.base_source import CameraSource
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


class Recording:
    """
    Represents a recording that is ready to run. May also be a preview that does not save any files.
    """
    def __init__(self, camera_recorder: DualCameraRecorder, top_video_pipeline: VideoPipeline,
                 front_video_pipeline: VideoPipeline, recording_context: RecordingContext | None):
        self.camera_recorder = camera_recorder
        self.top_video_pipeline = top_video_pipeline
        self.front_video_pipeline = front_video_pipeline
        self.recording_context = recording_context

        self.running = False
        self.analysis_running = False

    @Trace.trace(logger)
    def start(self):
        if self.running:
            # TODO: Should this be an error? In production it might be better to just ignore/log it
            raise ValueError("Recording already running")

        # TODO: stop preview before calling start
        #self.stop_preview()

        # TODO: Stop before calling start
        #if self.camera_recorder.isRunning():
        #    self.camera_recorder.stop()
        #    self.camera_recorder.wait()

        self.running = True
        # TODO: Should analysis_running always be true or only when actually running analysis?
        self.analysis_running = True

        self.camera_recorder.top_camera.set_video_buffer(self.top_video_pipeline.input_queue)
        self.camera_recorder.front_camera.set_video_buffer(self.front_video_pipeline.input_queue)

        self.camera_recorder.set_recording_context(self.recording_context)

        self.top_video_pipeline.start()
        self.front_video_pipeline.start()

        self.camera_recorder.start()

    @Trace.trace(logger)
    def stop(self):
        if not self.running:
            # TODO: Should this be an error?

            raise ValueError("Recording not running")

        # Stop the recorder to stop the flow of frames through the pipeline
        # The other parts of the pipeline will stop themselves when they're done processing the remaining frames
        self.camera_recorder.stop()
        self.camera_recorder.wait()

        # Disconnect the pipelines from the camera recorder
        self.camera_recorder.top_camera.set_video_buffer(None)
        self.camera_recorder.front_camera.set_video_buffer(None)

        # TODO: Does this order make sense?
        self.camera_recorder.set_recording_context(None)
        if self.recording_context is not None:
            self.recording_context.stop()

        # TODO: Some kind of loading screen while waiting for the pipelines to stop?

#        # TODO: Do some kind of warning if it timed out
#        if not self.top_video_pipeline.wait(2000):
#            logger.error("Top video pipeline did not stop after 2 seconds")
#            self.top_video_pipeline.stop()
#            if not self.top_video_pipeline.wait(2000):
#                logger.error("Top video pipeline did not stop after notifying and another 2 seconds")
#
#        if not self.front_video_pipeline.wait(2000):
#            logger.error("Front video pipeline did not stop after 2 seconds")
#            self.front_video_pipeline.stop()
#            if not self.front_video_pipeline.wait(2000):
#                logger.error("Front video pipeline did not stop after notifying and another 2 seconds")

        # TODO: Is it ok to just wait without timeout? I think it should be the user's decision to wait or close
        #  the application if it freezes in case the results are too important to lose
        self.top_video_pipeline.wait()
        self.front_video_pipeline.wait()

        self.running = False
        self.analysis_running = False

    @Trace.trace(logger, level=logging.WARNING)
    def kill_analysis(self):
        # Only stop grimace analysis so the recording, which is much more important, may still be able to finish
        self.top_video_pipeline.stop_analysis()
        self.front_video_pipeline.stop_analysis()

        self.analysis_running = False


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

    def get_not_ready_reason(self) -> Optional[str]:
        if self.video_file is None:
            return "Video file not configured"

        if self.timestamp_file is None:
            return "Timestamp file not configured"

        if self.fourcc is None:
            return "Video codec not configured"

        # Width, height and fps are not checked because they need the camera source,
        # which is only built when starting the recording

        return None


class RecordingBuilder(QObject):
    def __init__(self):
        super().__init__()

        self.recording_number: int = 1

        self.video_files_config = VideoFilesConfig()
        self.top_camera_config = CameraConfig()
        self.front_camera_config = CameraConfig()
        self.recording_config = RecordingConfig()
        self.grimace_config = GrimaceConfig()
        self.pose_config = PoseTopConfig()

        self.recording_duration: float | None = None

        self.top_video_writer_builder: VideoWriterBuilder = VideoWriterBuilder()
        self.front_video_writer_builder: VideoWriterBuilder = VideoWriterBuilder()

        self.top_video_pipeline_builder = TopVideoPipelineBuilder()
        self.front_video_pipeline_builder = FrontVideoPipelineBuilder()

    def set_top_preview(self, top_preview: QVariable):
        self.top_video_pipeline_builder.set_preview_queue(top_preview)
        return self

    def set_front_preview(self, front_preview: QVariable):
        self.front_video_pipeline_builder.set_preview_queue(front_preview)
        return self

    def set_grimace_results_list(self, grimace_results_list: QList):
        self.front_video_pipeline_builder.set_results_preview_queue(grimace_results_list)
        return self

    def configure_video_files(self, video_files_config: VideoFilesConfig):
        self.video_files_config = deepcopy(video_files_config)

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

        top_video_file = file_builder.construct_file("top_video")
        front_video_file = file_builder.construct_file("front_video")
        grimace_results_file = file_builder.construct_file("grimace_results")
        top_timestamps_file = file_builder.construct_file("top_timestamps")
        front_timestamps_file = file_builder.construct_file("front_timestamps")
        pose_results_file = file_builder.construct_file("pose_results")

        logger.info("Setting top_video_file=%s", top_video_file)
        logger.info("Setting front_video_file=%s", front_video_file)
        logger.info("Setting grimace_results_file=%s", grimace_results_file)
        logger.info("Setting top_timestamps_file=%s", top_timestamps_file)
        logger.info("Setting front_timestamps_file=%s", front_timestamps_file)
        logger.info("Setting pose_results_file=%s", pose_results_file)

        self.top_video_writer_builder.set_video_file(top_video_file)
        self.top_video_writer_builder.set_timestamp_file(top_timestamps_file)

        self.front_video_writer_builder.set_video_file(front_video_file)
        self.front_video_writer_builder.set_timestamp_file(front_timestamps_file)

        self.top_video_pipeline_builder.set_pose_results_file(pose_results_file)
        self.front_video_pipeline_builder.set_grimace_results_file(grimace_results_file)

        return self

    def configure_top_camera(self, camera_config: CameraConfig):
        self.top_camera_config = deepcopy(camera_config)
        return self

    def configure_front_camera(self, camera_config: CameraConfig):
        self.front_camera_config = deepcopy(camera_config)
        return self

    def configure_recording(self, recording_config: RecordingConfig):
        self.recording_config = deepcopy(recording_config)
        fourcc = cv2.VideoWriter.fourcc(*recording_config.codec)
        print(fourcc)
        self.top_video_writer_builder.set_fourcc(fourcc)
        self.front_video_writer_builder.set_fourcc(fourcc)

        self.recording_duration = self.recording_config.duration if self.recording_config.mode == "Timed" else None

        return self

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
            grimace_enabled = True
            if self.grimace_config.frame_quality_device is not None:
                frame_quality_model = FrameQualityModel(device=grimace_config.frame_quality_device)
                model_weights = torch.load(model_files["frame_quality"], map_location=lambda storage, loc: storage)
                frame_quality_model.load_state_dict(model_weights)
                frame_quality_scorer = FrameQualityScorer(frame_quality_model)
            else:
                frame_quality_scorer = None

            if self.grimace_config.face_cropper_device is not None:
                face_cropper_model_base = YOLO(model_files["face_cropper"])
                face_cropper_model_base.to(grimace_config.face_cropper_device)
                face_cropper_model = FrameCropperModel(face_cropper_model_base, device=grimace_config.face_cropper_device)
                # TODO: Decide on confidence threshold or make it configurable
                face_cropper = FrameCropper(face_cropper_model, padding=0.05, confidence_threshold=0.9)
            else:
                face_cropper = None

            if self.grimace_config.grimace_scoring_device is not None:
                grimace_scorer_model = GrimaceScoreModel(device=grimace_config.grimace_scoring_device)
                model_weights = torch.load(model_files["grimace_scorer"], map_location=lambda storage, loc: storage)
                grimace_scorer_model.load_state_dict(model_weights)
                grimace_scorer = GrimaceScorer(grimace_scorer_model)
            else:
                grimace_scorer = None
        else:
            grimace_enabled = False
            frame_quality_scorer = None
            face_cropper = None
            grimace_scorer = None

        self.front_video_pipeline_builder.set_grimace_enabled(grimace_enabled)
        self.front_video_pipeline_builder.set_frame_quality_scorer(frame_quality_scorer)
        self.front_video_pipeline_builder.set_face_cropper(face_cropper)
        self.front_video_pipeline_builder.set_grimace_scorer(grimace_scorer)

        return self

    def configure_pose_estimation(self, pose_config: PoseTopConfig):
        self.pose_config = deepcopy(pose_config)
        logger.info("Setting Pose Config: %s", self.pose_config)

        if self.pose_config.pose_model == "V1 - GrimaceBoxTop":
            model_files = super_scorer_model_files
        elif self.pose_config.pose_model == "Demo (Fake Mouse)":
            model_files = demo_model_files
        else:
            raise ValueError(f"Unknown model version: {self.pose_config.pose_model}")

        # TODO: This can be cleaned up (pose_device will never be None)
        if self.pose_config is not None and self.pose_config.enabled and self.pose_config.pose_device is not None:
            top_pose_enabled = True
            top_pose_preview_enabled = self.pose_config.show_preview

            top_pose_estimator_model_base = YOLO(model_files["top_pose_estimator"])
            top_pose_estimator_model_base.to(self.pose_config.pose_device)
            top_pose_estimator_model = PoseModel(top_pose_estimator_model_base, device=self.pose_config.pose_device)

            with open(model_files["top_pose_keypoints"], "r") as f:
                top_pose_keypoints = [line.strip() for line in f]

        else:
            top_pose_enabled = False
            top_pose_preview_enabled = False
            top_pose_estimator_model = None
            top_pose_keypoints = None

        self.top_video_pipeline_builder.set_pose_enabled(top_pose_enabled)
        self.top_video_pipeline_builder.set_pose_preview_enabled(top_pose_preview_enabled)
        self.top_video_pipeline_builder.set_pose_estimator_model(top_pose_estimator_model)
        self.top_video_pipeline_builder.set_top_pose_keypoints(top_pose_keypoints)

        return self

    def build_top_camera(self) -> CameraSource:
        if self.top_camera_config is None:
            raise ValueError("Top camera not configured")
        return build_camera_source(self.top_camera_config)

    def build_front_camera(self) -> CameraSource:
        if self.front_camera_config is None:
            raise ValueError("Front camera not configured")
        return build_camera_source(self.front_camera_config)

    def build_top_video_pipeline(self, camera: CameraSource) -> VideoPipeline:
        self.top_video_writer_builder.set_width(camera.get_width())
        self.top_video_writer_builder.set_height(camera.get_height())
        self.top_video_writer_builder.set_fps(camera.get_fps())
        video_writer = self.top_video_writer_builder.build()
        self.top_video_pipeline_builder.set_video_writer(video_writer)

        self.top_video_pipeline_builder.set_target_frame_rate(camera.get_fps())

        return self.top_video_pipeline_builder.build()

    def build_front_video_pipeline(self, camera: CameraSource) -> VideoPipeline:
        self.front_video_writer_builder.set_width(camera.get_width())
        self.front_video_writer_builder.set_height(camera.get_height())
        self.front_video_writer_builder.set_fps(camera.get_fps())
        video_writer = self.front_video_writer_builder.build()
        self.front_video_pipeline_builder.set_video_writer(video_writer)

        if self.grimace_config is not None and self.grimace_config.enabled:
            frames_per_interval = round(self.grimace_config.frame_interval * camera.get_fps())
            self.front_video_pipeline_builder.set_frames_per_interval(frames_per_interval)

        return self.front_video_pipeline_builder.build()

    def build(self, camera_recorder: DualCameraRecorder, preview: bool = False) -> Recording:
        top_camera = self.build_top_camera()
        front_camera = self.build_front_camera()

        if preview:
            top_video_pipeline = self.top_video_pipeline_builder.build(preview=True)
            front_video_pipeline = self.front_video_pipeline_builder.build(preview=True)
            recording_context = None
        else:
            top_video_pipeline = self.build_top_video_pipeline(top_camera)
            front_video_pipeline = self.build_front_video_pipeline(front_camera)

            recording_context = RecordingContext(self.recording_duration)

        camera_recorder.set_top_camera(top_camera)
        camera_recorder.set_front_camera(front_camera)

        return Recording(camera_recorder, top_video_pipeline, front_video_pipeline, recording_context)

    def get_not_ready_reason(self) -> Optional[str]:
        top_video_writer_not_ready_reason = self.top_video_writer_builder.get_not_ready_reason()
        if top_video_writer_not_ready_reason is not None:
            return f"Top video: {top_video_writer_not_ready_reason}"

        front_video_writer_not_ready_reason = self.front_video_writer_builder.get_not_ready_reason()
        if front_video_writer_not_ready_reason is not None:
            return f"Front video: {front_video_writer_not_ready_reason}"

        top_video_pipeline_not_ready_reason = self.top_video_pipeline_builder.get_not_ready_reason()
        if top_video_pipeline_not_ready_reason is not None:
            return f"Top video: {top_video_pipeline_not_ready_reason}"

        front_video_pipeline_not_ready_reason = self.front_video_pipeline_builder.get_not_ready_reason()
        if front_video_pipeline_not_ready_reason is not None:
            return f"Front video: {front_video_pipeline_not_ready_reason}"

        # TODO: I don't think the individual config values need to be checked for None

        if self.recording_number is None:
            return "Recording number not set"

        if self.top_camera_config is None:
            return "Top camera not configured"

        if self.front_camera_config is None:
            return "Front camera not configured"

        if self.top_camera_config.camera_type == "Pylon" and self.top_camera_config.camera_id is None:
            return "Top camera device not selected"
        elif self.top_camera_config.camera_type == "Video File" and self.top_camera_config.video_file is None:
            return "Top video file not selected"

        if self.front_camera_config.camera_type == "Pylon" and self.front_camera_config.camera_id is None:
            return "Front camera device not selected"
        elif self.front_camera_config.camera_type == "Video File" and self.front_camera_config.video_file is None:
            return "Front video file not selected"

        if self.recording_config is None:
            return "Recording not configured"

        if self.video_files_config is None:
            return "Video files not configured"

        if self.top_camera_config.fps is None:
            return "Top camera FPS not configured"

        if self.front_camera_config.fps is None:
            return "Front camera FPS not configured"

        if self.recording_config.mode is None:
            return "Recording mode not configured"

        if self.recording_duration is None:
            return "Recording duration not properly configured"

        if self.recording_config.codec is None:
            return "Codec not configured"

        if self.grimace_config.enabled is None:
            return "Grimace scoring not configured"

        if self.grimace_config.enabled:
            if self.grimace_config.grimace_model is None:
                return "Grimace model not configured"
            if self.grimace_config.frame_interval is None:
                return "Frame interval not configured"
            if self.grimace_config.frame_quality_device is None:
                return "Frame quality device not configured"
            if self.grimace_config.face_cropper_device is None:
                return "Face cropper device not configured"
            if self.grimace_config.grimace_scoring_device is None:
                return "Grimace scoring device not configured"

        if self.pose_config.enabled is None:
            return "Pose tracking not configured"

        if self.pose_config.enabled:
            if self.pose_config.pose_model is None:
                return "Pose model not configured"
            if self.pose_config.pose_device is None:
                return "Pose device not configured"


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

        self.recording_builder = RecordingBuilder()
        self.recording_builder.set_top_preview(preview_buffer_top)
        self.recording_builder.set_front_preview(preview_buffer_front)

        camera_identifier_model = CameraIdentifierModel(device="cpu")
        # TODO: What is map_location?
        model_weights = torch.load(super_scorer_model_files["camera_identifier"], map_location=lambda storage, loc: storage)
        camera_identifier_model.load_state_dict(model_weights)
        self.camera_identifier = CameraIdentifier(camera_identifier_model)

        self.camera_recorder = DualCameraRecorder(self.camera_identifier)
        self.camera_recorder.setPriority(QThread.Priority.HighestPriority)
        self.camera_recorder.stop_signal.connect(self.stop)
        self.camera_recorder.top_error_signal.connect(self.on_top_camera_error)
        self.camera_recorder.front_error_signal.connect(self.on_front_camera_error)

        self.grimace_results_list = QList()
        self.recording_builder.set_grimace_results_list(self.grimace_results_list)

        self.health_timer = QTimer(self)
        self.health_timer.timeout.connect(self.check_health)
        self.health_timer.start(1000)

        self.recording_error: Optional[str] = None
        self.analysis_error: Optional[str] = None
        self.warnings: Dict[str, str] = {}

        self.recording: Recording | None = None
        self.preview: bool = False

    @Trace.trace(logger)
    def configure_video_files(self, video_files_config: Optional[VideoFilesConfig]):
        self.recording_builder.configure_video_files(video_files_config)
        self.overview_changed_signal.emit()

    @Trace.trace(logger)
    def configure_top_camera(self, camera_config: Optional[CameraConfig]):
        self.recording_builder.configure_top_camera(camera_config)
        self.overview_changed_signal.emit()

    @Trace.trace(logger)
    def configure_front_camera(self, camera_config: Optional[CameraConfig]):
        self.recording_builder.configure_front_camera(camera_config)
        self.overview_changed_signal.emit()

    @Trace.trace(logger)
    def configure_recording(self, recording_config: RecordingConfig):
        self.recording_builder.configure_recording(recording_config)
        self.overview_changed_signal.emit()

    @Trace.trace(logger)
    def configure_grimace(self, grimace_config: GrimaceConfig):
        self.recording_builder.configure_grimace(grimace_config)
        self.overview_changed_signal.emit()

    @Trace.trace(logger)
    def configure_pose_tracking(self, pose_config: PoseTopConfig):
        self.recording_builder.configure_pose_estimation(pose_config)
        self.overview_changed_signal.emit()

    @Trace.trace(logger)
    def reset_error(self):
        self.recording_error = None
        self.analysis_error = None

    def get_not_ready_reason(self) -> Optional[str]:
        return self.recording_builder.get_not_ready_reason()

    def get_warnings(self) -> List[str]:
        warnings = []
        if self.analysis_error is not None:
            analysis_warning = (f"An error occurred in the live analysis, so it was stopped.  \n"
                                f"The recording may still continue.  \n"
                                f"Cause: {self.analysis_error}")
            warnings.append(analysis_warning)
        # TODO: Check if FPS is the same for both cameras. Or whether this is necessary
        #if self.camera_top_config is not None and self.camera_front_config is not None:
        #    if self.camera_top_config.fps is not None and self.camera_front_config.fps is not None:
        #        if self.camera_top_config.fps != self.camera_front_config.fps:
        #            warnings.append("Top and front camera FPS are different")
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

        if self.recording is not None:
            if self.recording.top_video_pipeline is not None:
                top_video_pipeline_report = self.recording.top_video_pipeline.check_health(prefix="top_")
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

            if self.recording.front_video_pipeline is not None:
                front_video_pipeline_report = self.recording.front_video_pipeline.check_health(prefix="front_")
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

    @Trace.trace(logger)
    def start_preview(self):
        if self.recording is not None:
            self.stop()

        self.recording = self.recording_builder.build(self.camera_recorder, preview=True)
        self.recording.start()

    @Trace.trace(logger)
    def start_recording(self):
        self.analysis_error = None
        self.recording_error = None
        self.warnings = {}

        self.recording = self.recording_builder.build(self.camera_recorder)
        self.recording.start()

        self.overview_changed_signal.emit()
        self.recording_started_signal.emit()

    @Trace.trace(logger)
    def stop(self):
        """
        Stops the recording/preview if it is running. Tries to get to a clean state.
        :return:
        """
        if self.recording is None:
            self.preview = False
            return
        if self.recording.running:
            self.recording.stop()
        self.recording = None
        self.preview = False

    @Trace.trace(logger)
    def kill_analysis(self):
        if self.recording is None:
            raise ValueError("Recording not running")

        self.recording.kill_analysis()

        # TODO: Do we need to emit signals here?
        #self.warnings_changed_signal.emit()

    @Trace.trace(logger, level=logging.WARNING)
    def on_recording_error(self, error: str):
        # TODO: Overhaul needed
        self.stop()
        #self.force_stop_recording()
        self.recording_error = error
        self.recording_error_signal.emit(error)

    @Trace.trace(logger, level=logging.WARNING)
    def on_analysis_error(self, error: str):
        # TODO: Overhaul needed
        self.kill_analysis()
        #self.force_stop_analysis()
        self.analysis_error = error
        self.analysis_error_signal.emit(error)
        self.warnings_changed_signal.emit()

    @Trace.trace(logger, level=logging.WARNING)
    def on_top_camera_error(self, error: str):
        # TODO: Overhaul needed
        if self.recording.running:
            self.stop()
            #self.force_stop_recording(kick_top_camera=True)
            self.recording_error = "Top Camera Error: " + error
            self.recording_error_signal.emit(self.recording_error)
        else:
            self.stop()
            #self.force_stop_recording(kick_top_camera=True)
        self.top_camera_error_signal.emit(error)

    @Trace.trace(logger, level=logging.WARNING)
    def on_front_camera_error(self, error: str):
        # TODO: Overhaul needed
        if self.recording.running:
            self.stop()
            #self.force_stop_recording(kick_front_camera=True)
            self.recording_error = "Front Camera Error: " + error
            self.recording_error_signal.emit(self.recording_error)
        else:
            self.stop()
            #self.force_stop_recording(kick_front_camera=True)
        self.front_camera_error_signal.emit(error)
