import logging
import os
from pathlib import Path

from app.controller.configure_pose_tracking_dialog import ConfigurePoseTracking
from app.recording.recording_timer import RecordingTimer

from util.trace import Trace

from datetime import timedelta
import math
from typing import List, Tuple

import numpy as np
import torch

from PySide6 import QtCore
from PySide6.QtGui import QImage, QPixmap, QShortcut, QKeySequence
from PySide6.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QProgressDialog
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
from app.recording.recording_manager import RecordingManager2
from app.validation.config.camera_config_validator import CameraConfigValidator
from app.validation.config.grimace_config_validator import GrimaceConfigValidator
from app.validation.config.recording_config_validator import RecordingConfigValidator
from app.validation.config.video_files_validator import VideoFilesConfigValidator
from app.dataflow.qvariable import QVariable

logger = logging.getLogger("grimace_recorder.app.controller.grimace_box")
logger.log(logging.DEBUG, "Finished imports")

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
    @Trace.trace(logger)
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.setStyleSheet(":disabled { color: gray }")

        self.menuHelp.setEnabled(False)

        self.debug_mode = False
        self.lbl_debug_mode.setVisible(False)

        self.action_configure_top_camera.triggered.connect(self.configure_top_camera)
        self.action_configure_front_camera.triggered.connect(self.configure_front_camera)
        self.action_configure_recording.triggered.connect(self.configure_recording)
        self.action_configure_video_files.triggered.connect(self.configure_video_files)

        self.action_save_project.triggered.connect(self.save_project)
        self.action_save_project_as.triggered.connect(self.save_project_as)
        self.action_load_project.triggered.connect(self.load_project)

        self.action_configure_grimace_scoring.triggered.connect(self.configure_grimace_scoring)
        self.action_open_grimace_results_window.triggered.connect(self.open_grimace_results_window)

        self.action_configure_pose_tracking.triggered.connect(self.configure_pose_tracking)

        self.btn_record.clicked.connect(self.btn_record_clicked)

        self.config_file = None

        self.preview_buffer_top = QVariable()
        self.preview_buffer_top.value_set.connect(self.on_video_frame_top)

        self.preview_buffer_front = QVariable()
        self.preview_buffer_front.value_set.connect(self.on_video_frame_front)

        self.demo_shortcut = QShortcut(self)
        self.demo_shortcut.setKey(QKeySequence("CTRL+D"))

        self.demo_shortcut.activated.connect(self.enable_debug_mode)

        self.recording_manager = RecordingManager2()
        self.recording_manager.recording_builder.set_top_preview(self.preview_buffer_top)
        self.recording_manager.recording_builder.set_front_preview(self.preview_buffer_front)

        self.recording_manager.timestamp_signal.connect(self.update_timer)

        #self.recording_manager.overview_changed_signal.connect(self.overview_changed)
        #self.recording_manager.warnings_changed_signal.connect(self.warnings_changed)
        self.recording_manager.recording_started_signal.connect(self.recording_started)
        self.recording_manager.recording_stopped_signal.connect(self.recording_stopped)
        #self.recording_manager.recording_error_signal.connect(self.on_recording_error)
        #self.recording_manager.analysis_error_signal.connect(self.on_analysis_error)
        #self.recording_manager.top_camera_error_signal.connect(self.on_top_camera_error)
        #self.recording_manager.front_camera_error_signal.connect(self.on_front_camera_error)

        self.grimace_results_window = None

        self.frame_extractor_input_buffer = None
        self.grimace_frames = None
        self.frame_extractor = None

        #self.overview_changed()
        self.update_menubar()
        self.update_recording_button()

        QThread.currentThread().setPriority(QThread.Priority.LowPriority)

    def enable_debug_mode(self):
        self.debug_mode = True
        self.lbl_debug_mode.setVisible(True)

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

    @Trace.trace(logger)
    def update_menubar(self):
        actions_enabled = not (self.recording_manager.recording is not None and self.recording_manager.recording.running)
        self.action_configure_top_camera.setEnabled(actions_enabled)
        self.action_configure_front_camera.setEnabled(actions_enabled)
        self.menu_configure_cameras.setEnabled(actions_enabled)
        self.action_configure_recording.setEnabled(actions_enabled)
        self.action_configure_video_files.setEnabled(actions_enabled)
        self.action_configure_grimace_scoring.setEnabled(actions_enabled)
        self.action_load_project.setEnabled(actions_enabled)
        self.action_save_project.setEnabled(True)
        self.action_save_project_as.setEnabled(True)

    @Trace.trace(logger)
    def update_recording_button(self):
#        message = self.recording_manager.get_not_ready_reason()
#
#        self.btn_record.setEnabled(message is None)

        if self.recording_manager.state == RecordingManager2.RecordingState.Recording:
            self.btn_record.setText("Stop Recording")
        else:
            self.btn_record.setText("Start Recording")

    @Trace.trace(logger)
    def update_video_label_size(self):
        label_width = self.lbl_video_top.width()

        def calculate_size(camera_recorder) -> Tuple[int, int]:
            width = camera_recorder.get_width() if camera_recorder is not None else 250
            height = camera_recorder.get_height() if camera_recorder is not None else 200
            aspect_ratio = width / height
            height = math.ceil(label_width / aspect_ratio)
            return width, height

        video_top_width, video_top_height = calculate_size(self.recording_manager.camera_recorder.top_camera)
        video_front_width, video_front_height = calculate_size(self.recording_manager.camera_recorder.front_camera)
        max_height = max(video_top_height, video_front_height)

        self.lbl_video_front.setMinimumSize(250, max_height)
        self.lbl_video_top.setMinimumSize(250, max_height)
        self.lbl_video_front.setMaximumSize(800, max_height)
        self.lbl_video_top.setMaximumSize(800, max_height)

        if self.recording_manager.camera_recorder.top_camera is not None:
            self.on_video_frame_top()
        if self.recording_manager.camera_recorder.front_camera is not None:
            self.on_video_frame_front()

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
        if isinstance(frame, tuple):
            frame = frame[0]

        if frame is None:
            return

        video_label_width = self.lbl_video_top.width()
        video_label_height = self.lbl_video_top.height()

        frame = self.process_frame(frame, video_label_width, video_label_height)

        self.lbl_video_top.setPixmap(frame)

    def on_video_frame_front(self):
        # TODO: update timer
#        if self.recording_manager.recording.recording_context:
#            recording_time = 0.0
#            if self.recording_manager.recording.recording_context.started:
#                recording_time = self.recording_manager.recording.recording_context.recording_time()
#
#            recording_time_string = str(timedelta(seconds=recording_time))
#            self.lbl_time.setText(recording_time_string)

        frame = self.preview_buffer_front.get()
        if isinstance(frame, tuple):
            frame = frame[0]

        if frame is None:
            return

        video_label_width = self.lbl_video_front.width()
        video_label_height = self.lbl_video_front.height()

        frame = self.process_frame(frame, video_label_width, video_label_height)

        self.lbl_video_front.setPixmap(frame)

    def update_timer(self, time: float):
        recording_time = str(timedelta(seconds=time))
        self.lbl_time.setText(recording_time)

    @Trace.trace(logger)
    def setup_top_camera(self, camera_config: CameraConfig, start: bool = True):
        self.recording_manager.configure_top_camera(camera_config)
        #self.recording_manager.reset_error()

        camera_ready = True
        if camera_config.camera_type == "Pylon" and camera_config.camera_id is None:
            camera_ready = False
        elif camera_config.camera_type == "Video File" and camera_config.video_file is None:
            camera_ready = False

        if not camera_ready:
            self.lbl_video_top.clear()
            self.lbl_video_top.setText("Top camera not configured")
        self.update_video_label_size()

    @Trace.trace(logger)
    def setup_front_camera(self, camera_config: CameraConfig, start: bool = True):
        self.recording_manager.configure_front_camera(camera_config)
        #self.recording_manager.reset_error()

        camera_ready = True
        if camera_config.camera_type == "Pylon" and camera_config.camera_id is None:
            camera_ready = False
        elif camera_config.camera_type == "Video File" and camera_config.video_file is None:
            camera_ready = False

        if not camera_ready:
            self.lbl_video_front.clear()
            self.lbl_video_front.setText("Front camera not configured")
        self.update_video_label_size()

    @Trace.trace(logger)
    def configure_top_camera(self):
        available_cameras = self.get_available_cameras()

        # TODO: Hide cameras already in use
        #if self.recording_manager.recording_builder.front_camera_config is not None:
        #    if self.recording_manager.recording_builder.front_camera_config.camera_id is not None:
        #        if self.recording_manager.recording_builder.front_camera_config.camera_id in available_cameras:
        #            available_cameras.remove(self.recording_manager.recording_builder.front_camera_config.camera_id)

        dlg = ConfigureCamera(self, self.recording_manager.top_camera_config, available_cameras, debug_mode=self.debug_mode)
        dlg.setWindowTitle("Configure Top Camera")
        dlg.applied_signal.connect(self.setup_top_camera)
        dlg.exec()

    @Trace.trace(logger)
    def configure_front_camera(self):
        available_cameras = self.get_available_cameras()

        # TODO: Hide cameras already in use
        #if self.recording_manager.recording_builder.top_camera_config is not None:
        #    if self.recording_manager.recording_builder.top_camera_config.camera_id is not None:
        #        if self.recording_manager.recording_builder.top_camera_config.camera_id in available_cameras:
        #            available_cameras.remove(self.recording_manager.recording_builder.top_camera_config.camera_id)

        dlg = ConfigureCamera(self, self.recording_manager.front_camera_config, available_cameras, debug_mode=self.debug_mode)
        dlg.setWindowTitle("Configure Front Camera")
        dlg.applied_signal.connect(self.setup_front_camera)
        dlg.exec()

    @Trace.trace(logger, level=logging.WARNING)
    def on_recording_error(self, _: str):
        self.overview_changed()
        self.update_menubar()
        self.update_recording_button()

    @Trace.trace(logger, level=logging.WARNING)
    def on_analysis_error(self, _: str):
        self.overview_changed()
        self.update_menubar()
        self.update_recording_button()

    @Trace.trace(logger, level=logging.WARNING)
    def on_top_camera_error(self, error: str):
        self.lbl_video_top.setText(error)
        self.update_menubar()
        self.update_recording_button()

    @Trace.trace(logger, level=logging.WARNING)
    def on_front_camera_error(self, error: str):
        self.lbl_video_front.setText(error)
        self.update_menubar()
        self.update_recording_button()

    @Trace.trace(logger, level=logging.WARNING)
    def recording_config_changed(self, recording_config: RecordingConfig):
        self.recording_manager.recording_builder.configure_recording(recording_config)
        #self.recording_manager.configure_recording(recording_config)
        #self.recording_manager.reset_error()

    @Trace.trace(logger)
    def configure_recording(self):
        dlg = ConfigureRecording(self, self.recording_manager.recording_builder.temp_config)
        dlg.applied_signal.connect(self.recording_config_changed)
        dlg.exec()

    @Trace.trace(logger)
    def video_files_config_changed(self, video_files_config: VideoFilesConfig):
        self.recording_manager.recording_builder.recording_number = 1
        self.recording_manager.recording_builder.configure_video_files(video_files_config)
        #self.recording_manager.configure_video_files(video_files_config)
        #self.recording_manager.reset_error()

    @Trace.trace(logger)
    def configure_video_files(self):
        dlg = ConfigureVideoFiles(self, self.recording_manager.recording_builder.temp_config)
        dlg.applied_signal.connect(self.video_files_config_changed)
        dlg.exec()

    @Trace.trace(logger)
    def grimace_config_changed(self, grimace_config):
        self.recording_manager.recording_builder.configure_grimace(grimace_config)
        #self.recording_manager.configure_grimace(grimace_config)
        #self.recording_manager.reset_error()

    @Trace.trace(logger)
    def configure_grimace_scoring(self):
        available_devices = self.get_available_devices()
        dlg = ConfigureGrimaceScoring(self, self.recording_manager.recording_builder.temp_config, available_devices, debug_mode=self.debug_mode)
        dlg.applied_signal.connect(self.grimace_config_changed)
        dlg.exec()

    @Trace.trace(logger)
    def pose_config_changed(self, pose_config):
        self.recording_manager.recording_builder.configure_pose_estimation(pose_config)
        #self.recording_manager.configure_pose_tracking(pose_config)
        #self.recording_manager.reset_error()

    @Trace.trace(logger)
    def configure_pose_tracking(self):
        available_devices = self.get_available_devices()
        dlg = ConfigurePoseTracking(self, self.recording_manager.recording_builder.pose_config, available_devices, debug_mode=self.debug_mode)
        dlg.applied_signal.connect(self.pose_config_changed)
        dlg.exec()

    @Trace.trace(logger)
    def overview_changed(self):
        recording_running = self.recording_manager.recording is not None and self.recording_manager.recording.running
        recording_state = "running recording" if recording_running else "next recording"

        recording_number = self.recording_manager.recording_builder.recording_number
        if recording_number is None:
            recording_number = "Not configured"
        else:
            recording_number = str(recording_number)

        recording_mode = self.recording_manager.recording_builder.temp_config.mode
        if recording_mode is None:
            recording_duration = "Not configured"
        elif recording_mode == "Manual":
            recording_duration = "Manual"
        elif recording_mode == "Timed":
            recording_duration = self.recording_manager.recording_builder.temp_config.duration
            if recording_duration is not None:
                recording_duration = str(timedelta(seconds=recording_duration))
            else:
                recording_duration = "Not Configured"
        else:
            recording_duration = "Not Configured"

        top_camera_fps = self.recording_manager.recording_builder.top_camera_config.fps
        if top_camera_fps is None:
            top_camera_fps = "Not configured"
        else:
            top_camera_fps = str(top_camera_fps) + " FPS"

        front_camera_fps = self.recording_manager.recording_builder.front_camera_config.fps
        if front_camera_fps is None:
            front_camera_fps = "Not configured"
        else:
            front_camera_fps = str(front_camera_fps) + " FPS"

        top_video_file = self.recording_manager.recording_builder.top_video_writer_builder.video_file
        if top_video_file is None:
            top_video_file = "Not configured"
        else:
            top_video_file = str(top_video_file)

        front_video_file = self.recording_manager.recording_builder.front_video_writer_builder.video_file
        if front_video_file is None:
            front_video_file = "Not configured"
        else:
            front_video_file = str(front_video_file)

        if self.recording_manager.recording_builder.temp_config is None:
            grimace_enabled = "Not configured"
            grimace_overview = ""
        else:
            grimace_enabled = "Enabled" if self.recording_manager.recording_builder.temp_config.enabled else "Disabled"

            if self.recording_manager.recording_builder.temp_config.enabled:
                grimace_model = self.recording_manager.recording_builder.temp_config.grimace_model
                if grimace_model is None:
                    grimace_model = "Not configured"
                frame_interval = self.recording_manager.recording_builder.temp_config.frame_interval
                if frame_interval is None:
                    frame_interval_str = "Not configured"
                else:
                    frame_interval_seconds = round(self.recording_manager.recording_builder.temp_config.frame_interval)

                    minutes = frame_interval_seconds // 60
                    seconds = frame_interval_seconds % 60

                    minutes_str = f"{minutes} Minutes" if minutes > 1 else ("1 Minute" if minutes == 1 else "")
                    seconds_str = f"{seconds} Seconds" if seconds > 1 else ("1 Second" if seconds == 1 else "")

                    frame_interval_str = minutes_str + (" " if minutes and seconds else "") + seconds_str

                grimace_overview = GRIMACE_OVERVIEW_TEMPLATE.format(
                    grimace_model=grimace_model,
                    frame_interval=frame_interval_str,
                    grimace_results_file=self.recording_manager.recording_builder.front_video_pipeline_builder.grimace_results_file
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

        message = self.recording_manager.get_not_ready_reason()
        if self.recording_manager.recording_error is not None:
            logger.info("STATUS Recording Stopped: %s", self.recording_manager.recording_error)
            self.lbl_message.setText("Recording Stopped: " + self.recording_manager.recording_error)
            self.lbl_message.setStyleSheet("color: red")
        elif message is not None:
            logger.info("STATUS Not ready: %s", message)
            self.lbl_message.setText("Not ready: " + message)
            self.lbl_message.setStyleSheet("color: red")
        elif recording_running:
            logger.info("STATUS Recording")
            self.lbl_message.setText("Recording...")
            self.lbl_message.setStyleSheet("color: blue")
        else:
            logger.info("STATUS Ready to record")
            self.lbl_message.setText("Ready to record")
            self.lbl_message.setStyleSheet("color: green")

        self.update_menubar()
        self.update_recording_button()

    @Trace.trace(logger)
    def warnings_changed(self):
        pass
        #warnings = self.recording_manager.get_warnings()
        #if warnings:
        #    warning_title = "## Warnings:  \n"
        #    warning_text = warning_title + ("  \n".join(warnings))
        #    logger.warning("Warnings Text: %s", warning_text)
        #    self.lbl_warnings.setText(warning_text)
        #else:
        #    self.lbl_warnings.setText("")

    @Trace.trace(logger)
    def open_grimace_results_window(self):
        if self.grimace_results_window is not None and self.grimace_results_window.isVisible():
            return

        if self.grimace_results_window is not None:
            self.grimace_results_window.close()

#        self.grimace_results_window = GrimaceResults(self, self.recording_manager.grimace_results_list)
#        self.grimace_results_window.show()

    @Trace.trace(logger)
    def recording_started(self):
        if self.recording_manager.recording_builder.temp_config.enabled:
            self.open_grimace_results_window()
        self.update_menubar()
        self.update_recording_button()
        self.warnings_changed()

    @Trace.trace(logger)
    def recording_stopped(self):
        self.update_menubar()
        self.update_recording_button()
        self.warnings_changed()

    @Trace.trace(logger)
    def start_recording(self):
        self.recording_manager.start_recording()

    @Trace.trace(logger)
    def stop_recording(self):
        if self.recording_manager.recording_builder.temp_config.mode == "Timed":
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

    @Trace.trace(logger)
    def btn_record_clicked(self):
        if not (self.recording_manager.recording is not None and self.recording_manager.recording.running):
            self.start_recording()
        else:
            self.stop_recording()

    @Trace.trace(logger)
    def closeEvent(self, event):
        if self.recording_manager.recording is not None and self.recording_manager.recording.running:
            msg = QMessageBox(parent=self)
            msg.setWindowTitle("Confirm")
            msg.setText("The recording is configured to stop automatically after a certain duration. "
                        "Do you want to stop it now?")
            msg.setIcon(QMessageBox.Icon.Question)
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg.exec()

            if msg.result() == QMessageBox.StandardButton.No:
                event.ignore()
                return

        self.recording_manager.stop_recording()

        super(MainWindow, self).closeEvent(event)

    @Trace.trace(logger)
    def save_project(self):
        if self.config_file is None:
            return self.save_project_as()
        top_camera_config = self.recording_manager.recording_builder.top_camera_config
        front_camera_config = self.recording_manager.recording_builder.front_camera_config
        recording_config = self.recording_manager.recording_builder.temp_config
        video_files_config = self.recording_manager.recording_builder.temp_config
        grimace_config = self.recording_manager.recording_builder.temp_config
        pose_top_config = self.recording_manager.recording_builder.pose_config
        ConfigLoader.save(Path(self.config_file), top_camera_config, front_camera_config,
                          recording_config, video_files_config, grimace_config, pose_top_config)

    @Trace.trace(logger)
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

    @Trace.trace(logger)
    def load_project(self):
        if self.recording_manager.recording is not None and self.recording_manager.recording.running:
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

        progress = QProgressDialog("Loading configuration...", "", 0, 100, self)
        progress.setWindowTitle("Loading project...")
        progress.setCancelButton(None)
        progress.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)

        progress.setValue(10)

        self.config_file = selected_file
        try:
            top_camera_config, front_camera_config, recording_config, video_files_config, grimace_config, pose_top_config = \
                ConfigLoader.load(Path(self.config_file))
        except Exception as e:
            logger.exception("Error loading project file")
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Error loading project file")
            dlg.setText("An error occurred while loading the project file. Check the log for details.")
            dlg.setIcon(QMessageBox.Icon.Critical)
            dlg.exec()
            return

        progress.setValue(20)
        progress.setLabelText("Applying configuration...")

        error = CameraConfigValidator.validate(top_camera_config)
        if error is not None:
            logger.warning("Error loading top camera config: %s %s", error, top_camera_config)
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Unable to load top camera configuration")
            dlg.setText(error)
            dlg.setIcon(QMessageBox.Icon.Warning)
            dlg.exec()
            top_camera_config = CameraConfig()

        progress.setValue(25)

        error = CameraConfigValidator.validate(front_camera_config)
        if error is not None:
            logger.warning("Error loading front camera config: %s %s", error, front_camera_config)
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Unable to load front camera configuration")
            dlg.setText(error)
            dlg.setIcon(QMessageBox.Icon.Warning)
            dlg.exec()
            front_camera_config = CameraConfig()

        progress.setValue(30)

        if top_camera_config.camera_id is not None and front_camera_config.camera_id is not None:
            if top_camera_config.camera_id == front_camera_config.camera_id:
                logger.warning("Error loading camera config: Identical camera ids %s %s", top_camera_config, front_camera_config)
                dlg = QMessageBox(self)
                dlg.setWindowTitle("Unable to load camera configuration")
                dlg.setText("Top and front camera cannot have the same device ID")
                dlg.setIcon(QMessageBox.Icon.Warning)
                dlg.exec()
                top_camera_config = CameraConfig()
                front_camera_config = CameraConfig()

        progress.setValue(35)

        error = RecordingConfigValidator.validate(recording_config)
        if error is not None:
            logger.warning("Error loading recording config: %s %s", error, recording_config)
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Unable to load recording configuration")
            dlg.setText(error)
            dlg.setIcon(QMessageBox.Icon.Warning)
            dlg.exec()
            recording_config = RecordingConfig()
        self.recording_config_changed(recording_config)

        progress.setValue(40)

        error = VideoFilesConfigValidator.validate(video_files_config)
        if error is not None:
            logger.warning("Error loading files config: %s %s", error, video_files_config)
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Unable to load video files configuration")
            dlg.setText(error)
            dlg.setIcon(QMessageBox.Icon.Warning)
            dlg.exec()
            video_files_config = VideoFilesConfig()
        self.video_files_config_changed(video_files_config)

        progress.setValue(45)

        error = GrimaceConfigValidator.validate(grimace_config)
        if error is not None:
            logger.warning("Error loading analysis config: %s %s", error, grimace_config)
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Unable to load grimace configuration")
            dlg.setText(error)
            dlg.setIcon(QMessageBox.Icon.Warning)
            dlg.exec()
            grimace_config = GrimaceConfig()
        self.grimace_config_changed(grimace_config)

        progress.setValue(50)

        # TODO: Implement pose config validation
        self.pose_config_changed(pose_top_config)

        progress.setValue(60)
        progress.setLabelText("Starting cameras...")

        # Only start the camera thread once both cameras are configured
        try:
            self.setup_top_camera(top_camera_config, start=False)
        except Exception as e:
            self.on_top_camera_error(str(e))

        try:
            self.setup_front_camera(front_camera_config, start=False)
        except Exception as e:
            self.on_front_camera_error(str(e))

        progress.setValue(100)

        # TODO: Is this correct?
        #self.recording_manager.start_preview()
