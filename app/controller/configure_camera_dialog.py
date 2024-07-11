from dataclasses import replace

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QFileDialog, QDialogButtonBox

from app.config.camera import CameraConfig
from app.layout.configure_camera_dialog import Ui_DConfigureCamera


class ConfigureCamera(Ui_DConfigureCamera, QDialog):
    applied_signal = Signal(CameraConfig)

    def __init__(self, parent, camera_config: CameraConfig, available_cameras: list[str]):
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

    def camera_changed(self):
        camera_id = self.dpd_camera.currentText()
        if camera_id is None or camera_id == "":
            camera_id = None
        self.camera_config.camera_id = camera_id

    def fps_changed(self):
        self.camera_config.fps = self.spb_fps.value()

    def apply(self):
        print("Applying camera configuration")
        self.last_camera_config = replace(self.camera_config)
        self.applied_signal.emit(self.camera_config)

    def accept(self):
        if self.camera_config != self.last_camera_config:
            self.apply()
        super().accept()

    def select_file(self):
        dlg = QFileDialog(self)
        dlg.setFileMode(QFileDialog.FileMode.ExistingFile)
        dlg.setNameFilter("Pylon Camera Configuration (*.pfs)")
        if dlg.exec():
            file = dlg.selectedFiles()[0]
            self.lbl_selected_file.setText(file)
            self.camera_config.config_file = file
        else:
            self.lbl_selected_file.setText("No file selected")
            self.camera_config.config_file = None
