from copy import deepcopy
from datetime import timedelta
import math
import os
import sys
from pathlib import Path
from typing import List, Tuple

import numpy as np
import torch
from PySide6 import QtCore
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PySide6.QtCore import QThread
from pypylon import pylon

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
from app.layout.grimace_box import Ui_WGrimaceBox
from app.recording.recording_manager import RecordingManager
from app.validation.config.camera_config_validator import CameraConfigValidator
from app.validation.config.grimace_config_validator import GrimaceConfigValidator
from app.validation.config.recording_config_validator import RecordingConfigValidator
from app.validation.config.video_files_validator import VideoFilesValidator
from app.recording.dual_video_recorder import PylonDualCameraRecorder
from app.dataflow.qvariable import QVariable

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


class MainWindow(Ui_WGrimaceBox, QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.setStyleSheet(":disabled { color: gray }")

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

        self.preview_buffer_top = QVariable()
        self.preview_buffer_top.value_set.connect(self.on_video_frame_top)

        self.preview_buffer_front = QVariable()
        self.preview_buffer_front.value_set.connect(self.on_video_frame_front)

        self.recording_manager = RecordingManager()
        self.recording_manager.overview_changed.connect(self.overview_changed)
        self.recording_manager.warnings_changed.connect(self.warnings_changed)
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

        def calculate_size(camera_recorder) -> Tuple[int, int]:
            width = camera_recorder.get_width() if camera_recorder is not None else 375
            height = camera_recorder.get_height() if camera_recorder is not None else 300
            aspect_ratio = width / height
            height = math.ceil(label_width / aspect_ratio)
            return width, height

        video_top_width, video_top_height = calculate_size(self.camera_recorder.top_camera)
        video_front_width, video_front_height = calculate_size(self.camera_recorder.front_camera)
        max_height = max(video_top_height, video_front_height)

        self.lbl_video_front.setMinimumSize(375, max_height)
        self.lbl_video_top.setMinimumSize(375, max_height)
        self.lbl_video_front.setMaximumSize(750, max_height)
        self.lbl_video_top.setMaximumSize(750, max_height)

    def process_frame(self, frame: np.ndarray, width: int, height: int) -> QPixmap:
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        if ch == 1:
            q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_Grayscale8)
        else:
            q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        frame = QPixmap.fromImage(q_img)

        frame = frame.scaled(width, height, QtCore.Qt.AspectRatioMode.KeepAspectRatio)

        return frame

    def on_video_frame_top(self):
        frame = self.preview_buffer_top.get()

        video_label_width = self.lbl_video_top.width()
        video_label_height = self.lbl_video_top.height()

        frame = self.process_frame(frame, video_label_width, video_label_height)

        self.lbl_video_top.setPixmap(frame)

    def on_video_frame_front(self):
        if self.recording_manager.recording_context:
            recording_time = 0.0
            if self.recording_manager.recording_context.started:
                recording_time = self.recording_manager.recording_context.recording_time()

            recording_time_string = str(timedelta(seconds=recording_time))
            self.lbl_time.setText(recording_time_string)

        frame = self.preview_buffer_front.get()

        video_label_width = self.lbl_video_front.width()
        video_label_height = self.lbl_video_front.height()

        frame = self.process_frame(frame, video_label_width, video_label_height)

        self.lbl_video_front.setPixmap(frame)

    def setup_top_camera(self, camera_config: CameraConfig, start: bool = True):
        self.recording_manager.configure_top_camera(camera_config)

        if camera_config.camera_id is None:
            self.update_video_label_size()
            self.lbl_video_top.clear()
            self.lbl_video_top.setText("Top camera not configured")

            self.camera_recorder.set_top_camera(None)
        else:
            self.camera_recorder.set_top_camera(
                camera_config.camera_id, fps=camera_config.fps,
                config_file=camera_config.config_file, start=start
            )
            self.camera_recorder.top_camera.set_preview_buffer(self.preview_buffer_top)

            self.update_video_label_size()

    def setup_front_camera(self, camera_config: CameraConfig, start: bool = True):
        self.recording_manager.configure_front_camera(camera_config)

        if camera_config.camera_id is None:
            self.update_video_label_size()
            self.lbl_video_front.clear()
            self.lbl_video_front.setText("Front camera not configured")

            self.camera_recorder.set_front_camera(None)
        else:
            self.camera_recorder.set_front_camera(
                camera_config.camera_id, fps=camera_config.fps,
                config_file=camera_config.config_file, start=start
            )
            self.camera_recorder.front_camera.set_preview_buffer(self.preview_buffer_front)

            self.update_video_label_size()

    def configure_top_camera(self):
        available_cameras = self.get_available_cameras()

        if self.recording_manager.camera_front_config is not None:
            if self.recording_manager.camera_front_config.camera_id is not None:
                available_cameras.remove(self.recording_manager.camera_front_config.camera_id)

        dlg = ConfigureCamera(self, self.recording_manager.camera_top_config, available_cameras)
        dlg.lbl_title.setText("Configure Top Camera")
        dlg.setWindowTitle("Configure Top Camera")
        dlg.applied_signal.connect(self.setup_top_camera)
        dlg.exec()

    def configure_front_camera(self):
        available_cameras = self.get_available_cameras()

        if self.recording_manager.camera_top_config is not None:
            if self.recording_manager.camera_top_config.camera_id is not None:
                available_cameras.remove(self.recording_manager.camera_top_config.camera_id)

        dlg = ConfigureCamera(self, self.recording_manager.camera_front_config, available_cameras)
        dlg.lbl_title.setText("Configure Front Camera")
        dlg.setWindowTitle("Configure Front Camera")
        dlg.applied_signal.connect(self.setup_front_camera)
        dlg.exec()

    def on_top_camera_error(self, error: str):
        if self.recording_manager.recording_running:
            self.recording_manager.stop_recording(error)
        camera_top_config = deepcopy(self.recording_manager.camera_top_config)
        camera_top_config.camera_id = None
        self.setup_top_camera(camera_top_config, start=False)
        self.lbl_video_top.setText(error)

    def on_front_camera_error(self, error: str):
        if self.recording_manager.recording_running:
            self.recording_manager.stop_recording(error)
        camera_front_config = deepcopy(self.recording_manager.camera_front_config)
        camera_front_config.camera_id = None
        self.setup_front_camera(camera_front_config, start=False)
        self.lbl_video_front.setText(error)

    def recording_config_changed(self, recording_config: RecordingConfig):
        self.recording_manager.configure_recording(recording_config)

    def configure_recording(self):
        dlg = ConfigureRecording(self, self.recording_manager.recording_config)
        dlg.applied_signal.connect(self.recording_config_changed)
        dlg.exec()

    def video_files_config_changed(self, video_files_config: VideoFilesConfig):
        self.recording_manager.configure_video_files(video_files_config)

    def configure_video_files(self):
        dlg = ConfigureVideoFiles(self, self.recording_manager.video_files_config)
        dlg.applied_signal.connect(self.video_files_config_changed)
        dlg.exec()

    def grimace_config_changed(self, grimace_config):
        self.recording_manager.configure_grimace(grimace_config)

    def configure_grimace_scoring(self):
        available_devices = self.get_available_devices()
        dlg = ConfigureGrimaceScoring(self, self.recording_manager.grimace_config, available_devices)
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

        recording_mode = self.recording_manager.recording_config.mode
        if recording_mode is None:
            recording_duration = "Not configured"
        elif recording_mode == "Manual":
            recording_duration = "Manual"
        elif recording_mode == "Timed":
            recording_duration = self.recording_manager.recording_config.duration
            if recording_duration is not None:
                recording_duration = str(timedelta(seconds=recording_duration))
            else:
                recording_duration = "Not Configured"
        else:
            recording_duration = "Not Configured"

        top_camera_fps = self.recording_manager.camera_top_config.fps
        if top_camera_fps is None:
            top_camera_fps = "Not configured"
        else:
            top_camera_fps = str(top_camera_fps) + " FPS"

        front_camera_fps = self.recording_manager.camera_front_config.fps
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
                    frame_interval_str = "Not configured"
                else:
                    frame_interval_seconds = round(self.recording_manager.grimace_config.frame_interval)

                    minutes = frame_interval_seconds // 60
                    seconds = frame_interval_seconds % 60

                    minutes_str = f"{minutes} Minutes" if minutes > 1 else ("1 Minute" if minutes == 1 else "")
                    seconds_str = f"{seconds} Seconds" if seconds > 1 else ("1 Second" if seconds == 1 else "")

                    frame_interval_str = minutes_str + (" " if minutes and seconds else "") + seconds_str

                grimace_overview = GRIMACE_OVERVIEW_TEMPLATE.format(
                    grimace_model=grimace_model,
                    frame_interval=frame_interval_str,
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

        message = self.recording_manager.get_error()
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

        self.warnings_changed()

    def warnings_changed(self):
        warnings = self.recording_manager.get_warnings()
        if warnings:
            warning_title = "## Warnings:  \n"
            warning_text = warning_title + ("  \n".join(warnings))
            self.lbl_warnings.setText(warning_text)
        else:
            self.lbl_warnings.setText("")

    def open_grimace_results_window(self):
        if self.grimace_results_window is not None and self.grimace_results_window.isVisible():
            return

        if self.grimace_results_window is not None:
            self.grimace_results_window.close()

        self.grimace_results_window = GrimaceResults(self, self.recording_manager.grimace_results_list)
        self.grimace_results_window.show()

    def recording_started(self):
        if self.recording_manager.grimace_config.enabled:
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
        if self.recording_manager.recording_config.mode == "Timed":
            msg = QMessageBox(parent=self)
            msg.setWindowTitle("Confirm")
            msg.setText("The recording is configured to stop automatically after a certain duration. "
                        "Do you want to stop it now?")
            msg.setIcon(QMessageBox.Icon.Question)
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg.exec()

            if msg.result() == QMessageBox.StandardButton.No:
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
        camera_top_config = self.recording_manager.camera_top_config
        camera_front_config = self.recording_manager.camera_front_config
        recording_config = self.recording_manager.recording_config
        video_files_config = self.recording_manager.video_files_config
        grimace_config = self.recording_manager.grimace_config
        ConfigLoader.save(Path(self.config_file), camera_top_config, camera_front_config,
                          recording_config, video_files_config, grimace_config)

    def save_project_as(self):
        if self.config_file is None:
            selected_file = str(Path.home() / "project.gb")
        else:
            selected_file = self.config_file

        file_name, _ = QFileDialog.getSaveFileName(self, "Save Project", selected_file,
                                                   "Grimace Box Project Files (*.gb)")
        if file_name:
            self.config_file = file_name
            self.save_project()

    def load_project(self):
        if self.recording_manager.recording_running:
            msg = QMessageBox(parent=self)
            msg.setWindowTitle("Error")
            msg.setText("Cannot load project while recording is running. "
                        "Stop the recording or wait for it to finish.")
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.exec_()
            return

        if self.config_file is not None:
            selected_file = self.config_file
        else:
            selected_file = str(Path.home())

        selected_file, _ = QFileDialog.getOpenFileName(self, "Open Project", selected_file,
                                                       "Grimace Box Project Files (*.gb)")
        if not selected_file:
            return

        self.config_file = selected_file
        camera_top_config, camera_front_config, recording_config, video_files_config, grimace_config = \
            ConfigLoader.load(Path(self.config_file))

        error = CameraConfigValidator.validate(camera_top_config)
        if error is not None:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Unable to load top camera configuration")
            dlg.setText(error)
            dlg.setIcon(QMessageBox.Icon.Warning)
            dlg.exec()
            camera_top_config = CameraConfig()

        error = CameraConfigValidator.validate(camera_front_config)
        if error is not None:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Unable to load front camera configuration")
            dlg.setText(error)
            dlg.setIcon(QMessageBox.Icon.Warning)
            dlg.exec()
            camera_front_config = CameraConfig()

        if camera_top_config.camera_id is not None and camera_front_config.camera_id is not None:
            if camera_top_config.camera_id == camera_front_config.camera_id:
                dlg = QMessageBox(self)
                dlg.setWindowTitle("Unable to load camera configuration")
                dlg.setText("Top and front camera cannot have the same device ID")
                dlg.setIcon(QMessageBox.Icon.Warning)
                dlg.exec()
                camera_top_config = CameraConfig()
                camera_front_config = CameraConfig()

        error = RecordingConfigValidator.validate(recording_config)
        if error is not None:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Unable to load recording configuration")
            dlg.setText(error)
            dlg.setIcon(QMessageBox.Icon.Warning)
            dlg.exec()
            recording_config = RecordingConfig()
        self.recording_config_changed(recording_config)

        error = VideoFilesValidator.validate(video_files_config)
        if error is not None:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Unable to load video files configuration")
            dlg.setText(error)
            dlg.setIcon(QMessageBox.Icon.Warning)
            dlg.exec()
            video_files_config = VideoFilesConfig()
        self.video_files_config_changed(video_files_config)

        error = GrimaceConfigValidator.validate(grimace_config)
        if error is not None:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Unable to load grimace configuration")
            dlg.setText(error)
            dlg.setIcon(QMessageBox.Icon.Warning)
            dlg.exec()
            grimace_config = GrimaceConfig()
        self.grimace_config_changed(grimace_config)

        # Only start the camera thread once both cameras are configured
        try:
            self.setup_top_camera(camera_top_config, start=False)
        except Exception as e:
            self.on_top_camera_error(str(e))

        try:
            self.setup_front_camera(camera_front_config, start=False)
        except Exception as e:
            self.on_front_camera_error(str(e))

        if self.camera_recorder.top_camera is not None or self.camera_recorder.front_camera is not None:
            self.camera_recorder.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    window.update_video_label_size()

    sys.exit(app.exec())
