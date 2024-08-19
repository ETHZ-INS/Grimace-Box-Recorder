import os
import sys
import time
from copy import deepcopy
from pathlib import Path
from typing import Optional, Dict, List, Tuple

import cv2
import torch
from PySide6.QtCore import QObject, Signal, QTimer, QThread
from ultralytics import YOLO

from app.analysis.grimace_analyzer_v1 import GrimaceAnalyzerV1
from app.analysis.grimace_results_writer import GrimaceResultWriter
from app.config.camera import CameraConfig
from app.config.grimace import GrimaceConfig
from app.config.recording import RecordingConfig
from app.config.video_files import VideoFilesConfig
from app.dataflow.qlist import QList
from app.dataflow.qqueue import QQueue
from app.dataflow.qvariable import QVariable
from app.recording.new_dual_video_recorder import DualCameraRecorder, build_camera_source
from app.recording.recording_context import RecordingContext
from app.recording.video_writer import BufferVideoWriter
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
    "frame_quality": models_folder / "mock_frame_quality.pt",
    "face_cropper": models_folder / "mock_face_cropper.pt",
    "grimace_scorer": models_folder / "mock_grimace_scorer.pt"
}

super_scorer_model_files = {
    "frame_quality": models_folder / "frame_quality.pt",
    "face_cropper": models_folder / "face_cropper.pt",
    "grimace_scorer": models_folder / "grimace_scorer.pt",
    "top_pose_estimator": models_folder / "top_pose_estimator.pt",
}

# TODO: After loading config, ready to record despite cameras not found
# TODO: When both cameras disconnect at once, they show different errors
#  ("device with serial number ... not found" vs "camera is not conneced"

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

        self.recording_number = 1

        self.top_video_file: Optional[str] = None
        self.front_video_file: Optional[str] = None
        self.grimace_results_file: Optional[str] = None
        self.top_timestamps_file: Optional[str] = None
        self.front_timestamps_file: Optional[str] = None

        self.frame_quality_scorer = None
        self.face_cropper = None
        self.grimace_scorer = None
        self.top_pose_estimator = None

        self.camera_recorder = DualCameraRecorder()
        self.camera_recorder.setPriority(QThread.Priority.HighestPriority)
        self.camera_recorder.stop_signal.connect(self.stop_recording)
        self.camera_recorder.top_error_signal.connect(self.on_top_camera_error)
        self.camera_recorder.front_error_signal.connect(self.on_front_camera_error)

        self.recording_context = None

        self.top_video_buffer: Optional[QQueue] = None
        self.front_video_buffer: Optional[QQueue] = None
        self.grimace_input_buffer: Optional[QQueue] = None
        self.grimace_output_buffer: Optional[QQueue] = None

        self.grimace_results_list = QList()

        self.top_video_writer = None
        self.front_video_writer = None

        self.grimace_analyzer = None
        self.grimace_results_writer = None

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

    def construct_file(self, target_directory: str, template: str, recording_number: int, timestamp: str) -> str:
        filename = template.format(recording_number=recording_number, start_time=timestamp)
        video_file = Path(target_directory) / filename
        return str(video_file)

    @Trace.trace(logger)
    def construct_files(self, video_files_config: VideoFilesConfig) -> Tuple:
        naming_mode = video_files_config.naming_mode
        target_directory = video_files_config.target_directory
        if naming_mode is None or target_directory is None:
            return None, None, None, None, None

        top_video_file = None
        front_video_file = None
        grimace_results_file = None
        top_timestamps_file = None
        front_timestamps_file = None

        top_video_file_template = video_files_config.top_templates.get(naming_mode)
        front_video_file_template = video_files_config.front_templates.get(naming_mode)
        grimace_results_file_template = video_files_config.grimace_results_templates.get(naming_mode)

        top_timestamps_template = top_video_file_template[:-4] + ".csv"
        front_timestamps_template = front_video_file_template[:-4] + ".csv"

        timestamp = time.strftime("%Y%m%d%H%M%S")

        templates = [top_video_file_template, front_video_file_template, grimace_results_file_template]
        templates += [top_timestamps_template, front_timestamps_template]
        recording_number = self.find_next_recording_number(target_directory, templates, timestamp, self.recording_number)

        self.recording_number = recording_number
        logger.info("Setting recording_number=%s", self.recording_number)

        if top_video_file_template is not None:
            top_video_file = self.construct_file(target_directory, top_video_file_template,
                                                 recording_number, timestamp)

        if front_video_file_template is not None:
            front_video_file = self.construct_file(target_directory, front_video_file_template,
                                                   recording_number, timestamp)

        if grimace_results_file_template is not None:
            grimace_results_file = self.construct_file(target_directory, grimace_results_file_template,
                                                       recording_number, timestamp)

        if top_timestamps_template is not None:
            top_timestamps_file = self.construct_file(target_directory, top_timestamps_template,
                                                      recording_number, timestamp)

        if front_timestamps_template is not None:
            front_timestamps_file = self.construct_file(target_directory, front_timestamps_template,
                                                        recording_number, timestamp)

        return top_video_file, front_video_file, grimace_results_file, top_timestamps_file, front_timestamps_file

    @Trace.trace(logger)
    def configure_video_files(self, video_files_config: Optional[VideoFilesConfig]):
        self.video_files_config = deepcopy(video_files_config)

        files = self.construct_files(video_files_config)
        self.top_video_file, self.front_video_file, self.grimace_results_file = files[:3]
        self.top_timestamps_file, self.front_timestamps_file = files[3:]

        logger.info("Setting top_video_file=%s", self.top_video_file)
        logger.info("Setting front_video_file=%s", self.front_video_file)
        logger.info("Setting grimace_results_file=%s", self.grimace_results_file)
        logger.info("Setting top_timestamps_file=%s", self.top_timestamps_file)
        logger.info("Setting front_timestamps_file=%s", self.front_timestamps_file)

        self.overview_changed_signal.emit()

    @Trace.trace(logger)
    def configure_top_camera(self, camera_config: Optional[CameraConfig], start: bool = True):
        self.camera_top_config = deepcopy(camera_config)
        logger.info("Setting Camera Top Config: %s", self.camera_top_config)

        camera_ready = True
        if camera_config.camera_type == "Pylon" and camera_config.camera_id is None:
            camera_ready = False
        elif camera_config.camera_type == "Video File" and camera_config.video_file is None:
            camera_ready = False

        if camera_ready:
            source = build_camera_source(camera_config)
            self.camera_recorder.set_top_camera(
                source, start=start
            )
            self.camera_recorder.top_camera.set_preview_buffer(self.preview_buffer_top)
        else:
            self.camera_recorder.set_top_camera(None)

        self.overview_changed_signal.emit()

    @Trace.trace(logger)
    def configure_front_camera(self, camera_config: Optional[CameraConfig], start: bool = True):
        self.camera_front_config = deepcopy(camera_config)
        logger.info("Setting Camera Front Config: %s", self.camera_front_config)

        camera_ready = True
        if camera_config.camera_type == "Pylon" and camera_config.camera_id is None:
            camera_ready = False
        elif camera_config.camera_type == "Video File" and camera_config.video_file is None:
            camera_ready = False

        if camera_ready:
            source = build_camera_source(camera_config)
            self.camera_recorder.set_front_camera(
                source, start=start
            )
            self.camera_recorder.front_camera.set_preview_buffer(self.preview_buffer_front)
        else:
            self.camera_recorder.set_front_camera(None)

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

        if self.grimace_config.grimace_model == "V1 - SuperScorer":
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

            #top_pose_estimator_model_base = YOLO(model_files["top_pose_estimator"])
            #top_pose_estimator_model_base.to(grimace_config.face_cropper_device)
            #self.top_pose_estimator = PoseModel(top_pose_estimator_model_base, device="cuda")
            #self.camera_recorder.top_pose_estimator = self.top_pose_estimator
        else:
            self.frame_quality_scorer = None
            self.face_cropper = None
            self.grimace_scorer = None

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
        top_camera_buffer_fill_level = 0.0
        front_camera_buffer_fill_level = 0.0
        top_video_buffer_fill_level = 0.0
        front_video_buffer_fill_level = 0.0
        grimace_input_buffer_fill_level = 0.0
        grimace_output_buffer_fill_level = 0.0

        if self.camera_recorder is not None:
            if self.camera_recorder.top_camera is not None:
                warning = None
                top_camera_buffer_fill_level = self.camera_recorder.top_camera.buffer_fill_level
                if top_camera_buffer_fill_level > 0.1:
                    warning = f"Top camera buffer fill level: {top_camera_buffer_fill_level * 100:.2f}%"
                warnings_changed |= self.set_warning("top_camera_buffer_fill", warning)

                warning = None
                fps = self.camera_recorder.top_camera.fps
                if fps < self.camera_top_config.fps * 0.9:
                    warning = f"Top camera FPS: {fps:.2f} (expected {self.camera_top_config.fps})"
                warnings_changed |= self.set_warning("top_camera_fps", warning)

                warning = None
                dropped_frames = self.camera_recorder.top_camera.dropped_frames
                if dropped_frames > 0:
                    warning = f"Top camera dropped {dropped_frames} frames"
                warnings_changed |= self.set_warning("top_camera_dropped_frames", warning)

            if self.camera_recorder.front_camera is not None:
                warning = None
                front_camera_buffer_fill_level = self.camera_recorder.front_camera.buffer_fill_level
                if front_camera_buffer_fill_level > 0.1:
                    warning = f"Front camera buffer fill level: {front_camera_buffer_fill_level * 100:.2f}%"
                warnings_changed |= self.set_warning("front_camera_buffer_fill", warning)

                warning = None
                fps = self.camera_recorder.front_camera.fps
                if fps < self.camera_front_config.fps * 0.9:
                    warning = f"Front camera FPS: {fps:.2f} (expected {self.camera_front_config.fps})"
                warnings_changed |= self.set_warning("front_camera_fps", warning)

                warning = None
                dropped_frames = self.camera_recorder.front_camera.dropped_frames
                if dropped_frames > 0:
                    warning = f"Front camera dropped {dropped_frames} frames"
                warnings_changed |= self.set_warning("front_camera_dropped_frames", warning)

        if self.top_video_buffer is not None:
            warning = None
            top_video_buffer_fill_level = self.top_video_buffer.get_fill_level()
            if top_video_buffer_fill_level > 0.1:
                warning = f"Top video buffer fill level: {top_video_buffer_fill_level * 100:.2f}%"
            warnings_changed |= self.set_warning("top_video_buffer_fill", warning)
        if self.front_video_buffer is not None:
            warning = None
            front_video_buffer_fill_level = self.front_video_buffer.get_fill_level()
            if front_video_buffer_fill_level > 0.1:
                warning = f"Front video buffer fill level: {front_video_buffer_fill_level * 100:.2f}%"
            warnings_changed |= self.set_warning("front_video_buffer_fill", warning)

        if self.grimace_input_buffer is not None:
            warning = None
            grimace_input_buffer_fill_level = self.grimace_input_buffer.get_fill_level()
            if grimace_input_buffer_fill_level > 0.1:
                warning = f"Grimace analysis buffer fill level: {grimace_input_buffer_fill_level * 100:.2f}%"
            warnings_changed |= self.set_warning("grimace_input_buffer_fill", warning)
        if self.grimace_output_buffer is not None:
            warning = None
            grimace_output_buffer_fill_level = self.grimace_output_buffer.get_fill_level()
            if grimace_output_buffer_fill_level > 0.1:
                warning = f"Grimace results buffer fill level: {grimace_output_buffer_fill_level * 100:.2f}%"
            warnings_changed |= self.set_warning("grimace_output_buffer_fill", warning)

        if warnings_changed:
            self.warnings_changed_signal.emit()

        # Stop analysis if any buffer is dangerously full to save resources for recording
        if self.analysis_running:
            if top_camera_buffer_fill_level > 0.7:
                self.on_analysis_error("Top camera buffer almost full - stopping analysis to save resources")
            elif front_camera_buffer_fill_level > 0.7:
                self.on_analysis_error("Front camera buffer almost full - stopping analysis to save resources")
            elif top_video_buffer_fill_level > 0.7:
                self.on_analysis_error("Top video buffer almost full - stopping analysis to save resources")
            elif front_video_buffer_fill_level > 0.7:
                self.on_analysis_error("Front video buffer almost full - stopping analysis to save resources")
            elif grimace_input_buffer_fill_level > 0.99 or grimace_output_buffer_fill_level > 0.99:
                self.on_analysis_error("Grimace analysis buffer almost full - stopping analysis to save resources")

    @Trace.trace(logger)
    def prepare_recording(self):
        self.configure_video_files(self.video_files_config)

        fourcc = cv2.VideoWriter.fourcc(*self.recording_config.codec)
        top_video_writer = cv2.VideoWriter(
            self.top_video_file, fourcc, self.camera_top_config.fps,
            (self.camera_recorder.top_camera.get_width(), self.camera_recorder.top_camera.get_height()), isColor=False)
        front_video_writer = cv2.VideoWriter(
            self.front_video_file, fourcc, self.camera_front_config.fps,
            (self.camera_recorder.front_camera.get_width(), self.camera_recorder.front_camera.get_height()), isColor=False)

        self.top_video_buffer = QQueue(1000)
        self.front_video_buffer = QQueue(1000)

        self.top_video_writer = BufferVideoWriter(top_video_writer, self.top_video_buffer,
                                                  timestamp_file=Path(self.top_timestamps_file))
        self.front_video_writer = BufferVideoWriter(front_video_writer, self.front_video_buffer,
                                                    timestamp_file=Path(self.front_timestamps_file))

        self.top_video_writer.error_signal.connect(self.on_recording_error)
        self.front_video_writer.error_signal.connect(self.on_recording_error)

        if self.grimace_config.enabled:
            self.grimace_input_buffer = QQueue(1000)
            self.grimace_output_buffer = QQueue(1000)

            frames_per_interval = int(self.grimace_config.frame_interval * self.camera_front_config.fps)

            self.grimace_analyzer = GrimaceAnalyzerV1(self.frame_quality_scorer, self.face_cropper, self.grimace_scorer,
                                                      self.grimace_input_buffer, self.grimace_output_buffer,
                                                      self.grimace_results_list,
                                                      batch_size=16, min_score=4.75 / 6,
                                                      frames_per_interval=frames_per_interval)

            self.grimace_results_writer = GrimaceResultWriter(Path(self.grimace_results_file),
                                                              self.grimace_output_buffer)

            self.grimace_analyzer.error_signal.connect(self.on_analysis_error)
            self.grimace_results_writer.error_signal.connect(self.on_analysis_error)

        recording_duration = self.recording_config.duration if self.recording_config.mode == "Timed" else None
        self.recording_context = RecordingContext(recording_duration)

        self.overview_changed_signal.emit()

    @Trace.trace(logger)
    def start_preview(self):
        if self.recording_running:
            return

        if self.camera_recorder.running:
            self.camera_recorder.stop()
            self.camera_recorder.wait()

        if self.camera_recorder.top_camera is not None or self.camera_recorder.front_camera is not None:
            self.camera_recorder.start()

    @Trace.trace(logger)
    def start_recording(self):
        self.analysis_error = None
        self.recording_error = None
        self.warnings = {}

        self.recording_running = True
        if self.grimace_config.enabled:
            self.analysis_running = True

        if self.camera_recorder.isRunning():
            self.camera_recorder.stop()
            self.camera_recorder.wait()

        if self.camera_recorder.top_camera is not None:
            self.camera_recorder.top_camera.set_video_buffer(self.top_video_buffer)
        if self.camera_recorder.front_camera is not None:
            self.camera_recorder.front_camera.set_video_buffer(self.front_video_buffer)
            if self.grimace_config.enabled:
                self.camera_recorder.front_camera.set_grimace_buffer(self.grimace_input_buffer)

        self.camera_recorder.set_recording_context(self.recording_context)

        if self.grimace_config.enabled:
            self.grimace_results_list.clear()

        self.top_video_writer.start()
        self.front_video_writer.start()

        if self.grimace_config.enabled:
            self.grimace_analyzer.start()
            self.grimace_results_writer.start()

        self.camera_recorder.start()

        self.overview_changed_signal.emit()
        self.recording_started_signal.emit()

    @Trace.trace(logger)
    def stop_recording(self, start_preview: bool = True):
        if not self.recording_running:
            return

        self.camera_recorder.stop()
        self.camera_recorder.wait()

        self.camera_recorder.top_camera.set_video_buffer(None)
        self.camera_recorder.front_camera.set_video_buffer(None)
        self.camera_recorder.front_camera.set_grimace_buffer(None)

        self.camera_recorder.set_recording_context(None)
        self.recording_context.stop()

        self.top_video_writer.wait()
        self.front_video_writer.wait()

        if self.grimace_config.enabled:
            self.grimace_analyzer.wait()
            self.grimace_results_writer.wait()

        self.recording_running = False

        self.configure_video_files(self.video_files_config)

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
        if self.grimace_analyzer is not None:
            self.grimace_analyzer.stop()

        if self.grimace_results_writer is not None:
            self.grimace_results_writer.stop()

        # Set grimace buffers to void so incoming items are simply ignored
        if self.grimace_input_buffer is not None:
            self.grimace_input_buffer.set_void()
        if self.grimace_output_buffer is not None:
            self.grimace_output_buffer.set_void()

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
        if self.camera_recorder is not None:
            self.camera_recorder.stop()

        if self.top_video_writer is not None:
            self.top_video_writer.stop()

        if self.front_video_writer is not None:
            self.front_video_writer.stop()

        if self.grimace_analyzer is not None:
            self.grimace_analyzer.stop()

        if self.grimace_results_writer is not None:
            self.grimace_results_writer.stop()

        if self.recording_context is not None:
            self.recording_context.stop()

        if self.camera_recorder is not None:
            self.camera_recorder.wait()

        if self.top_video_writer is not None:
            self.top_video_writer.wait()

        if self.front_video_writer is not None:
            self.front_video_writer.wait()

        if self.grimace_analyzer is not None:
            self.grimace_analyzer.wait()

        if self.grimace_results_writer is not None:
            self.grimace_results_writer.wait()

        if self.camera_recorder is not None:
            if self.camera_recorder.top_camera is not None:
                self.camera_recorder.top_camera.set_video_buffer(None)
                self.camera_recorder.set_top_camera(None, start=False)

            if self.camera_recorder.front_camera is not None:
                self.camera_recorder.front_camera.set_video_buffer(None)
                self.camera_recorder.front_camera.set_grimace_buffer(None)
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
