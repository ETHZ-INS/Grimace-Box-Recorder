import time
from copy import deepcopy
from pathlib import Path
from typing import Optional, Dict, List, Tuple

import cv2
import torch
from PySide6.QtCore import QObject, Signal, QTimer
from ultralytics import YOLO

from app.analysis.grimace_analyzer_v1 import GrimaceAnalyzerV1
from app.analysis.grimace_results_writer import GrimaceResultWriter
from app.config.camera import CameraConfig
from app.config.grimace import GrimaceConfig
from app.config.recording import RecordingConfig
from app.config.video_files import VideoFilesConfig
from app.dataflow.qlist import QList
from app.dataflow.qqueue import QQueue
from app.recording.dual_video_recorder import PylonDualCameraRecorder
from app.recording.recording_context import RecordingContext
from app.recording.video_writer import BufferVideoWriter
from grimace.frame_cropper import FrameCropper
from grimace.frame_cropper_model import FrameCropperModel
from grimace.frame_quality_model import FrameQualityModel
from grimace.frame_quality_scorer import FrameQualityScorer
from grimace.grimace_scorer import GrimaceScorer
from grimace.grimace_scorer_model import GrimaceScoreModel


class RecordingManager(QObject):
    overview_changed = Signal()
    warnings_changed = Signal()
    recording_started = Signal()
    recording_stopped = Signal()
    recording_error = Signal(str)

    def __init__(self):
        super().__init__()
        self.camera_top_config = CameraConfig()
        self.camera_front_config = CameraConfig()
        self.recording_config = RecordingConfig()
        self.video_files_config = VideoFilesConfig()
        self.grimace_config = GrimaceConfig()

        self.recording_number = 1

        self.top_video_file: Optional[str] = None
        self.front_video_file: Optional[str] = None
        self.grimace_results_file: Optional[str] = None

        self.frame_quality_scorer = None
        self.face_cropper = None
        self.grimace_scorer = None

        self.camera_recorder = None

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

        self.health_timer = QTimer(self)
        self.health_timer.timeout.connect(self.check_health)
        self.health_timer.start(1000)

        self.error: Optional[str] = None
        self.warnings: Dict[str, str] = {}

    def find_next_recording_number(self, target_directory: str, templates: List[str], timestamp: str, start: int = 1) -> int:
        if start is None:
            start = 1

        # Find the next recording number that does not have a file
        recording_number = start
        while True:
            for template in templates:
                filename = template.format(recording_number=recording_number, start_time=timestamp)
                video_file = Path(target_directory) / filename
                if video_file.exists():
                    break
            else:
                break
            recording_number += 1
        return recording_number

    def construct_file(self, target_directory: str, template: str, recording_number: int, timestamp: str) -> str:
        filename = template.format(recording_number=recording_number, start_time=timestamp)
        video_file = Path(target_directory) / filename
        return str(video_file)

    def construct_files(self, video_files_config: VideoFilesConfig) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        naming_mode = video_files_config.naming_mode
        target_directory = video_files_config.target_directory
        if naming_mode is None or target_directory is None:
            return None, None, None

        top_video_file = None
        front_video_file = None
        grimace_results_file = None

        top_video_file_template = video_files_config.top_templates.get(naming_mode)
        front_video_file_template = video_files_config.front_templates.get(naming_mode)
        grimace_results_file_template = video_files_config.grimace_results_templates.get(naming_mode)

        recording_number = self.recording_number
        timestamp = time.strftime("%Y%m%d%H%M%S")

        templates = [top_video_file_template, front_video_file_template, grimace_results_file_template]
        recording_number = self.find_next_recording_number(target_directory, templates, timestamp, recording_number)

        if top_video_file_template is not None:
            top_video_file = self.construct_file(target_directory, top_video_file_template,
                                                 recording_number, timestamp)

        if front_video_file_template is not None:
            front_video_file = self.construct_file(target_directory, front_video_file_template,
                                                   recording_number, timestamp)

        if grimace_results_file_template is not None:
            grimace_results_file = self.construct_file(target_directory, grimace_results_file_template,
                                                       recording_number, timestamp)

        return top_video_file, front_video_file, grimace_results_file

    def configure_video_files(self, video_files_config: Optional[VideoFilesConfig]):
        self.video_files_config = deepcopy(video_files_config)

        self.top_video_file, self.front_video_file, self.grimace_results_file = self.construct_files(video_files_config)

        self.error = None
        self.overview_changed.emit()

    def configure_top_camera(self, camera_top_config: Optional[CameraConfig]):
        self.camera_top_config = deepcopy(camera_top_config)
        self.error = None
        self.overview_changed.emit()

    def configure_front_camera(self, camera_front_config: Optional[CameraConfig]):
        self.camera_front_config = deepcopy(camera_front_config)
        self.error = None
        self.overview_changed.emit()

    def configure_recording(self, recording_config: RecordingConfig):
        self.recording_config = deepcopy(recording_config)
        self.error = None
        self.overview_changed.emit()

    def configure_grimace(self, grimace_config: GrimaceConfig):
        self.grimace_config = deepcopy(grimace_config)

        if grimace_config is not None and grimace_config.enabled:
            if self.grimace_config.frame_quality_device is not None:
                frame_quality_model = FrameQualityModel(device=grimace_config.frame_quality_device)
                model_weights = torch.load(Path("models/frame_quality.pt"), map_location=lambda storage, loc: storage)
                frame_quality_model.load_state_dict(model_weights)
                self.frame_quality_scorer = FrameQualityScorer(frame_quality_model)
            else:
                self.frame_quality_scorer = None

            if self.grimace_config.face_cropper_device is not None:
                face_cropper_model_base = YOLO('models/face_cropper.pt')
                face_cropper_model_base.to(grimace_config.face_cropper_device)
                face_cropper_model = FrameCropperModel(face_cropper_model_base, device=grimace_config.face_cropper_device)
                self.face_cropper = FrameCropper(face_cropper_model, padding=0.05, confidence_threshold=0.9)
            else:
                self.face_cropper = None

            if self.grimace_config.grimace_scoring_device is not None:
                grimace_scorer_model = GrimaceScoreModel(device=grimace_config.grimace_scoring_device)
                model_weights = torch.load(Path("models/grimace_scorer.pt"), map_location=lambda storage, loc: storage)
                grimace_scorer_model.load_state_dict(model_weights)
                self.grimace_scorer = GrimaceScorer(grimace_scorer_model)
            else:
                self.grimace_scorer = None
        else:
            self.frame_quality_scorer = None
            self.face_cropper = None
            self.grimace_scorer = None

        self.error = None

        self.overview_changed.emit()

    def get_error(self) -> Optional[str]:
        if self.camera_top_config is None:
            return "Top camera not configured"

        if self.camera_front_config is None:
            return "Front camera not configured"

        if self.camera_top_config.camera_id is None:
            return "Top camera device not selected"

        if self.camera_front_config.camera_id is None:
            return "Front camera device not selected"

        if self.recording_config is None:
            return "Recording not configured"

        if self.video_files_config is None:
            return "Video files not configured"

        if self.top_video_file is None or self.front_video_file is None:
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
                return "Grimace results file not configured"

    def get_warnings(self) -> List[str]:
        warnings = []
        if self.camera_top_config is not None and self.camera_front_config is not None:
            if self.camera_top_config.fps is not None and self.camera_front_config.fps is not None:
                if self.camera_top_config.fps != self.camera_front_config.fps:
                    warnings.append("Top and front camera FPS are different")
        for key, value in self.warnings.items():
            if value is not None:
                warnings.append(value)
        return warnings

    def prepare_recording(self, camera_recorder: PylonDualCameraRecorder):
        self.camera_recorder = camera_recorder

        self.configure_video_files(self.video_files_config)

        fourcc = cv2.VideoWriter.fourcc(*self.recording_config.codec)
        top_video_writer = cv2.VideoWriter(
            self.top_video_file, fourcc, self.camera_top_config.fps,
            (camera_recorder.top_camera.get_width(), camera_recorder.top_camera.get_height()), isColor=False)
        front_video_writer = cv2.VideoWriter(
            self.front_video_file, fourcc, self.camera_front_config.fps,
            (camera_recorder.front_camera.get_width(), camera_recorder.front_camera.get_height()), isColor=False)

        self.top_video_buffer = QQueue(1000, "Top Video Buffer")
        self.front_video_buffer = QQueue(1000, "Front Video Buffer")

        self.top_video_writer = BufferVideoWriter(top_video_writer, self.top_video_buffer)
        self.front_video_writer = BufferVideoWriter(front_video_writer, self.front_video_buffer)

        if self.grimace_config.enabled:
            self.grimace_input_buffer = QQueue(1000, "Grimace Input Buffer")
            self.grimace_output_buffer = QQueue(1000, "Grimace Output Buffer")

            frames_per_interval = int(self.grimace_config.frame_interval * self.camera_front_config.fps)

            self.grimace_analyzer = GrimaceAnalyzerV1(self.frame_quality_scorer, self.face_cropper, self.grimace_scorer,
                                                      self.grimace_input_buffer, self.grimace_output_buffer,
                                                      self.grimace_results_list,
                                                      batch_size=16, min_score=1.25 / 6,
                                                      frames_per_interval=frames_per_interval)

            self.grimace_results_writer = GrimaceResultWriter(Path(self.grimace_results_file),
                                                              self.grimace_output_buffer)

        recording_duration = self.recording_config.duration if self.recording_config.mode == "Timed" else None
        self.recording_context = RecordingContext(recording_duration)
        self.recording_context.stop_signal.connect(self.stop_recording)

        self.overview_changed.emit()

    def set_warning(self, key: str, value: str) -> bool:
        prev_value = self.warnings.get(key)
        if prev_value != value:
            self.warnings[key] = value
            return True
        return False

    def check_health(self):
        warnings_changed = False
        if self.camera_recorder is not None:
            if self.camera_recorder.top_camera is not None:
                warning = None
                fill_level = self.camera_recorder.top_camera.buffer_fill_level
                if fill_level > 0.1:
                    warning = f"Top camera buffer fill level: {fill_level * 100:.2f}%"
                warnings_changed |= self.set_warning("top_camera_buffer_fill", warning)

                warning = None
                fps = self.camera_recorder.top_camera.fps
                if fps < self.camera_top_config.fps * 0.9:
                    warning = f"Top camera FPS: {fps:.2f} (expected {self.camera_top_config.fps})"
                warnings_changed |= self.set_warning("top_camera_fps", warning)

            if self.camera_recorder.front_camera is not None:
                warning = None
                fill_level = self.camera_recorder.front_camera.buffer_fill_level
                if fill_level > 0.1:
                    warning = f"Front camera buffer fill level: {fill_level * 100:.2f}%"
                warnings_changed |= self.set_warning("front_camera_buffer_fill", warning)

                warning = None
                fps = self.camera_recorder.front_camera.fps
                if fps < self.camera_front_config.fps * 0.9:
                    warning = f"Front camera FPS: {fps:.2f} (expected {self.camera_front_config.fps})"
                warnings_changed |= self.set_warning("front_camera_fps", warning)

        if self.top_video_buffer is not None:
            warning = None
            fill_level = self.top_video_buffer.get_fill_level()
            if fill_level > 0.1:
                warning = f"Top video buffer fill level: {fill_level * 100:.2f}%"
            warnings_changed |= self.set_warning("top_video_buffer_fill", warning)
        if self.front_video_buffer is not None:
            warning = None
            fill_level = self.front_video_buffer.get_fill_level()
            if fill_level > 0.1:
                warning = f"Front video buffer fill level: {fill_level * 100:.2f}%"
            warnings_changed |= self.set_warning("front_video_buffer_fill", warning)

        if self.grimace_input_buffer is not None:
            warning = None
            fill_level = self.grimace_input_buffer.get_fill_level()
            if fill_level > 0.1:
                warning = f"Grimace analysis buffer fill level: {fill_level * 100:.2f}%"
            warnings_changed |= self.set_warning("grimace_input_buffer_fill", warning)
        if self.grimace_output_buffer is not None:
            warning = None
            fill_level = self.grimace_output_buffer.get_fill_level()
            if fill_level > 0.1:
                warning = f"Grimace results buffer fill level: {fill_level * 100:.2f}%"
            warnings_changed |= self.set_warning("grimace_output_buffer_fill", warning)

        if warnings_changed:
            self.warnings_changed.emit()

    def start_recording(self):
        self.error = None
        self.recording_running = True

        if self.camera_recorder.isRunning():
            self.camera_recorder.stop()
            self.camera_recorder.wait()

        if self.camera_recorder.top_camera is not None:
            self.camera_recorder.top_camera.reset_frame_index()
            self.camera_recorder.top_camera.reset_timestamp_offset()
            self.camera_recorder.top_camera.set_video_buffer(self.top_video_buffer)
        if self.camera_recorder.front_camera is not None:
            self.camera_recorder.front_camera.reset_frame_index()
            self.camera_recorder.front_camera.reset_timestamp_offset()
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

        self.overview_changed.emit()
        self.recording_started.emit()

    def stop_recording(self, error: Optional[str] = None):
        self.camera_recorder.stop()
        self.camera_recorder.wait()

        self.camera_recorder.top_camera.set_video_buffer(None)
        self.camera_recorder.front_camera.set_video_buffer(None)
        self.camera_recorder.front_camera.set_grimace_buffer(None)

        self.camera_recorder.set_recording_context(None)
        self.recording_context.stop()

        self.camera_recorder.start()

        #self.top_video_writer.stop()
        #self.front_video_writer.stop()

        #if self.grimace_config.enabled:
        #    #self.grimace_analyzer.stop()
        #    #self.grimace_results_writer.stop()

        self.top_video_writer.wait()
        self.front_video_writer.wait()

        if self.grimace_config.enabled:
            self.grimace_analyzer.wait()
            self.grimace_results_writer.wait()

        self.recording_running = False

        self.recording_number += 1
        self.configure_video_files(self.video_files_config)

        if error is not None:
            self.error = error
            self.recording_error.emit(error)

        self.overview_changed.emit()
        self.recording_stopped.emit()
