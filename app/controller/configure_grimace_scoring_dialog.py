from dataclasses import replace
from typing import List, Tuple

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QDialogButtonBox

from app.config.grimace import GrimaceConfig
from app.layout.configure_grimace_scoring_dialog import Ui_DConfigureGrimaceScoring

import logging

from util.trace import Trace

logger = logging.getLogger("grimace_recorder.app.analysis.configure_grimace_scoring_dialog")


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

    @Trace.trace(logger)
    def __init__(self, parent, grimace_config: GrimaceConfig, available_devices: List[Tuple[str, str]], debug_mode: bool = False):
        super().__init__(parent)
        self.setupUi(self)

        self.grimace_config = replace(grimace_config)
        self.last_grimace_config = replace(grimace_config)

        self.chb_enable_grimace.setChecked(grimace_config.enabled)

        grimace_models = grimace_config.GRIMACE_MODELS
        if not debug_mode:
            grimace_models = [model for model in grimace_models if model != "Demo (Fake Mouse)"]
        self.dpd_grimace_model.clear()
        self.dpd_grimace_model.addItems(grimace_models)
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

    @Trace.trace(logger)
    def enable_grimace_changed(self, *_):
        grimace_enabled = self.chb_enable_grimace.isChecked()
        self.grimace_config.enabled = grimace_enabled
        logger.info("Grimace Analysis Enabled: %s", grimace_enabled)

        self.dpd_grimace_model.setEnabled(self.grimace_config.enabled)
        self.dpd_frame_interval.setEnabled(self.grimace_config.enabled)
        self.dpd_frame_quality_device.setEnabled(self.grimace_config.enabled)
        self.dpd_face_cropper_device.setEnabled(self.grimace_config.enabled)
        self.dpd_grimace_scoring_device.setEnabled(self.grimace_config.enabled)

    @Trace.trace(logger)
    def grimace_model_changed(self, *_):
        grimace_model = self.dpd_grimace_model.currentText()
        self.grimace_config.grimace_model = grimace_model
        logger.info("Grimace Analysis Enabled: %s", grimace_model)

    @Trace.trace(logger)
    def frame_interval_changed(self, *_):
        frame_interval = self.dpd_frame_interval.currentData()
        self.grimace_config.frame_interval = frame_interval
        logger.info("Frame Interval Selected: %s", frame_interval)

    @Trace.trace(logger)
    def face_quality_device_changed(self, *_):
        frame_quality_device = self.dpd_frame_quality_device.currentData()
        self.grimace_config.frame_quality_device = frame_quality_device
        logger.info("Frame Quality Device Selected: %s", frame_quality_device)

    @Trace.trace(logger)
    def face_cropper_device_changed(self, *_):
        face_cropper_device = self.dpd_face_cropper_device.currentData()
        self.grimace_config.face_cropper_device = face_cropper_device
        logger.info("Face Cropper Device Selected: %s", face_cropper_device)

    @Trace.trace(logger)
    def grimace_scoring_device_changed(self, *_):
        grimace_scoring_device = self.dpd_grimace_scoring_device.currentData()
        self.grimace_config.grimace_scoring_device = grimace_scoring_device
        logger.info("Grimace Scoring Device Selected: %s", grimace_scoring_device)

    @Trace.trace(logger)
    def apply(self):
        self.last_grimace_config = replace(self.grimace_config)
        self.applied_signal.emit(self.grimace_config)

    @Trace.trace(logger)
    def accept(self):
        if self.grimace_config != self.last_grimace_config:
            self.apply()
        super().accept()
