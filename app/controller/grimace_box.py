import logging
import math
import os
import sys
from copy import deepcopy
from datetime import timedelta
from pathlib import Path
from typing import Tuple

import numpy as np
from PySide6 import QtCore
from PySide6.QtGui import QPixmap, QImage, QShortcut, QKeySequence
from numpy import ndarray

from app.config.hard_config import load_camera_ids
from app.config.serialization.config_loader import ConfigLoader
from app.controller.configure_camera_dialog import ConfigureCamera
from app.controller.configure_grimace_scoring_dialog import ConfigureGrimaceAnalysis
from app.controller.configure_pose_tracking_dialog import ConfigurePoseEstimation
from app.controller.configure_recording_dialog import ConfigureRecording
from app.controller.configure_recording_name_dialog import ConfigureRecordingName
from app.controller.grimace_results_widget import GrimaceResults
from app.model.grimace_recorder_model import GrimaceRecorderModel, RecordingState, MessageBoxState, ProgressDialogState, \
    ApplicationState
from app.model.overview_renderer import OverviewRenderer
from app.recording.recording_manager_2 import RecordingManager

from util.trace import Trace
from PySide6.QtWidgets import QMainWindow, QMessageBox, QFileDialog, QProgressDialog

from app.layout.grimace_box import Ui_WGrimaceBox

logger = logging.getLogger("grimace_box."+__name__)
logger.log(logging.WARNING, "Finished imports")

bundle_dir = getattr(sys, '_MEIPASS', os.getcwd())
camera_config_folder = Path(os.path.abspath(os.path.join(bundle_dir, 'camera_config')))

top_camera_config_file = camera_config_folder / "top.pfs"
front_camera_config_file = camera_config_folder / "front.pfs"


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
        self.action_change_target_directory.triggered.connect(self.configure_video_files)
        self.action_configure_grimace_scoring.triggered.connect(self.configure_grimace)
        self.action_configure_pose_tracking.triggered.connect(self.configure_pose)

        self.action_open_grimace_results_window.triggered.connect(self.open_grimace_results_window)

        self.action_save_project.triggered.connect(self.save_project)
        self.action_save_project_as.triggered.connect(self.save_project_as)
        self.action_load_project.triggered.connect(self.load_project)

        self.model.debug_mode_signal.connect(self.on_debug_mode)

        self.model.recording.recording_state_signal.connect(self.on_recording_state)
        self.model.recording.recording_timer_time_signal.connect(self.on_recording_timer_time)

        self.model.top_camera_frame_signal.connect(self.on_top_camera_frame)
        self.model.front_camera_frame_signal.connect(self.on_front_camera_frame)

        self.model.recording.top_camera_error_signal.connect(self.on_top_camera_error)
        self.model.recording.front_camera_error_signal.connect(self.on_front_camera_error)

        self.model.overview_text_signal.connect(self.on_overview)
        self.model.warnings_text_signal.connect(self.on_warnings)

        self.model.message_box.change_signal.connect(self.on_message_box_change)
        self.model.progress_dialog.change_signal.connect(self.on_progress_dialog_change)
        self.model.progress_dialog.progress_signal.connect(self.on_progress_dialog_progress)

        self.btn_record.clicked.connect(self.btn_record_clicked)
        self.chb_identifier.stateChanged.connect(self.chb_identifier_state_changed)

        self.demo_shortcut = QShortcut(self)
        self.demo_shortcut.setKey(QKeySequence("CTRL+D"))
        self.demo_shortcut.activated.connect(self.enable_debug_mode)

        self.overview_renderer = OverviewRenderer(self.model)
        self.recording_manager = RecordingManager(self.model)
        self.config_loader = ConfigLoader(self.model)

        self.recording_manager.check_ready()

        # Keep track of the shapes of the frames to determine if the video labels need to be resized
        self.top_frame_shape = None
        self.front_frame_shape = None

        self.message_box = None
        self.progress_dialog = None

        self.grimace_results_window = None

        self.on_debug_mode(self.model.debug_mode)
        self.on_recording_state(self.model.recording.recording_state, self.model.recording.recording_state_reason)
        self.on_recording_timer_time(self.model.recording.recording_timer_time)
        self.on_top_camera_frame(self.model.top_camera_frame)
        self.on_top_camera_error(self.model.recording.top_camera_error)
        self.on_front_camera_error(self.model.recording.front_camera_error)
        self.on_front_camera_frame(self.model.front_camera_frame)

        # Load hard coded camera ids for collaborators
        top_camera_id, front_camera_id = load_camera_ids()
        self.model.recording.top_camera_config.camera_id = top_camera_id
        self.model.recording.front_camera_config.camera_id = front_camera_id
        self.model.recording.top_camera_config.config_file = str(top_camera_config_file)
        self.model.recording.front_camera_config.config_file = str(front_camera_config_file)

        self.model.recording.apply_all_configs()

    @Trace.trace(logger)
    def on_debug_mode(self, debug_mode: bool):
        self.lbl_debug_mode.setVisible(debug_mode)

    @Trace.trace(logger)
    def enable_debug_mode(self):
        self.model.set_debug_mode(True)

    @Trace.trace(logger)
    def chb_identifier_state_changed(self, ask_identifier: bool):
        self.model.set_ask_for_identifier(ask_identifier)

    @Trace.trace(logger)
    def _set_menu_enabled(self, enabled: bool):
        self.action_configure_top_camera.setEnabled(enabled)
        self.action_configure_front_camera.setEnabled(enabled)
        self.menuRecording.setEnabled(enabled)
        self.menu_configure_cameras.setEnabled(enabled)
        self.action_configure_recording.setEnabled(enabled)
        self.action_change_target_directory.setEnabled(enabled)
        self.action_configure_grimace_scoring.setEnabled(enabled)
        self.action_configure_pose_tracking.setEnabled(enabled)
        self.action_load_project.setEnabled(enabled)

        self.chb_identifier.setEnabled(enabled)

        # Saving is always possible
        self.menuFile.setEnabled(True)
        self.action_save_project.setEnabled(True)
        self.action_save_project_as.setEnabled(True)

    @Trace.trace(logger)
    def _set_status_message(self, message: str, color: str, error: str = None):
        if error is not None:
            message = f"<span style='color: red'> Recording Stopped: {error}</span>  \n" + message
        self.lbl_message.setText(message)
        self.lbl_message.setStyleSheet(f"color: {color}")

    @Trace.trace(logger)
    def _set_start_button(self, start: bool, enabled: bool):
        if start:
            self.btn_record.setText("Start Recording")
        else:
            self.btn_record.setText("Stop Recording")
        self.btn_record.setEnabled(enabled)

    @Trace.trace(logger)
    def on_recording_state(self, recording_state: RecordingState, recording_state_reason: str, error: str = None):
        if self.model.application_state == ApplicationState.CLOSING and recording_state not in (
                RecordingState.RECORDING, RecordingState.STARTING, RecordingState.STOPPING):
            self.close()
            return

        if recording_state == RecordingState.STARTING:
            self._set_status_message("Recording starting...", "blue")
            self._set_start_button(False, False)
            self._set_menu_enabled(False)
        elif recording_state == RecordingState.STOPPING:
            self._set_status_message("Recording stopping...", "blue")
            self._set_start_button(False, False)
            self._set_menu_enabled(False)
        elif recording_state == RecordingState.RECORDING:
            self._set_status_message("Recording...", "blue")
            self._set_start_button(False, True)
            self._set_menu_enabled(False)
        else:
            # An error is not shown if the recording state is "recording", "starting" or "stopping".
            # I do not remember why I did this, but it means the backend needs to handle the error and
            # set the recording state to either "ready" or "not_ready" if an error occurs during recording.

            # I couldn't make error a state, because there can be an error during the recording, but at the same time
            # the application may be ready to record again. So I had to make the error a separate thing. The states
            # are mutually exclusive, but the error can coexist with at least some of the states.
            if recording_state == RecordingState.IDLE:
                self._set_status_message("Not ready", "orange", error)
                self._set_start_button(True, False)
                self._set_menu_enabled(False)
            elif recording_state == RecordingState.NOT_READY:
                self._set_status_message("Not ready: " + recording_state_reason, "orange", error)
                self._set_start_button(True, False)
                self._set_menu_enabled(True)
            elif recording_state == RecordingState.CHANGING_CONFIG:
                self._set_status_message(recording_state_reason, "orange", error)
                self._set_start_button(True, False)
                self._set_menu_enabled(False)
            elif recording_state == RecordingState.READY:
                self._set_status_message("Ready to Record", "green", error)
                self._set_start_button(True, True)
                self._set_menu_enabled(True)

    @Trace.trace(logger)
    def on_overview(self, overview: str):
        self.lbl_overview.setText(overview)

    @Trace.trace(logger)
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

    @Trace.trace(logger)
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
        if self.model.recording.top_camera_error is not None:
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

        #cv2.imshow("top", frame)
        #cv2.waitKey(1)

        frame = self._scale_frame(frame, video_label_width, video_label_height)

        self.lbl_video_top.setPixmap(frame)

    def on_front_camera_frame(self, frame: ndarray | None):
        if self.model.recording.front_camera_error is not None:
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

        #cv2.imshow("front", frame)
        #cv2.waitKey(1)

        frame = self._scale_frame(frame, video_label_width, video_label_height)

        self.lbl_video_front.setPixmap(frame)

    @Trace.trace(logger, level=logging.WARNING)
    def on_top_camera_error(self, error: str):
        # Setting the text removes the pixmap. If the error is set to None,
        # the frame will probably be set again right after, so we leave it as is.
        if error is not None:
            self.lbl_video_top.setText(error)

    @Trace.trace(logger, level=logging.WARNING)
    def on_front_camera_error(self, error: str):
        if error is not None:
            self.lbl_video_front.setText(error)

    @Trace.trace(logger)
    def configure_top_camera(self):
        dlg = ConfigureCamera(self, self.model, "top")
        dlg.exec()

    @Trace.trace(logger)
    def configure_front_camera(self):
        dlg = ConfigureCamera(self, self.model, "front")
        dlg.exec()

    @Trace.trace(logger)
    def configure_recording(self):
        dlg = ConfigureRecording(self, self.model)
        dlg.exec()

    @Trace.trace(logger)
    def _select_target_directory(self):
        if self.model.config_file is None:
            # Default path when opening the file dialog
            selected_file = str(Path.home() / "project.gb")
        else:
            selected_file = self.model.config_file

        file_filter = "Grimace Box Project Files (*.gb)"
        selected_file, _ = QFileDialog.getSaveFileName(self, "Select Target Folder", selected_file, file_filter)

        return selected_file

    @Trace.trace(logger)
    def configure_video_files(self):
        video_files_config = deepcopy(self.model.recording.video_files_config)

        if video_files_config.target_directory is None:
            # Default path when opening the file dialog
            directory = str(Path.home())
        else:
            directory = video_files_config.target_directory

        selected_directory = QFileDialog.getExistingDirectory(self, "Select Target Directory", directory)
        if selected_directory:
            video_files_config.target_directory = selected_directory
            self.model.recording.set_video_files_config(video_files_config)

    @Trace.trace(logger)
    def configure_grimace(self):
        dlg = ConfigureGrimaceAnalysis(self, self.model)
        dlg.exec()

    @Trace.trace(logger)
    def configure_pose(self):
        dlg = ConfigurePoseEstimation(self, self.model)
        dlg.exec()

    @Trace.trace(logger)
    def _enter_identifier(self) -> bool:
        if self.chb_identifier.isChecked():
            dlg = ConfigureRecordingName(self, self.model)
            res = dlg.exec()
            return res == 1
        else:
            self.model.recording.set_recording_name(None)
            return True

    @Trace.trace(logger)
    def start_recording(self):
        if self.model.recording.recording_state != RecordingState.READY:
            return
        if not self._enter_identifier():
            return
        self.model.recording.grimace_results.clear()
        self.model.recording.set_recording_starting()
        self.open_grimace_results_window()

    @Trace.trace(logger)
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

    @Trace.trace(logger)
    def stop_recording(self):
        if self.model.recording.recording_state != RecordingState.RECORDING:
            return
        if self.model.recording.recording_config.mode == "Timed" and not self._confirm_stop_recording():
            return
        self.model.recording.set_recording_stopping()

    @Trace.trace(logger)
    def btn_record_clicked(self):
        if self.model.recording.recording_state == RecordingState.RECORDING:
            self.stop_recording()
        else:
            self.start_recording()

    @Trace.trace(logger)
    def open_grimace_results_window(self):
        if self.grimace_results_window is not None and self.grimace_results_window.isVisible():
            return

        if self.grimace_results_window is not None:
            self.grimace_results_window.close()

        self.grimace_results_window = GrimaceResults(self, self.model)
        self.grimace_results_window.show()

    @Trace.trace(logger)
    def _select_save_file(self):
        if self.model.config_file is None:
            # Default path when opening the file dialog
            selected_file = str(Path.home() / "project.gb")
        else:
            selected_file = self.model.config_file

        file_filter = "Grimace Box Project Files (*.gb)"
        selected_file, _ = QFileDialog.getSaveFileName(self, "Save Project", selected_file, file_filter)

        return selected_file

    @Trace.trace(logger)
    def _select_load_file(self):
        if self.model.config_file is None:
            # Default path when opening the file dialog
            directory = str(Path.home())
        else:
            directory = self.model.config_file

        file_filter = "Grimace Box Project Files (*.gb)"
        selected_file, _ = QFileDialog.getOpenFileName(self, "Load Project", directory, file_filter)

        return selected_file

    @Trace.trace(logger)
    def save_project(self):
        if self.model.config_file is None:
            self.save_project_as()
        self.config_loader.save(Path(self.model.config_file))

    @Trace.trace(logger)
    def save_project_as(self):
        selected_file = self._select_save_file()
        if selected_file:
            self.model.config_file = selected_file
            self.save_project()

    @Trace.trace(logger)
    def load_project(self):
        selected_file = self._select_load_file()
        if selected_file:
            self.model.config_file = selected_file
        self.model.set_loading(True)

    @Trace.trace(logger)
    def on_message_box_change(self, state: str, title: str, text: str):
        if state == MessageBoxState.VISIBLE:
            if self.message_box is not None:
                self.message_box.close()
                self.message_box = None
        elif state == MessageBoxState.VISIBLE:
            if self.message_box is None:
                self.message_box = QMessageBox(parent=self)
            self.message_box.setWindowTitle(title)
            self.message_box.setText(text)
            self.message_box.setIcon(QMessageBox.Icon.Information)
            self.message_box.exec()
            if self.model.message_box.state == MessageBoxState.VISIBLE:
                self.model.recording.close_message_box()

    @Trace.trace(logger)
    def on_progress_dialog_change(self, state: str, title: str, text: str, progress: int):
        if state == ProgressDialogState.FINISHED:
            if self.progress_dialog is not None:
                self.progress_dialog.close()
                self.progress_dialog = None
        elif state == ProgressDialogState.RUNNING:
            if self.progress_dialog is None:
                self.progress_dialog = QProgressDialog(text, "", 0, 100, self)
                self.progress_dialog.setWindowTitle(title)
                # noinspection PyTypeChecker
                self.progress_dialog.setCancelButton(None)
                # Disable the close button so the user can't close it manually
                # to ensure that the UI stays frozen until the progress dialog is finished
                self.progress_dialog.setWindowFlag(QtCore.Qt.WindowType.WindowCloseButtonHint, False)
                self.progress_dialog.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
                self.progress_dialog.setMinimumDuration(0)
                self.progress_dialog.setValue(progress)
            else:
                self.progress_dialog.setValue(progress)

    @Trace.trace(logger)
    def on_progress_dialog_progress(self, text: str, progress: int):
        if self.progress_dialog is not None:
            self.progress_dialog.setLabelText(text)
            self.progress_dialog.setValue(progress)

    # region Window Events

    @Trace.trace(logger)
    def resizeEvent(self, event):
        self.update_video_label_size()

    @Trace.trace(logger)
    def closeEvent(self, event):
        # TODO: do we need this check?
        if self.model.application_state != ApplicationState.CLOSING:
            self.model.set_application_closing()

        if self.model.recording.recording_state in (RecordingState.RECORDING, RecordingState.STARTING, RecordingState.STOPPING):
            self.stop_recording()
            event.ignore()
            return

    # endregion
