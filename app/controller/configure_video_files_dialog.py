import copy
from dataclasses import replace

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QFileDialog, QDialogButtonBox, QMessageBox

from app.config.video_files import VideoFilesConfig
from app.layout.configure_video_files_dialog import Ui_DConfigureVideoFiles
from app.validation.config.video_files_validator import VideoFilesValidator

import logging

logger = logging.getLogger("grimace_recorder.app.analysis.configure_video_files_dialog")

TOP_DEFAULTS = {
    "Incremental Number": "top_{recording_number}.avi",
    "Start Time": "top_{start_time}.avi",
    "Custom Template": "top_{start_time}_{recording_number}.avi"
}
FRONT_DEFAULTS = {
    "Incremental Number": "front_{recording_number}.avi",
    "Start Time": "front_{start_time}.avi",
    "Custom Template": "front_{start_time}_{recording_number}.avi"
}
GRIMACE_RESULTS_DEFAULTS = {
    "Incremental Number": "grimace_results_{recording_number}.csv",
    "Start Time": "grimace_results_{start_time}.csv",
    "Custom Template": "grimace_results_{start_time}_{recording_number}.csv"
}


class ConfigureVideoFiles(Ui_DConfigureVideoFiles, QDialog):
    applied_signal = Signal(VideoFilesConfig)

    def __init__(self, parent, video_files_config: VideoFilesConfig):
        logger.debug("FUN ConfigureVideoFiles.__init__")
        super().__init__(parent)
        self.setupUi(self)

        self.video_files_config = copy.deepcopy(video_files_config)
        self.last_video_files_config = copy.deepcopy(video_files_config)

        self.initialize_templates()

        if self.video_files_config.target_directory is not None:
            self.lbl_selected_folder.setText(self.video_files_config.target_directory)
        else:
            self.lbl_selected_folder.setText("No folder selected")

        if self.video_files_config.naming_mode is not None:
            self.dpd_naming_mode.setCurrentText(self.video_files_config.naming_mode)
        else:
            self.dpd_naming_mode.setCurrentIndex(-1)

        self.naming_mode_changed()

        self.dpd_naming_mode.currentTextChanged.connect(self.naming_mode_changed)
        self.txt_template_top.textChanged.connect(self.template_top_changed)
        self.txt_template_front.textChanged.connect(self.template_front_changed)
        self.txt_template_grimace.textChanged.connect(self.template_grimace_changed)

        self.btn_select_folder.clicked.connect(self.select_folder)
        self.btn_apply = self.btnbox_buttons.button(QDialogButtonBox.StandardButton.Apply)
        self.btn_apply.clicked.connect(self.apply)

        self.btnbox_buttons.accepted.connect(self.accept)
        self.btnbox_buttons.rejected.connect(self.reject)
        logger.debug("FUNEND ConfigureVideoFiles.__init__")

    def initialize_templates(self):
        """
        Initialize the templates in the local config with default values if they are not set
        """

        logger.debug("FU ConfigureVideoFiles.initialize_templates")
        def set_defaults(target, defaults):
            for mode, default in defaults.items():
                if mode not in target or target[mode] is None or target[mode] == "":
                    target[mode] = default

        set_defaults(self.video_files_config.top_templates, TOP_DEFAULTS)
        set_defaults(self.video_files_config.front_templates, FRONT_DEFAULTS)
        set_defaults(self.video_files_config.grimace_results_templates, GRIMACE_RESULTS_DEFAULTS)

    def naming_mode_changed(self):
        logger.debug("FU ConfigureRecording.recording_mode_changed")
        naming_mode = self.dpd_naming_mode.currentText()
        logger.info("Naming Mode Selected: %s", naming_mode)
        if naming_mode == "" or naming_mode is None:
            naming_mode = None
        self.video_files_config.naming_mode = naming_mode

        if naming_mode is None:
            self.txt_template_top.setReadOnly(True)
            self.txt_template_front.setReadOnly(True)
            self.txt_template_grimace.setReadOnly(True)

            self.txt_template_top.setDisabled(True)
            self.txt_template_front.setDisabled(True)
            self.txt_template_grimace.setDisabled(True)

            self.txt_template_top.setText("")
            self.txt_template_front.setText("")
            self.txt_template_grimace.setText("")
            return

        editable = self.video_files_config.naming_mode == "Custom Template"

        self.txt_template_top.setDisabled(False)
        self.txt_template_front.setDisabled(False)
        self.txt_template_grimace.setDisabled(False)

        self.txt_template_top.setReadOnly(not editable)
        self.txt_template_front.setReadOnly(not editable)
        self.txt_template_grimace.setReadOnly(not editable)

        self.txt_template_top.setText(self.video_files_config.top_templates[naming_mode])
        self.txt_template_front.setText(self.video_files_config.front_templates[naming_mode])
        self.txt_template_grimace.setText(self.video_files_config.grimace_results_templates[naming_mode])

    def template_top_changed(self):
        logger.debug("FU ConfigureRecording.recording_mode_changed")
        naming_mode = self.video_files_config.naming_mode
        template_top = self.txt_template_top.text()
        logger.info("Template Top Changed: %s", template_top)
        self.video_files_config.top_templates[naming_mode] = template_top

    def template_front_changed(self):
        logger.debug("FU ConfigureRecording.recording_mode_changed")
        naming_mode = self.video_files_config.naming_mode
        template_front = self.txt_template_front.text()
        logger.info("Template Front Changed: %s", template_front)
        self.video_files_config.front_templates[naming_mode] = template_front

    def template_grimace_changed(self):
        logger.debug("FU ConfigureRecording.recording_mode_changed")
        naming_mode = self.video_files_config.naming_mode
        template_grimace = self.txt_template_grimace.text()
        logger.info("Template Grimace Changed: %s", template_grimace)
        self.video_files_config.grimace_results_templates[naming_mode] = template_grimace

    def apply(self):
        logger.debug("FUN ConfigureRecording.apply")
        error = VideoFilesValidator.validate(self.video_files_config)

        if error is not None:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Invalid Configuration")
            dlg.setText(error)
            dlg.setIcon(QMessageBox.Icon.Warning)
            dlg.exec()
            raise ValueError("Invalid Configuration")

        self.last_video_files_config = replace(self.video_files_config)
        self.applied_signal.emit(self.video_files_config)
        logger.debug("FUNEND ConfigureRecording.apply")

    def accept(self):
        logger.debug("FUN ConfigureRecording.accept")
        if self.video_files_config != self.last_video_files_config:
            self.apply()
        super().accept()
        logger.debug("FUNEND ConfigureRecording.accept")

    def select_folder(self):
        logger.debug("FU ConfigureRecording.select_folder")
        dlg = QFileDialog(self)
        dlg.setFileMode(QFileDialog.FileMode.Directory)
        dlg.setNameFilter("Pylon Camera Configuration (*.pfs)")
        if dlg.exec():
            folder = dlg.selectedFiles()[0]
            self.lbl_selected_folder.setText(folder)
            self.video_files_config.target_directory = folder
