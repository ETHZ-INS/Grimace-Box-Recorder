import os
import sys
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Literal

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QFileDialog, QDialogButtonBox

from app.config.camera import CameraConfig
from app.config.hard_config import load_camera_ids
from app.layout.configure_camera_dialog import Ui_DConfigureCamera

import logging

from app.model.devices import Devices
from app.model.grimace_recorder_model import GrimaceRecorderModel
from util.trace import Trace

logger = logging.getLogger("grimace_box."+__name__)


class ConfigureCamera(Ui_DConfigureCamera, QDialog):
    @Trace.trace(logger)
    def __init__(self, parent, model: GrimaceRecorderModel, camera: Literal["top", "front"]):
        super().__init__(parent)
        self.setupUi(self)

        self.model = model
        self.camera = camera

        self.temp_config = deepcopy(model.recording.top_camera_config if camera == "top" else model.recording.front_camera_config)

        # Video File instead of a camera is only available in debug mode
        debug_mode = model.debug_mode
        if not debug_mode:
            self.temp_config.camera_type = "Pylon"

        self.frm_camera_type.setVisible(debug_mode)

        self.dpd_camera_type.setCurrentText(self.temp_config.camera_type)

        if self.temp_config.camera_type == "Pylon":
            self.stk_camera.setCurrentIndex(0)
        elif self.temp_config.camera_type == "Video File":
            self.stk_camera.setCurrentIndex(1)
        else:
            self.stk_camera.setCurrentIndex(-1)

        available_cameras = Devices.get_available_cameras()

        hard_top_camera_id, hard_front_camera_id = load_camera_ids()
        hard_camera_id = hard_top_camera_id if camera == "top" else hard_front_camera_id
        cameras_in_use = [model.recording.front_camera_config.camera_id if camera == "top" else model.recording.top_camera_config.camera_id]

        if hard_camera_id is None or debug_mode:
            available_cameras = [camera for camera in available_cameras if camera not in cameras_in_use]
        else:
            available_cameras = [camera for camera in available_cameras if camera == hard_camera_id]
            self.dpd_camera.setEnabled(False)

        self.dpd_camera.clear()
        self.dpd_camera.addItems([None] + available_cameras)  # Add None to allow the user to unselect the camera
        if self.temp_config.camera_id is not None and self.temp_config.camera_id in available_cameras:
            self.dpd_camera.setCurrentText(self.temp_config.camera_id)
        else:
            self.dpd_camera.setCurrentIndex(-1)

        if self.temp_config.video_file is not None:
            self.lbl_selected_video_file.setText(self.temp_config.video_file)
        else:
            self.lbl_selected_video_file.setText("No file selected")

        self.dpd_camera.currentTextChanged.connect(self.camera_changed)
        self.dpd_camera_type.currentTextChanged.connect(self.camera_type_changed)
        self.btn_select_video_file.clicked.connect(self.select_video_file)
        self.btn_apply = self.btnbox_buttons.button(QDialogButtonBox.StandardButton.Apply)
        self.btn_apply.clicked.connect(self.apply)

    @Trace.trace(logger)
    def camera_type_changed(self, *_):
        camera_type = self.dpd_camera_type.currentText()
        logger.info("Selected camera type: %s", camera_type)
        self.temp_config.camera_type = camera_type
        if camera_type == "Pylon":
            self.stk_camera.setCurrentIndex(0)
        elif camera_type == "Video File":
            self.stk_camera.setCurrentIndex(1)

    @Trace.trace(logger)
    def camera_changed(self, *_):
        camera_id = self.dpd_camera.currentText()
        logger.info("Selected camera ID: %s", camera_id)
        if camera_id is None or camera_id == "":
            camera_id = None
        self.temp_config.camera_id = camera_id

    @Trace.trace(logger)
    def apply(self):
        if self.camera == "top":
            self.model.recording.set_top_camera_config(self.temp_config)
        else:
            self.model.recording.set_front_camera_config(self.temp_config)

    @Trace.trace(logger)
    def accept(self):
        if self.temp_config != self.model.recording.top_camera_config if self.camera == "top" else self.model.recording.front_camera_config:
            self.apply()
        super().accept()

    @Trace.trace(logger)
    def select_video_file(self):
        dlg = QFileDialog(self)
        dlg.setFileMode(QFileDialog.FileMode.ExistingFile)
        dlg.setNameFilter("AVI file (*.avi)")
        if dlg.exec():
            file = dlg.selectedFiles()[0]
            logger.info("Selected video file: %s", file)
            self.lbl_selected_video_file.setText(file)
            self.temp_config.video_file = file
        else:
            self.lbl_selected_video_file.setText("No file selected")
            self.temp_config.video_file = None
