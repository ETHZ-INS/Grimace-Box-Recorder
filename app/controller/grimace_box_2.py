import logging
import math
from datetime import timedelta
from pathlib import Path
from typing import Tuple

import numpy as np
from PySide6 import QtCore
from PySide6.QtGui import QPixmap, QImage
from numpy import ndarray

from app.config.serialization.config_loader import ConfigLoader
from app.controller.configure_camera_dialog_2 import ConfigureCamera
from app.controller.configure_grimace_scoring_dialog_2 import ConfigureGrimaceAnalysis
from app.controller.configure_pose_tracking_dialog_2 import ConfigurePoseEstimation
from app.controller.configure_recording_dialog_2 import ConfigureRecording
from app.controller.configure_recording_name_dialog import ConfigureRecordingName
from app.controller.configure_video_files_dialog_2 import ConfigureVideoFiles
from app.model.grimace_recorder_model import GrimaceRecorderModel
from app.model.overview_renderer import OverviewRenderer
from app.recording.recording_manager_2 import RecordingManager

from util.trace import Trace
from PySide6.QtWidgets import QMainWindow, QMessageBox, QFileDialog, QProgressDialog

from app.layout.grimace_box import Ui_WGrimaceBox

logger = logging.getLogger("grimace_recorder.app.controller.grimace_box")
logger.log(logging.DEBUG, "Finished imports")


class MainWindow(Ui_WGrimaceBox, QMainWindow):
    @Trace.trace(logger)
    def __init__(self, model: GrimaceRecorderModel):
        super(MainWindow, self).__init__()

        self.model = model

        self.setupUi(self)

        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)

        self.setStyleSheet(":disabled { color: gray }")

        self.menuHelp.setEnabled(False)

        self.btn_record.setEnabled(False)
        self.lbl_message.setText("Not ready to record.")
        self.lbl_message.setStyleSheet("color: orange")
        self.lbl_time.setText("0:00:00")

        self.lbl_warnings.setText("")

        self.action_configure_top_camera.triggered.connect(self.configure_top_camera)
        self.action_configure_front_camera.triggered.connect(self.configure_front_camera)
        self.action_configure_recording.triggered.connect(self.configure_recording)
        self.action_configure_video_files.triggered.connect(self.configure_video_files)
        self.action_configure_grimace_scoring.triggered.connect(self.configure_grimace)
        self.action_configure_pose_tracking.triggered.connect(self.configure_pose)

        self.action_save_project.triggered.connect(self.save_project)
        self.action_save_project_as.triggered.connect(self.save_project_as)
        self.action_load_project.triggered.connect(self.load_project)

        self.model.debug_mode_signal.connect(self.on_debug_mode)

        self.model.recording_state_signal.connect(self.on_recording_state)
        self.model.recording_timer_time_signal.connect(self.on_recording_timer_time)

        self.model.top_camera_frame_signal.connect(self.on_top_camera_frame)
        self.model.front_camera_frame_signal.connect(self.on_front_camera_frame)

        self.model.top_camera_error_signal.connect(self.on_top_camera_error)
        self.model.front_camera_error_signal.connect(self.on_front_camera_error)

        self.model.overview_text_signal.connect(self.on_overview)
        self.model.warnings_text_signal.connect(self.on_warnings)

        self.model.message_box_signal.connect(self.on_message_box)
        self.model.progress_dialog_signal.connect(self.on_progress_dialog)
        self.model.progress_dialog_progress_signal.connect(self.on_progress_dialog_progress)

        self.btn_record.clicked.connect(self.btn_record_clicked)
        self.chb_identifier.stateChanged.connect(self.chb_identifier_state_changed)

        self.overview_renderer = OverviewRenderer(self.model)
        self.recording_manager = RecordingManager(self.model)
        self.config_loader = ConfigLoader(self.model)

        self.recording_manager.check_ready()

        # Keep track of the shapes of the frames to determine if the video labels need to be resized
        self.top_frame_shape = None
        self.front_frame_shape = None

        self.message_box = None
        self.progress_dialog = None

        self.on_debug_mode(self.model.debug_mode)
        self.on_recording_state(self.model.recording_state, self.model.recording_state_reason)
        self.on_recording_timer_time(self.model.recording_timer_time)
        self.on_top_camera_frame(self.model.top_camera_frame)
        self.on_top_camera_error(self.model.top_camera_error)
        self.on_front_camera_error(self.model.front_camera_error)
        self.on_front_camera_frame(self.model.front_camera_frame)

    def on_debug_mode(self, debug_mode: bool):
        self.lbl_debug_mode.setVisible(debug_mode)

    def chb_identifier_state_changed(self, ask_identifier: bool):
        self.model.set_ask_for_identifier(ask_identifier)

    def _set_menu_enabled(self, enabled: bool):
        self.action_configure_top_camera.setEnabled(enabled)
        self.action_configure_front_camera.setEnabled(enabled)
        self.menuRecording.setEnabled(enabled)
        self.menu_configure_cameras.setEnabled(enabled)
        self.action_configure_recording.setEnabled(enabled)
        self.action_configure_video_files.setEnabled(enabled)
        self.action_configure_grimace_scoring.setEnabled(enabled)
        self.action_configure_pose_tracking.setEnabled(enabled)
        self.action_load_project.setEnabled(enabled)

        self.chb_identifier.setEnabled(enabled)

        # Saving is always possible
        self.menuFile.setEnabled(True)
        self.action_save_project.setEnabled(True)
        self.action_save_project_as.setEnabled(True)

    def on_recording_state(self, recording_state: str, recording_state_reason: str, error: str = None):
        if recording_state == "starting":
            self.lbl_message.setText("Recording starting...")
            self.lbl_message.setStyleSheet("color: blue")
            self.btn_record.setText("Stop Recording")
            self.btn_record.setEnabled(False)
            self._set_menu_enabled(False)
        elif recording_state == "stopping":
            self.lbl_message.setText("Recording stopping...")
            self.lbl_message.setStyleSheet("color: blue")
            self.btn_record.setText("Stop Recording")
            self.btn_record.setEnabled(False)
            self._set_menu_enabled(False)
        elif recording_state == "recording":
            self.lbl_message.setText("Recording...")
            self.lbl_message.setStyleSheet("color: blue")
            self.btn_record.setText("Stop Recording")
            self.btn_record.setEnabled(True)
            self._set_menu_enabled(False)
        else:
            if error is not None:
                self.lbl_message.setText(error)
                self.lbl_message.setStyleSheet("color: red")

            if recording_state == "ready":
                if error is None:
                    self.lbl_message.setText("Ready to Record")
                    self.lbl_message.setStyleSheet("color: green")
                self.btn_record.setText("Start Recording")
                self.btn_record.setEnabled(True)
            elif recording_state == "not_ready":
                if error is None:
                    self.lbl_message.setText(recording_state_reason)
                    self.lbl_message.setStyleSheet("color: orange")
                self.btn_record.setText("Start Recording")
                self.btn_record.setEnabled(False)
            self._set_menu_enabled(True)

    def on_overview(self, overview: str):
        self.lbl_overview.setText(overview)

    def on_warnings(self, warnings: str):
        self.lbl_warnings.setText(warnings)

    def on_recording_timer_time(self, time: float):
        recording_time = str(timedelta(seconds=time))
        # Only show the first digit of the milliseconds
        if len(recording_time) > 7:
            recording_time = recording_time[:9]
        else:
            recording_time = recording_time + ".0"
        self.lbl_time.setText(recording_time)

    def _scale_frame(self, frame: np.ndarray, width: int, height: int) -> QPixmap:
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        if ch == 1:
            q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_Grayscale8)
        else:
            q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        frame = QPixmap.fromImage(q_img)

        frame = frame.scaled(width, height, QtCore.Qt.AspectRatioMode.KeepAspectRatio)

        return frame

    def update_video_label_size(self):
        # The width of the video preview labels is given by the layout. Both labels have the same width.
        # The height of the labels needs to be calculated based on the video frames. They need to have the same height.

        # The two video frames may have different aspect ratios.
        # Both frames need to be scaled to the width of the labels while preserving their aspect ratio.

        # The height of the labels is the maximum of the heights of the two frames,
        # so that both frames fit in the labels.

        label_width = self.lbl_video_top.width()

        def calculate_size(frame: np.ndarray) -> Tuple[int, int]:
            height, width, _ = frame.shape if frame is not None else (200, 250, 1)
            aspect_ratio = width / height
            height = math.ceil(label_width / aspect_ratio)
            return width, height

        top_frame = self.model.top_camera_frame
        front_frame = self.model.front_camera_frame

        # Store the shapes of the frames to determine if the labels need to be resized again
        self.top_frame_shape = top_frame.shape if top_frame is not None else None
        self.front_frame_shape = front_frame.shape if front_frame is not None else None

        video_top_width, video_top_height = calculate_size(top_frame)
        video_front_width, video_front_height = calculate_size(front_frame)

        max_height = max(video_top_height, video_front_height)

        self.lbl_video_front.setMinimumSize(250, max_height)
        self.lbl_video_top.setMinimumSize(250, max_height)
        self.lbl_video_front.setMaximumSize(800, max_height)
        self.lbl_video_top.setMaximumSize(800, max_height)

        self.on_top_camera_frame(top_frame)
        self.on_front_camera_frame(front_frame)

    def on_top_camera_frame(self, frame: ndarray | None):
        if self.model.top_camera_error is not None:
            return

        if (frame is None) != (self.top_frame_shape is None):
            self.update_video_label_size()
        elif frame is not None and frame.shape != self.top_frame_shape:
            self.update_video_label_size()

        if frame is None:
            self.lbl_video_top.setText("No Camera Feed")
            return

        video_label_width = self.lbl_video_top.width()
        video_label_height = self.lbl_video_top.height()

        frame = self._scale_frame(frame, video_label_width, video_label_height)

        self.lbl_video_top.setPixmap(frame)

    def on_front_camera_frame(self, frame: ndarray | None):
        if self.model.front_camera_error is not None:
            return

        if (frame is None) != (self.front_frame_shape is None):
            self.update_video_label_size()
        elif frame is not None and frame.shape != self.front_frame_shape:
            self.update_video_label_size()

        if frame is None:
            self.lbl_video_front.setText("No Camera Feed")
            return

        video_label_width = self.lbl_video_front.width()
        video_label_height = self.lbl_video_front.height()

        frame = self._scale_frame(frame, video_label_width, video_label_height)

        self.lbl_video_front.setPixmap(frame)

    def on_top_camera_error(self, error: str):
        # Setting the text removes the pixmap. If the error is set to None,
        # the frame will probably be set again right after, so we leave it as is.
        if error is not None:
            self.lbl_video_top.setText(error)

    def on_front_camera_error(self, error: str):
        if error is not None:
            self.lbl_video_front.setText(error)

    def configure_top_camera(self):
        dlg = ConfigureCamera(self, self.model, "top")
        dlg.exec()

    def configure_front_camera(self):
        dlg = ConfigureCamera(self, self.model, "front")
        dlg.exec()

    def configure_recording(self):
        dlg = ConfigureRecording(self, self.model)
        dlg.exec()

    def configure_video_files(self):
        dlg = ConfigureVideoFiles(self, self.model)
        dlg.exec()

    def configure_grimace(self):
        dlg = ConfigureGrimaceAnalysis(self, self.model)
        dlg.exec()

    def configure_pose(self):
        dlg = ConfigurePoseEstimation(self, self.model)
        dlg.exec()

    def _enter_identifier(self) -> bool:
        if self.chb_identifier.isChecked():
            dlg = ConfigureRecordingName(self, self.model)
            res = dlg.exec()
            return res == 1
        else:
            self.model.set_recording_name(None)
            return True

    def start_recording(self):
        if self.model.recording_state != "ready":
            return
        if not self._enter_identifier():
            return
        self.model.set_recording_starting()

    def _confirm_stop_recording(self) -> bool:
        msg = QMessageBox(parent=self)
        msg.setWindowTitle("Confirm")
        msg.setText("The recording is configured to stop automatically after a certain duration. "
                    "Do you want to stop it now?")
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.exec()

        if msg.result() == QMessageBox.StandardButton.No:
            return False
        return True

    def stop_recording(self):
        if self.model.recording_state != "recording":
            return
        if self.model.auto_stop and not self._confirm_stop_recording():
            return
        self.model.set_recording_stopping()

    def btn_record_clicked(self):
        if self.model.recording_state == "recording":
            self.stop_recording()
        else:
            self.start_recording()

    def _select_save_file(self):
        if self.model.config_file is None:
            # Default path when opening the file dialog
            selected_file = str(Path.home() / "project.gb")
        else:
            selected_file = self.model.config_file

        file_filter = "Grimace Box Project Files (*.gb)"
        selected_file, _ = QFileDialog.getSaveFileName(self, "Save Project", selected_file, file_filter)

        return selected_file

    def _select_load_file(self):
        if self.model.config_file is None:
            # Default path when opening the file dialog
            directory = str(Path.home())
        else:
            directory = self.model.config_file

        file_filter = "Grimace Box Project Files (*.gb)"
        selected_file, _ = QFileDialog.getOpenFileName(self, "Load Project", directory, file_filter)

        return selected_file

    def save_project(self):
        if self.model.config_file is None:
            self.save_project_as()
        # TODO: Save the project

    def save_project_as(self):
        selected_file = self._select_save_file()
        if selected_file:
            self.model.config_file = selected_file
            self.save_project()

    def load_project(self):
        selected_file = self._select_load_file()
        if selected_file:
            self.model.config_file = selected_file
        self.model.set_loading()

    def on_message_box(self, state: str, title: str, text: str):
        if state == "hidden":
            if self.message_box is not None:
                self.message_box.close()
                self.message_box = None
        elif state == "visible":
            if self.message_box is None:
                self.message_box = QMessageBox(parent=self)
            self.message_box.setWindowTitle(title)
            self.message_box.setText(text)
            self.message_box.setIcon(QMessageBox.Icon.Information)
            self.message_box.exec()
            if self.model.message_box_state == "visible":
                self.model.close_message_box()

    def on_progress_dialog(self, state: str, title: str, text: str, progress: int):
        if state == "finished":
            if self.progress_dialog is not None:
                self.progress_dialog.close()
                self.progress_dialog = None
        elif state == "running":
            if self.progress_dialog is None:
                self.progress_dialog = QProgressDialog(text, "", 0, 100, self)
                self.progress_dialog.setWindowTitle(title)
                self.progress_dialog.setCancelButton(None)
                # Disable the close button so the user can't close it manually
                # to ensure that the UI stays frozen until the progress dialog is finished
                self.progress_dialog.setWindowFlag(QtCore.Qt.WindowType.WindowCloseButtonHint, False)
                self.progress_dialog.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
                self.progress_dialog.setMinimumDuration(0)
                self.progress_dialog.setValue(progress)
            else:
                self.progress_dialog.setValue(progress)

    def on_progress_dialog_progress(self, text: str, progress: int):
        if self.progress_dialog is not None:
            self.progress_dialog.setLabelText(text)
            self.progress_dialog.setValue(progress)

    # region Window Events

    def resizeEvent(self, event):
        self.update_video_label_size()

    def closeEvent(self, event):
        # Delete the overview renderer to make sure its signals are disconnected from the model
        del self.overview_renderer

    # endregion
