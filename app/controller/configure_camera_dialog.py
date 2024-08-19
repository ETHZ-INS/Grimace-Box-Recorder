from dataclasses import replace

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QFileDialog, QDialogButtonBox

from app.config.camera import CameraConfig
from app.layout.configure_camera_dialog import Ui_DConfigureCamera

import logging

from util.trace import Trace

logger = logging.getLogger("grimace_recorder.app.analysis.configure_camera_dialog")


class ConfigureCamera(Ui_DConfigureCamera, QDialog):
    applied_signal = Signal(CameraConfig)

    @Trace.trace(logger)
    def __init__(self, parent, camera_config: CameraConfig, available_cameras: list[str], debug_mode: bool = False):
        super().__init__(parent)
        self.setupUi(self)

        self.camera_config = replace(camera_config)
        self.last_camera_config = replace(camera_config)

        self.dpd_camera_type.setCurrentText(camera_config.camera_type)

        self.frm_camera_type.setVisible(debug_mode)

        self.stk_camera.setCurrentIndex(0)
        if debug_mode and camera_config.camera_type == "Video File":
            self.stk_camera.setCurrentIndex(1)

        self.dpd_camera.clear()
        self.dpd_camera.addItems([None] + available_cameras)
        if camera_config.camera_id is not None:
            self.dpd_camera.setCurrentText(camera_config.camera_id)
        else:
            self.dpd_camera.setCurrentIndex(-1)

        if camera_config.config_file is not None:
            self.lbl_selected_config_file.setText(camera_config.config_file)
        else:
            self.lbl_selected_config_file.setText("No file selected")

        if camera_config.video_file is not None:
            self.lbl_selected_video_file.setText(camera_config.video_file)
        else:
            self.lbl_selected_video_file.setText("No file selected")

        self.spb_fps.setValue(camera_config.fps)

        self.dpd_camera.currentTextChanged.connect(self.camera_changed)
        self.dpd_camera_type.currentTextChanged.connect(self.camera_type_changed)
        self.btn_select_config_file.clicked.connect(self.select_config_file)
        self.btn_select_video_file.clicked.connect(self.select_video_file)
        self.spb_fps.valueChanged.connect(self.fps_changed)
        self.btn_apply = self.btnbox_buttons.button(QDialogButtonBox.StandardButton.Apply)
        self.btn_apply.clicked.connect(self.apply)

    @Trace.trace(logger)
    def camera_type_changed(self, *_):
        camera_type = self.dpd_camera_type.currentText()
        logger.info("Selected camera type: %s", camera_type)
        self.camera_config.camera_type = camera_type
        if camera_type == "Pylon":
            self.stk_camera.setCurrentIndex(0)
        elif camera_type == "Video File":
            print("Switching layout")
            self.stk_camera.setCurrentIndex(1)

    @Trace.trace(logger)
    def camera_changed(self, *_):
        camera_id = self.dpd_camera.currentText()
        logger.info("Selected camera ID: %s", camera_id)
        if camera_id is None or camera_id == "":
            camera_id = None
        self.camera_config.camera_id = camera_id

    @Trace.trace(logger)
    def fps_changed(self, *_):
        fps = self.spb_fps.value()
        logger.info("Selected fps: %s", fps)
        self.camera_config.fps = fps

    @Trace.trace(logger)
    def apply(self):
        self.last_camera_config = replace(self.camera_config)
        self.applied_signal.emit(self.camera_config)

    @Trace.trace(logger)
    def accept(self):
        if self.camera_config != self.last_camera_config:
            self.apply()
        super().accept()

    @Trace.trace(logger)
    def select_config_file(self):
        dlg = QFileDialog(self)
        dlg.setFileMode(QFileDialog.FileMode.ExistingFile)
        dlg.setNameFilter("Pylon Camera Configuration (*.pfs)")
        if dlg.exec():
            file = dlg.selectedFiles()[0]
            logger.info("Selected config file: %s", file)
            self.lbl_selected_config_file.setText(file)
            self.camera_config.config_file = file
        else:
            self.lbl_selected_config_file.setText("No file selected")
            self.camera_config.config_file = None

    @Trace.trace(logger)
    def select_video_file(self):
        dlg = QFileDialog(self)
        dlg.setFileMode(QFileDialog.FileMode.ExistingFile)
        dlg.setNameFilter("AVI file (*.avi)")
        if dlg.exec():
            file = dlg.selectedFiles()[0]
            logger.info("Selected video file: %s", file)
            self.lbl_selected_video_file.setText(file)
            self.camera_config.video_file = file
        else:
            self.lbl_selected_video_file.setText("No file selected")
            self.camera_config.video_file = None
