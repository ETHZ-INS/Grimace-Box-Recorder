from datetime import timedelta
import math
import os
import sys
import time
from dataclasses import replace
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
import torch
from PySide6 import QtCore
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PySide6.QtCore import Signal, QThread, QObject
from pypylon import pylon
from ultralytics import YOLO

from app.analysis.grimace_analyzer_v1 import GrimaceAnalyzerV1
from app.analysis.grimace_results_writer import GrimaceResultWriter
from app.config.camera import CameraConfig
from app.config.grimace import GrimaceConfig
from app.config.recording import RecordingConfig
from app.config.serialization.config_loader import ConfigLoader
from app.config.video_files import VideoFilesConfig
from app.controller.configure_camera_dialog import ConfigureCamera
from app.controller.configure_grimace_scoring_dialog import ConfigureGrimaceScoring
from app.controller.configure_recording_dialog import ConfigureRecording
from app.controller.configure_video_files_dialog import ConfigureVideoFiles
from app.controller.grimace_results_widget import GrimaceResults
from app.dataflow.qqueue import QQueue
from app.layout.grimace_box import Ui_WGrimaceBox
from grimace.frame_cropper import FrameCropper
from grimace.frame_cropper_model import FrameCropperModel
from grimace.frame_quality_model import FrameQualityModel
from grimace.frame_quality_scorer import FrameQualityScorer
from grimace.grimace_scorer import GrimaceScorer
from grimace.grimace_scorer_model import GrimaceScoreModel
from app.recording.dual_video_recorder import PylonDualCameraRecorder
from app.recording.video_writer import BufferVideoWriter
from app.recording.recording_context import RecordingContext
from app.dataflow.qvariable import QVariable
from app.dataflow.qlist import QList

os.environ["YOLO_VERBOSE"] = "false"
os.environ["PYLON_CAMEMU"] = "2"

OVERVIEW_TEMPLATE = """
## Overview for {recording_state}:  
Recording Number: \t{recording_number}  
Recording Duration: \t{recording_duration}  
Top Camera Frame Rate: \t{top_camera_fps}  
Front Camera Frame Rate: \t{front_camera_fps}  
Top Video Filename: \t{top_video_file}  
Front Video Filename: \t{front_video_file}
### Grimace Scoring: {grimace_enabled}  
{grimace_overview}
"""

GRIMACE_OVERVIEW_TEMPLATE = """
Grimace Model: {grimace_model}  
Frame Interval: {frame_interval}  
Grimace Results File: {grimace_results_file}
"""

VideoBuffer = QQueue[Tuple[np.ndarray, int, float]]


class RecordingManager(QObject):
    overview_changed = Signal()
    recording_started = Signal()
    recording_stopped = Signal()
    recording_error = Signal(str)

    def __init__(self):
        super().__init__()
        self.camera_top_config = None
        self.camera_front_config = None
        self.recording_config = None
        self.video_files_config = None
        self.grimace_config = None

        self.recording_number = 1

        self.top_video_file = None
        self.front_video_file = None
        self.grimace_results_file = None

        self.camera_top_fps = None
        self.camera_front_fps = None

        self.recording_mode = None
        self.recording_duration = None
        self.codec = None

        self.grimace_enabled = None
        self.grimace_model = None
        self.frame_interval = None

        self.frame_quality_scorer = None
        self.face_cropper = None
        self.grimace_scorer = None

        self.camera_recorder = None

        self.recording_context = None

        self.top_video_buffer: Optional[VideoBuffer] = None
        self.front_video_buffer: Optional[VideoBuffer] = None
        self.grimace_input_buffer: Optional[VideoBuffer] = None
        self.grimace_output_buffer: Optional[VideoBuffer] = None

        self.grimace_results_list = QList()

        self.top_video_writer = None
        self.front_video_writer = None

        self.grimace_analyzer = None
        self.grimace_results_writer = None

        self.recording_running = False

        self.error: Optional[str] = None

    def configure_video_files(self, video_files_config: Optional[VideoFilesConfig]):
        self.video_files_config = replace(video_files_config)

        if video_files_config is None:
            self.top_video_file = None
            self.front_video_file = None
            self.grimace_results_file = None
            self.overview_changed.emit()
            return

        naming_mode = video_files_config.naming_mode
        target_directory = video_files_config.target_directory
        if naming_mode is None or target_directory is None:
            self.top_video_file = None
            self.front_video_file = None
            self.grimace_results_file = None
            self.overview_changed.emit()
            return

        top_video_file_template = video_files_config.top_templates.get(naming_mode)
        front_video_file_template = video_files_config.front_templates.get(naming_mode)
        grimace_results_file_template = video_files_config.grimace_results_templates.get(naming_mode)

        if top_video_file_template is None or front_video_file_template is None or grimace_results_file_template is None:
            self.top_video_file = None
            self.front_video_file = None
            self.grimace_results_file = None
            self.overview_changed.emit()
            return

        timestamp = time.strftime("%Y%m%d%H%M%S")

        while True:
            top_video_file = top_video_file_template.format(recording_number=self.recording_number,
                                                            start_time=timestamp)
            front_video_file = front_video_file_template.format(recording_number=self.recording_number,
                                                                start_time=timestamp)
            grimace_results_file = grimace_results_file_template.format(recording_number=self.recording_number,
                                                                        start_time=timestamp)

            top_video_file = Path(target_directory) / top_video_file
            front_video_file = Path(target_directory) / front_video_file
            grimace_results_file = Path(target_directory) / grimace_results_file

            if not top_video_file.exists() and not front_video_file.exists() and not grimace_results_file.exists():
                break

            self.recording_number += 1

        self.top_video_file = str(top_video_file)
        self.front_video_file = str(front_video_file)
        self.grimace_results_file = str(grimace_results_file)

        self.error = None

        self.overview_changed.emit()

    def configure_top_camera(self, camera_top_config: Optional[CameraConfig]):
        self.camera_top_config = replace(camera_top_config)

        if camera_top_config is None:
            self.camera_top_fps = None
        else:
            self.camera_top_fps = camera_top_config.fps

        self.error = None

        self.overview_changed.emit()

    def configure_front_camera(self, camera_front_config: Optional[CameraConfig]):
        self.camera_front_config = replace(camera_front_config)

        if camera_front_config is None:
            self.camera_front_fps = None
            self.overview_changed.emit()
            return

        self.camera_front_fps = camera_front_config.fps

        self.error = None

        self.overview_changed.emit()

    def configure_recording(self, recording_config: RecordingConfig):
        self.recording_config = replace(recording_config)

        if recording_config is None:
            self.recording_mode = None
            self.recording_duration = None
            self.codec = None
            self.overview_changed.emit()
            return

        self.recording_mode = recording_config.mode
        self.recording_duration = recording_config.duration if recording_config.mode == "Timed" else None
        self.codec = recording_config.codec

        self.error = None

        self.overview_changed.emit()

    def configure_grimace(self, grimace_config: GrimaceConfig):
        self.grimace_config = replace(grimace_config)

        if grimace_config is None:
            self.grimace_enabled = None
            self.grimace_model = None
            self.frame_interval = None
            self.overview_changed.emit()
            return

        self.grimace_enabled = grimace_config.enabled
        self.grimace_model = grimace_config.grimace_model
        self.frame_interval = grimace_config.frame_interval

        if grimace_config.enabled:
            frame_quality_model = FrameQualityModel(device=grimace_config.frame_quality_device)
            model_weigths = torch.load(Path("models/frame_quality.pt"), map_location=lambda storage, loc: storage)
            frame_quality_model.load_state_dict(model_weigths)
            self.frame_quality_scorer = FrameQualityScorer(frame_quality_model)

            face_cropper_model_base = YOLO('models/face_cropper.pt')
            face_cropper_model_base.to(grimace_config.face_cropper_device)
            face_cropper_model = FrameCropperModel(face_cropper_model_base, device=grimace_config.face_cropper_device)
            self.face_cropper = FrameCropper(face_cropper_model, padding=0.05, confidence_threshold=0.9)

            grimace_scorer_model = GrimaceScoreModel(device=grimace_config.grimace_scoring_device)
            model_weigths = torch.load(Path("models/grimace_scorer.pt"), map_location=lambda storage, loc: storage)
            grimace_scorer_model.load_state_dict(model_weigths)
            self.grimace_scorer = GrimaceScorer(grimace_scorer_model)
        else:
            self.frame_quality_scorer = None
            self.face_cropper = None
            self.grimace_scorer = None

        self.error = None

        self.overview_changed.emit()

    def ready(self) -> Optional[str]:
        if self.camera_top_config is None:
            return "Top camera not configured"

        if self.camera_front_config is None:
            return "Front camera not configured"

        if self.recording_config is None:
            return "Recording not configured"

        if self.video_files_config is None:
            return "Video files not configured"

        if self.top_video_file is None or self.front_video_file is None:
            return "Video files not configured"

        if self.camera_top_fps is None or self.camera_front_fps is None:
            return "Camera FPS not configured"

        if self.recording_mode is None:
            return "Recording mode not configured"

        if self.recording_duration is None and self.recording_mode == "Timed":
            return "Recording duration not configured"

        if self.codec is None:
            return "Codec not configured"

        if self.grimace_enabled is None:
            return "Grimace scoring not configured"

        if self.grimace_enabled:
            if self.grimace_model is None:
                return "Grimace model not configured"
            if self.frame_interval is None:
                return "Frame interval not configured"
            if self.frame_quality_scorer is None:
                return "Frame quality scorer not configured"
            if self.face_cropper is None:
                return "Face cropper not configured"
            if self.grimace_scorer is None:
                return "Grimace scorer not configured"
            if self.grimace_results_file is None:
                return "Grimace results file not configured"

        return None

    def prepare_recording(self, camera_recorder: PylonDualCameraRecorder):
        self.camera_recorder = camera_recorder

        self.configure_video_files(self.video_files_config)

        fourcc = cv2.VideoWriter_fourcc(*self.codec)
        top_video_writer = cv2.VideoWriter(
            self.top_video_file, fourcc, self.camera_top_fps,
            (camera_recorder.top_camera.get_width(), camera_recorder.top_camera.get_height()), isColor=False)
        front_video_writer = cv2.VideoWriter(
            self.front_video_file, fourcc, self.camera_front_fps,
            (camera_recorder.front_camera.get_width(), camera_recorder.front_camera.get_height()), isColor=False)

        self.top_video_buffer = QQueue(1000, "Top Video Buffer")
        self.front_video_buffer = QQueue(1000, "Front Video Buffer")

        self.top_video_writer = BufferVideoWriter(top_video_writer, self.top_video_buffer)
        self.front_video_writer = BufferVideoWriter(front_video_writer, self.front_video_buffer)

        if self.grimace_config.enabled:
            self.grimace_input_buffer = QQueue(1000, "Grimace Input Buffer")
            self.grimace_output_buffer = QQueue(1000, "Grimace Output Buffer")

            frames_per_interval = int(self.frame_interval * self.camera_front_fps)

            self.grimace_analyzer = GrimaceAnalyzerV1(self.frame_quality_scorer, self.face_cropper, self.grimace_scorer,
                                                      self.grimace_input_buffer, self.grimace_output_buffer,
                                                      self.grimace_results_list,
                                                      batch_size=16, min_score=1.25 / 6,
                                                      frames_per_interval=frames_per_interval)

            self.grimace_results_writer = GrimaceResultWriter(Path(self.grimace_results_file),
                                                              self.grimace_output_buffer)

        self.recording_context = RecordingContext(self.recording_duration if self.recording_mode == "Timed" else None)
        self.recording_context.stop_signal.connect(self.stop_recording)

        self.overview_changed.emit()

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

        self.camera_recorder.start()
        #self.recording_context.start()

        self.top_video_writer.start()
        self.front_video_writer.start()

        if self.grimace_config.enabled:
            self.grimace_analyzer.start()
            self.grimace_results_writer.start()

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

        self.top_video_writer.stop()
        self.front_video_writer.stop()

        if self.grimace_config.enabled:
            self.grimace_analyzer.stop()
            self.grimace_results_writer.stop()

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


class MainWindow(Ui_WGrimaceBox, QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.action_configure_top_camera.triggered.connect(self.configure_top_camera)
        self.action_configure_front_camera.triggered.connect(self.configure_front_camera)
        self.action_configure_recording.triggered.connect(self.configure_recording)
        self.action_configure_video_files.triggered.connect(self.configure_video_files)

        self.action_save_project.triggered.connect(self.save_project)
        self.action_save_project_as.triggered.connect(self.save_project_as)
        self.action_load_project.triggered.connect(self.load_project)

        self.action_configure_grimace_scoring.triggered.connect(self.configure_grimace_scoring)
        self.action_open_grimace_results_window.triggered.connect(self.open_grimace_results_window)

        self.btn_record.clicked.connect(self.btn_record_clicked)

        self.config_file = None

        self.camera_top_config = CameraConfig()
        self.camera_front_config = CameraConfig()

        self.recording_config = RecordingConfig()
        self.video_files_config = VideoFilesConfig()

        self.grimace_config = GrimaceConfig()

        self.preview_buffer_top = QVariable()
        self.preview_buffer_top.value_set.connect(self.on_video_frame_top)

        self.preview_buffer_front = QVariable()
        self.preview_buffer_front.value_set.connect(self.on_video_frame_front)

        self.recording_manager = RecordingManager()
        self.recording_manager.overview_changed.connect(self.overview_changed)
        self.recording_manager.recording_started.connect(self.recording_started)
        self.recording_manager.recording_stopped.connect(self.recording_stopped)

        self.camera_recorder = PylonDualCameraRecorder()
        self.camera_recorder.setPriority(QThread.Priority.HighestPriority)
        self.camera_recorder.top_error_signal.connect(self.on_top_camera_error)
        self.camera_recorder.front_error_signal.connect(self.on_front_camera_error)

        self.grimace_results_window = None

        self.frame_extractor_input_buffer = None
        self.grimace_frames = None
        self.frame_extractor = None

        self.overview_changed()
        self.update_video_label_size()

        QThread.currentThread().setPriority(QThread.Priority.LowPriority)

    def resizeEvent(self, event):
        self.update_video_label_size()

    @staticmethod
    def get_available_cameras() -> List[str]:
        devices = list(pylon.TlFactory.GetInstance().EnumerateDevices())
        return [device.GetSerialNumber() for device in devices]

    @staticmethod
    def get_available_devices() -> List[Tuple[str, str]]:
        devices = [("cpu", "CPU")]

        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                device_name = torch.cuda.get_device_name(i)
                device_id = f"cuda:{i}"
                devices.append((device_id, device_name))

        # Add number to duplicate device names
        device_names = [device_name for _, device_name in devices]
        for i, (device_id, device_name) in enumerate(devices):
            if device_names.count(device_name) > 1:
                devices[i] = (device_id, f"{device_name} ({device_names[:i].count(device_name)})")

        return devices

    def update_menubar(self):
        actions_enabled = not self.recording_manager.recording_running
        self.action_configure_top_camera.setEnabled(actions_enabled)
        self.action_configure_front_camera.setEnabled(actions_enabled)
        self.menu_configure_cameras.setEnabled(actions_enabled)
        self.action_configure_recording.setEnabled(actions_enabled)
        self.action_configure_video_files.setEnabled(actions_enabled)
        self.action_configure_grimace_scoring.setEnabled(actions_enabled)
        self.action_load_project.setEnabled(actions_enabled)
        self.action_save_project.setEnabled(True)
        self.action_save_project_as.setEnabled(True)

    def update_recording_button(self):
        if self.recording_manager.recording_running:
            self.btn_record.setText("Stop Recording")
        else:
            self.btn_record.setText("Start Recording")

    def update_video_label_size(self):
        label_width = self.lbl_video_top.width()

        video_top_width = self.camera_recorder.top_camera.get_width() if self.camera_recorder.top_camera is not None else 375
        video_top_height = self.camera_recorder.top_camera.get_height() if self.camera_recorder.top_camera is not None else 300
        video_top_aspect_ratio = video_top_width / video_top_height
        video_top_height = math.ceil(label_width / video_top_aspect_ratio)

        video_front_width = self.camera_recorder.front_camera.get_width() if self.camera_recorder.front_camera is not None else 375
        video_front_height = self.camera_recorder.front_camera.get_height() if self.camera_recorder.front_camera is not None else 300
        video_front_aspect_ratio = video_front_width / video_front_height
        video_front_height = math.ceil(label_width / video_front_aspect_ratio)

        max_height = max(video_top_height, video_front_height)
        self.lbl_video_front.setMinimumSize(375, max_height)
        self.lbl_video_top.setMinimumSize(375, max_height)
        self.lbl_video_front.setMaximumSize(750, max_height)
        self.lbl_video_top.setMaximumSize(750, max_height)

    def on_video_frame_top(self):
        frame = self.preview_buffer_top.get()

        video_label_width = self.lbl_video_top.width()
        video_label_height = self.lbl_video_top.height()

        h, w, ch = frame.shape
        bytes_per_line = ch * w
        if ch == 1:
            q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_Grayscale8)
        else:
            q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        frame = QPixmap.fromImage(q_img)

        frame = frame.scaled(video_label_width, video_label_height, QtCore.Qt.AspectRatioMode.KeepAspectRatio)

        self.lbl_video_top.setPixmap(frame)

    def on_video_frame_front(self):
        if self.recording_manager.recording_context:
            recording_time = self.recording_manager.recording_context.recording_time() if self.recording_manager.recording_context.started else 0.0
            recording_time_string = str(
                timedelta(seconds=recording_time)) if recording_time is not None else "Not Recording"
            self.lbl_time.setText(recording_time_string)

        frame = self.preview_buffer_front.get()

        video_label_width = self.lbl_video_front.width()
        video_label_height = self.lbl_video_front.height()

        h, w, ch = frame.shape
        bytes_per_line = ch * w
        if ch == 1:
            q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_Grayscale8)
        else:
            q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        frame = QPixmap.fromImage(q_img)

        frame = frame.scaled(video_label_width, video_label_height, QtCore.Qt.AspectRatioMode.KeepAspectRatio)

        self.lbl_video_front.setPixmap(frame)

    def setup_top_camera(self, camera_config: CameraConfig, start: bool = True):
        self.camera_top_config = camera_config

        if camera_config.camera_id is None:
            self.update_video_label_size()
            self.lbl_video_top.clear()
            self.lbl_video_top.setText("Top camera not configured")
            return

        self.camera_recorder.set_top_camera(
            camera_config.camera_id, fps=camera_config.fps,
            config_file=camera_config.config_file, start=start
        )
        self.camera_recorder.top_camera.set_preview_buffer(self.preview_buffer_top)

        self.update_video_label_size()

        self.recording_manager.configure_top_camera(camera_config)

    def setup_front_camera(self, camera_config: CameraConfig, start: bool = True):
        self.camera_front_config = camera_config

        if camera_config.camera_id is None:
            self.update_video_label_size()
            self.lbl_video_front.clear()
            self.lbl_video_front.setText("Front camera not configured")
            return

        self.camera_recorder.set_front_camera(
            camera_config.camera_id, fps=camera_config.fps,
            config_file=camera_config.config_file, start=start
        )
        self.camera_recorder.front_camera.set_preview_buffer(self.preview_buffer_front)

        self.update_video_label_size()

        self.recording_manager.configure_front_camera(camera_config)

    def configure_top_camera(self):
        available_cameras = self.get_available_cameras()

        dlg = ConfigureCamera(self, self.camera_top_config, available_cameras)
        dlg.lbl_title.setText("Configure Top Camera")
        dlg.setWindowTitle("Configure Top Camera")
        dlg.applied_signal.connect(self.setup_top_camera)
        dlg.exec()

    def configure_front_camera(self):
        available_cameras = self.get_available_cameras()

        dlg = ConfigureCamera(self, self.camera_front_config, available_cameras)
        dlg.lbl_title.setText("Configure Front Camera")
        dlg.setWindowTitle("Configure Front Camera")
        dlg.applied_signal.connect(self.setup_front_camera)
        dlg.exec()

    def on_top_camera_error(self, error: str):
        if self.recording_manager.recording_running:
            self.recording_manager.stop_recording(error)
        self.camera_top_config.camera_id = None
        self.setup_top_camera(self.camera_top_config, start=False)
        self.lbl_video_top.setText(error)

    def on_front_camera_error(self, error: str):
        if self.recording_manager.recording_running:
            self.recording_manager.stop_recording(error)
        self.camera_front_config.camera_id = None
        self.setup_front_camera(self.camera_front_config, start=False)
        self.lbl_video_front.setText(error)

    def recording_config_changed(self, recording_config: RecordingConfig):
        self.recording_config = recording_config
        self.recording_manager.configure_recording(recording_config)

    def configure_recording(self):
        dlg = ConfigureRecording(self, self.recording_config)
        dlg.applied_signal.connect(self.recording_config_changed)
        dlg.exec()

    def video_files_config_changed(self, video_files_config: VideoFilesConfig):
        self.video_files_config = video_files_config
        self.recording_manager.configure_video_files(video_files_config)

    def configure_video_files(self):
        dlg = ConfigureVideoFiles(self, self.video_files_config)
        dlg.applied_signal.connect(self.video_files_config_changed)
        dlg.exec()

    def grimace_config_changed(self, grimace_config):
        self.grimace_config = grimace_config
        self.recording_manager.configure_grimace(grimace_config)

    def configure_grimace_scoring(self):
        available_devices = self.get_available_devices()
        dlg = ConfigureGrimaceScoring(self, self.grimace_config, available_devices)
        dlg.applied_signal.connect(self.grimace_config_changed)
        dlg.exec()

    def overview_changed(self):
        recording_running = self.recording_manager.recording_running
        recording_state = "running recording" if recording_running else "next recording"

        recording_number = self.recording_manager.recording_number
        if recording_number is None:
            recording_number = "Not configured"
        else:
            recording_number = str(recording_number)

        recording_mode = self.recording_manager.recording_mode
        if recording_mode is None:
            recording_duration = "Not configured"
        elif recording_mode == "Manual":
            recording_duration = "Manual"
        elif recording_mode == "Timed":
            recording_duration = self.recording_manager.recording_duration
            if recording_duration is not None:
                recording_duration = str(timedelta(seconds=recording_duration))
            else:
                recording_duration = "Not Configured"
        else:
            recording_duration = "Not Configured"

        top_camera_fps = self.recording_manager.camera_top_fps
        if top_camera_fps is None:
            top_camera_fps = "Not configured"
        else:
            top_camera_fps = str(top_camera_fps) + " FPS"

        front_camera_fps = self.recording_manager.camera_front_fps
        if front_camera_fps is None:
            front_camera_fps = "Not configured"
        else:
            front_camera_fps = str(front_camera_fps) + " FPS"

        top_video_file = self.recording_manager.top_video_file
        if top_video_file is None:
            top_video_file = "Not configured"
        else:
            top_video_file = str(top_video_file)

        front_video_file = self.recording_manager.front_video_file
        if front_video_file is None:
            front_video_file = "Not configured"
        else:
            front_video_file = str(front_video_file)

        if self.recording_manager.grimace_config is None:
            grimace_enabled = "Not configured"
            grimace_overview = ""
        else:
            grimace_enabled = "Enabled" if self.recording_manager.grimace_config.enabled else "Disabled"

            if self.recording_manager.grimace_config.enabled:
                grimace_model = self.recording_manager.grimace_config.grimace_model
                if grimace_model is None:
                    grimace_model = "Not configured"
                frame_interval = self.recording_manager.grimace_config.frame_interval
                if frame_interval is None:
                    frame_interval = "Not configured"
                else:
                    print(frame_interval)
                    frame_interval_seconds = round(self.recording_manager.grimace_config.frame_interval)
                    if frame_interval_seconds == 10:
                        frame_interval = "10 Seconds"
                    elif frame_interval_seconds == 20:
                        frame_interval = "20 Seconds"
                    elif frame_interval_seconds == 30:
                        frame_interval = "30 Seconds"
                    elif frame_interval_seconds == 60:
                        frame_interval = "1 Minute"
                    elif frame_interval_seconds == 120:
                        frame_interval = "2 Minutes"
                    elif frame_interval_seconds == 300:
                        frame_interval = "5 Minutes"

                grimace_overview = GRIMACE_OVERVIEW_TEMPLATE.format(
                    grimace_model=grimace_model,
                    frame_interval=frame_interval,
                    grimace_results_file=self.recording_manager.grimace_results_file
                )
            else:
                grimace_overview = ""

        overview = OVERVIEW_TEMPLATE.format(
            recording_state=recording_state,
            recording_number=recording_number,
            recording_duration=recording_duration,
            top_camera_fps=top_camera_fps,
            front_camera_fps=front_camera_fps,
            top_video_file=top_video_file,
            front_video_file=front_video_file,
            grimace_enabled=grimace_enabled,
            grimace_overview=grimace_overview
        )

        self.lbl_overview.setText(overview)

        if recording_running:
            self.btn_record.setEnabled(True)
            self.btn_record.setText("Stop Recording")
        else:
            self.btn_record.setEnabled(True)
            self.btn_record.setText("Start Recording")

        message = self.recording_manager.ready()
        if message is not None:
            self.btn_record.setEnabled(False)
            self.lbl_message.setText("Not ready: " + message)
            self.lbl_message.setStyleSheet("color: red")
        elif recording_running:
            self.lbl_message.setText("Recording...")
            self.lbl_message.setStyleSheet("color: blue")
        elif self.recording_manager.error is not None:
            self.lbl_message.setText("Recording Stopped: " + self.recording_manager.error)
            self.lbl_message.setStyleSheet("color: red")
        else:
            self.lbl_message.setText("Ready to record")
            self.lbl_message.setStyleSheet("color: green")

    def open_grimace_results_window(self):
        if self.grimace_results_window is not None and self.grimace_results_window.isVisible():
            return

        if self.grimace_results_window is not None:
            self.grimace_results_window.close()

        self.grimace_results_window = GrimaceResults(self, self.recording_manager.grimace_results_list)
        self.grimace_results_window.show()

    def recording_started(self):
        if self.grimace_config.enabled:
            self.open_grimace_results_window()
        self.update_menubar()
        self.update_recording_button()

    def recording_stopped(self):
        self.update_menubar()
        self.update_recording_button()

    def start_recording(self):
        self.recording_manager.prepare_recording(self.camera_recorder)
        self.recording_manager.start_recording()

    def stop_recording(self):
        if self.recording_manager.recording_mode == "Timed":
            msgBox = QMessageBox(parent=self)
            msgBox.setWindowTitle("Confirm")
            msgBox.setText(
                "The recording is configured to stop automatically after a certain duration. Do you want to stop it now?")
            msgBox.setIcon(QMessageBox.Icon.Question)
            msgBox.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msgBox.exec()

            if msgBox.result() == QMessageBox.StandardButton.No:
                return

        self.recording_manager.stop_recording()

    def btn_record_clicked(self):
        if not self.recording_manager.recording_running:
            self.start_recording()
        else:
            self.stop_recording()

    def closeEvent(self, event):
        self.camera_recorder.stop()
        self.camera_recorder.wait()

        super(MainWindow, self).closeEvent(event)

    def save_project(self):
        if self.config_file is None:
            return self.save_project_as()
        ConfigLoader.save(Path(self.config_file), self.camera_top_config, self.camera_front_config,
                          self.recording_config, self.video_files_config, self.grimace_config)

    def save_project_as(self):
        if self.config_file is None:
            selected_file = str(Path.home() / "project.gbp")
        else:
            selected_file = self.config_file

        file_name, _ = QFileDialog.getSaveFileName(self, "Save Project", selected_file,
                                                   "Grimace Box Project Files (*.gbp)")
        if file_name:
            self.config_file = file_name
            self.save_project()

    def load_project(self):
        if self.recording_manager.recording_running:
            msgBox = QMessageBox(parent=self)
            msgBox.setWindowTitle("Error")
            msgBox.setText(
                "Cannot load project while recording is running. Stop the recording or wait for it to finish.")
            msgBox.setIcon(QMessageBox.Icon.Critical)
            msgBox.exec_()
            return

        if self.config_file is not None:
            selected_file = self.config_file
        else:
            selected_file = str(Path.home())

        selected_file, _ = QFileDialog.getOpenFileName(self, "Open Project", selected_file,
                                                       "Grimace Box Project Files (*.gbp)")
        if selected_file:
            self.config_file = selected_file
            self.camera_top_config, self.camera_front_config, self.recording_config, self.video_files_config, self.grimace_config = \
                ConfigLoader.load(Path(self.config_file))

            # Only start the camera thread once both cameras are configured
            try:
                self.setup_top_camera(self.camera_top_config, start=False)
            except Exception as e:
                self.on_top_camera_error(str(e))

            try:
                self.setup_front_camera(self.camera_front_config, start=True)
            except Exception as e:
                self.on_front_camera_error(str(e))
                if self.camera_recorder.top_camera is not None:
                    self.camera_recorder.start()

            self.recording_config_changed(self.recording_config)
            self.video_files_config_changed(self.video_files_config)
            self.grimace_config_changed(self.grimace_config)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    window.update_video_label_size()

    sys.exit(app.exec())
