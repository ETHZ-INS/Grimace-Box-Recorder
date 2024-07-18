from dataclasses import replace
from typing import List, Tuple

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QDialogButtonBox

from app.config.grimace import GrimaceConfig
from app.layout.configure_grimace_scoring_dialog import Ui_DConfigureGrimaceScoring


FRAME_INTERVAL_OPTIONS = [
    ("10 Seconds", 10.0),
    ("20 Seconds", 20.0),
    ("30 Seconds", 30.0),
    ("1 Minute", 60.0),
    ("2 Minutes", 120.0),
    ("5 Minutes", 300.0)
]


class ConfigureGrimaceScoring(Ui_DConfigureGrimaceScoring, QDialog):
    applied_signal = Signal(GrimaceConfig)

    def __init__(self, parent, grimace_config: GrimaceConfig, available_devices: List[Tuple[str, str]]):
        super().__init__(parent)
        self.setupUi(self)

        self.grimace_config = replace(grimace_config)
        self.last_grimace_config = replace(grimace_config)

        self.chb_enable_grimace.setChecked(grimace_config.enabled)

        self.dpd_grimace_model.clear()
        self.dpd_grimace_model.addItem("V1 - SuperScorer")
        if grimace_config.grimace_model is not None:
            self.dpd_grimace_model.setCurrentText(grimace_config.grimace_model)
        else:
            self.dpd_grimace_model.setCurrentIndex(-1)

        self.dpd_frame_interval.clear()
        for option in FRAME_INTERVAL_OPTIONS:
            self.dpd_frame_interval.addItem(option[0], option[1])

        if grimace_config.frame_interval is not None:
            frame_interval_seconds = round(grimace_config.frame_interval)
            current_index = self.dpd_frame_interval.findData(frame_interval_seconds)
            self.dpd_frame_interval.setCurrentIndex(current_index)
        else:
            self.dpd_frame_interval.setCurrentIndex(-1)

        self.dpd_frame_quality_device.clear()
        for device in available_devices:
            self.dpd_frame_quality_device.addItem(device[1], device[0])
        current_index = self.dpd_frame_quality_device.findData(grimace_config.frame_quality_device)
        self.dpd_frame_quality_device.setCurrentIndex(current_index)

        self.dpd_face_cropper_device.clear()
        for device in available_devices:
            self.dpd_face_cropper_device.addItem(device[1], device[0])
        current_index = self.dpd_face_cropper_device.findData(grimace_config.face_cropper_device)
        self.dpd_face_cropper_device.setCurrentIndex(current_index)

        self.dpd_grimace_scoring_device.clear()
        for device in available_devices:
            self.dpd_grimace_scoring_device.addItem(device[1], device[0])
        current_index = self.dpd_grimace_scoring_device.findData(grimace_config.grimace_scoring_device)
        self.dpd_grimace_scoring_device.setCurrentIndex(current_index)

        self.chb_enable_grimace.stateChanged.connect(self.enable_grimace_changed)
        self.dpd_grimace_model.currentTextChanged.connect(self.grimace_model_changed)
        self.dpd_frame_interval.currentTextChanged.connect(self.frame_interval_changed)

        self.dpd_frame_quality_device.currentIndexChanged.connect(self.face_quality_device_changed)
        self.dpd_face_cropper_device.currentIndexChanged.connect(self.face_cropper_device_changed)
        self.dpd_grimace_scoring_device.currentIndexChanged.connect(self.grimace_scoring_device_changed)

        self.btn_apply = self.btnbox_buttons.button(QDialogButtonBox.StandardButton.Apply)
        self.btn_apply.clicked.connect(self.apply)

        self.enable_grimace_changed()

    def enable_grimace_changed(self):
        self.grimace_config.enabled = self.chb_enable_grimace.isChecked()

        self.dpd_grimace_model.setEnabled(self.grimace_config.enabled)
        self.dpd_frame_interval.setEnabled(self.grimace_config.enabled)
        self.dpd_frame_quality_device.setEnabled(self.grimace_config.enabled)
        self.dpd_face_cropper_device.setEnabled(self.grimace_config.enabled)
        self.dpd_grimace_scoring_device.setEnabled(self.grimace_config.enabled)

    def grimace_model_changed(self):
        self.grimace_config.grimace_model = self.dpd_grimace_model.currentText()

    def frame_interval_changed(self):
        self.grimace_config.frame_interval = self.dpd_frame_interval.currentData()

    def face_quality_device_changed(self):
        self.grimace_config.frame_quality_device = self.dpd_frame_quality_device.currentData()

    def face_cropper_device_changed(self):
        self.grimace_config.face_cropper_device = self.dpd_face_cropper_device.currentData()

    def grimace_scoring_device_changed(self):
        self.grimace_config.grimace_scoring_device = self.dpd_grimace_scoring_device.currentData()

    def apply(self):
        print("Applying grimace configuration")
        self.last_grimace_config = replace(self.grimace_config)
        self.applied_signal.emit(self.grimace_config)

    def accept(self):
        if self.grimace_config != self.last_grimace_config:
            self.apply()
        super().accept()
