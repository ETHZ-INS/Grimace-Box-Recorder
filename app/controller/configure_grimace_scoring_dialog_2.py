from copy import deepcopy

from PySide6.QtWidgets import QDialog, QDialogButtonBox

from app.layout.configure_grimace_scoring_dialog import Ui_DConfigureGrimaceScoring

import logging

from app.model.devices import Devices
from app.model.grimace_recorder_model import GrimaceRecorderModel
from util.trace import Trace

logger = logging.getLogger("grimace_recorder.app.analysis.configure_grimace_scoring_dialog")


class ConfigureGrimaceAnalysis(Ui_DConfigureGrimaceScoring, QDialog):
    @Trace.trace(logger)
    def __init__(self, parent, model: GrimaceRecorderModel):
        super().__init__(parent)
        self.setupUi(self)

        self.model = model
        self.temp_config = deepcopy(model.grimace_config)

        debug_mode = model.debug_mode

        self.chb_enable_grimace.setChecked(self.temp_config.enabled)

        grimace_models = self.temp_config.GRIMACE_MODELS
        if not debug_mode:
            grimace_models = [model for model in grimace_models if model != "Demo (Fake Mouse)"]
        self.dpd_grimace_model.clear()
        self.dpd_grimace_model.addItems(grimace_models)
        if self.temp_config.grimace_model is not None:
            self.dpd_grimace_model.setCurrentText(self.temp_config.grimace_model)
        else:
            self.dpd_grimace_model.setCurrentIndex(-1)

        self.dpd_frame_interval.clear()
        for option in self.temp_config.FRAME_INTERVAL_OPTIONS:
            self.dpd_frame_interval.addItem(option[0], option[1])

        if self.temp_config.frame_interval is not None:
            frame_interval_seconds = round(self.temp_config.frame_interval)
            current_index = self.dpd_frame_interval.findData(frame_interval_seconds)
            self.dpd_frame_interval.setCurrentIndex(current_index)
        else:
            self.dpd_frame_interval.setCurrentIndex(-1)

        available_devices = Devices.get_computation_devices()

        self.dpd_frame_quality_device.clear()
        for device in available_devices:
            self.dpd_frame_quality_device.addItem(device[1], device[0])
        current_index = self.dpd_frame_quality_device.findData(self.temp_config.frame_quality_device)
        self.dpd_frame_quality_device.setCurrentIndex(current_index)

        self.dpd_face_cropper_device.clear()
        for device in available_devices:
            self.dpd_face_cropper_device.addItem(device[1], device[0])
        current_index = self.dpd_face_cropper_device.findData(self.temp_config.face_cropper_device)
        self.dpd_face_cropper_device.setCurrentIndex(current_index)

        self.dpd_grimace_scoring_device.clear()
        for device in available_devices:
            self.dpd_grimace_scoring_device.addItem(device[1], device[0])
        current_index = self.dpd_grimace_scoring_device.findData(self.temp_config.grimace_scoring_device)
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
        self.temp_config.enabled = grimace_enabled
        logger.info("Grimace Analysis Enabled: %s", grimace_enabled)

        self.dpd_grimace_model.setEnabled(self.temp_config.enabled)
        self.dpd_frame_interval.setEnabled(self.temp_config.enabled)
        self.dpd_frame_quality_device.setEnabled(self.temp_config.enabled)
        self.dpd_face_cropper_device.setEnabled(self.temp_config.enabled)
        self.dpd_grimace_scoring_device.setEnabled(self.temp_config.enabled)

    @Trace.trace(logger)
    def grimace_model_changed(self, *_):
        grimace_model = self.dpd_grimace_model.currentText()
        self.temp_config.grimace_model = grimace_model
        logger.info("Grimace Analysis Enabled: %s", grimace_model)

    @Trace.trace(logger)
    def frame_interval_changed(self, *_):
        frame_interval = self.dpd_frame_interval.currentData()
        self.temp_config.frame_interval = frame_interval
        logger.info("Frame Interval Selected: %s", frame_interval)

    @Trace.trace(logger)
    def face_quality_device_changed(self, *_):
        frame_quality_device = self.dpd_frame_quality_device.currentData()
        self.temp_config.frame_quality_device = frame_quality_device
        logger.info("Frame Quality Device Selected: %s", frame_quality_device)

    @Trace.trace(logger)
    def face_cropper_device_changed(self, *_):
        face_cropper_device = self.dpd_face_cropper_device.currentData()
        self.temp_config.face_cropper_device = face_cropper_device
        logger.info("Face Cropper Device Selected: %s", face_cropper_device)

    @Trace.trace(logger)
    def grimace_scoring_device_changed(self, *_):
        grimace_scoring_device = self.dpd_grimace_scoring_device.currentData()
        self.temp_config.grimace_scoring_device = grimace_scoring_device
        logger.info("Grimace Scoring Device Selected: %s", grimace_scoring_device)

    @Trace.trace(logger)
    def apply(self):
        self.model.set_grimace_config(self.temp_config)

    @Trace.trace(logger)
    def accept(self):
        if self.temp_config != self.model.grimace_config:
            self.apply()
        super().accept()
