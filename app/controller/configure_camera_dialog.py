from dataclasses import replace

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QFileDialog, QDialogButtonBox

from app.config.camera import CameraConfig
from app.layout.configure_camera_dialog import Ui_DConfigureCamera

import logging

logger = logging.getLogger("grimace_recorder.app.analysis.configure_camera_dialog")


class ConfigureCamera(Ui_DConfigureCamera, QDialog):
    applied_signal = Signal(CameraConfig)

    def __init__(self, parent, camera_config: CameraConfig, available_cameras: list[str]):
        logger.debug("FUN ConfigureCamera.__init__")
        super().__init__(parent)
        self.setupUi(self)

        self.camera_config = replace(camera_config)
        self.last_camera_config = replace(camera_config)

        self.dpd_camera.clear()
        self.dpd_camera.addItems([None] + available_cameras)
        if camera_config.camera_id is not None:
            self.dpd_camera.setCurrentText(camera_config.camera_id)
        else:
            self.dpd_camera.setCurrentIndex(-1)

        if camera_config.config_file is not None:
            self.lbl_selected_file.setText(camera_config.config_file)
        else:
            self.lbl_selected_file.setText("No file selected")

        self.spb_fps.setValue(camera_config.fps)

        self.dpd_camera.currentTextChanged.connect(self.camera_changed)
        self.btn_select_file.clicked.connect(self.select_file)
        self.spb_fps.valueChanged.connect(self.fps_changed)
        self.btn_apply = self.btnbox_buttons.button(QDialogButtonBox.StandardButton.Apply)
        self.btn_apply.clicked.connect(self.apply)
        logger.debug("FUNEND ConfigureCamera.__init__")

    def camera_changed(self):
        logger.debug("FU ConfigureCamera.camera_changed")
        camera_id = self.dpd_camera.currentText()
        logger.info("Selected camera ID: %s", camera_id)
        if camera_id is None or camera_id == "":
            camera_id = None
        self.camera_config.camera_id = camera_id

    def fps_changed(self):
        logger.debug("FU ConfigureCamera.fps_changed")
        fps = self.spb_fps.value()
        logger.info("Selected fps: %s", fps)
        self.camera_config.fps = fps

    def apply(self):
        logger.debug("FUN ConfigureCamera.apply")
        self.last_camera_config = replace(self.camera_config)
        self.applied_signal.emit(self.camera_config)
        logger.debug("FUNEND ConfigureCamera.apply")

    def accept(self):
        logger.debug("FUN ConfigureCamera.accept")
        if self.camera_config != self.last_camera_config:
            self.apply()
        super().accept()
        logger.debug("FUNEND ConfigureCamera.accept")

    def select_file(self):
        logger.debug("FUN ConfigureCamera.select_file")
        dlg = QFileDialog(self)
        dlg.setFileMode(QFileDialog.FileMode.ExistingFile)
        dlg.setNameFilter("Pylon Camera Configuration (*.pfs)")
        if dlg.exec():
            file = dlg.selectedFiles()[0]
            logger.info("Selected file: %s", file)
            self.lbl_selected_file.setText(file)
            self.camera_config.config_file = file
        else:
            self.lbl_selected_file.setText("No file selected")
            self.camera_config.config_file = None
        logger.debug("FUNEND ConfigureCamera.select_file")
