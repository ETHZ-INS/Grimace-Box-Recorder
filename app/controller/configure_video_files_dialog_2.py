import copy

from PySide6.QtWidgets import QDialog, QFileDialog, QDialogButtonBox, QMessageBox

from app.layout.configure_video_files_dialog import Ui_DConfigureVideoFiles
from app.model.grimace_recorder_model import GrimaceRecorderModel
from app.validation.config.video_files_validator import VideoFilesValidator

import logging

from util.trace import Trace

logger = logging.getLogger("grimace_recorder.app.analysis.configure_video_files_dialog")


class ConfigureVideoFiles(Ui_DConfigureVideoFiles, QDialog):
    @Trace.trace(logger)
    def __init__(self, parent, model: GrimaceRecorderModel):
        super().__init__(parent)
        self.setupUi(self)

        self.model = model
        self.temp_config = copy.deepcopy(model.video_files_config)

        if self.temp_config.target_directory is not None:
            self.lbl_selected_folder.setText(self.temp_config.target_directory)
        else:
            self.lbl_selected_folder.setText("No folder selected")

        self.btn_select_folder.clicked.connect(self.select_folder)
        self.btn_apply = self.btnbox_buttons.button(QDialogButtonBox.StandardButton.Apply)
        self.btn_apply.clicked.connect(self.apply)

        self.btnbox_buttons.accepted.connect(self.accept)
        self.btnbox_buttons.rejected.connect(self.reject)

    @Trace.trace(logger)
    def apply(self):
        error = VideoFilesValidator.validate(self.temp_config)

        if error is not None:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Invalid Configuration")
            dlg.setText(error)
            dlg.setIcon(QMessageBox.Icon.Warning)
            dlg.exec()
            raise ValueError("Invalid Configuration")

        self.model.set_video_files_config(self.temp_config)

    @Trace.trace(logger)
    def accept(self):
        if self.temp_config != self.model.video_files_config:
            self.apply()
        super().accept()

    @Trace.trace(logger)
    def select_folder(self):
        dlg = QFileDialog(self)
        dlg.setFileMode(QFileDialog.FileMode.Directory)
        dlg.setNameFilter("Pylon Camera Configuration (*.pfs)")
        if dlg.exec():
            folder = dlg.selectedFiles()[0]
            self.lbl_selected_folder.setText(folder)
            self.temp_config.target_directory = folder
