from copy import deepcopy

from PySide6.QtCore import QTime
from PySide6.QtWidgets import QDialog, QDialogButtonBox

from app.layout.configure_recording_dialog import Ui_DConfigureRecording

import logging

from app.model.grimace_recorder_model import GrimaceRecorderModel
from util.trace import Trace

logger = logging.getLogger("grimace_recorder.app.analysis.configure_recording_dialog")


class ConfigureRecording(Ui_DConfigureRecording, QDialog):
    @Trace.trace(logger)
    def __init__(self, parent, model: GrimaceRecorderModel):
        super().__init__(parent)
        self.setupUi(self)

        self.model = model
        self.temp_config = deepcopy(model.recording_config)

        self.dpd_recording_mode.clear()
        self.dpd_recording_mode.addItems(self.temp_config.MODES)

        if self.temp_config.mode is not None and self.temp_config.mode in self.temp_config.MODES:
            self.dpd_recording_mode.setCurrentText(self.temp_config.mode)
        else:
            self.dpd_recording_mode.setCurrentIndex(-1)
            self.tme_time.setEnabled(False)

        self.dpd_codec.clear()
        self.dpd_codec.addItems(self.temp_config.CODECS)

        if self.temp_config.codec is not None and self.temp_config.codec in self.temp_config.CODECS:
            self.dpd_codec.setCurrentText(self.temp_config.codec)
        else:
            self.dpd_codec.setCurrentIndex(-1)

        recording_duration_ms = int(self.temp_config.duration * 1000)
        self.tme_time.setTime(QTime(0, 0).addMSecs(recording_duration_ms))

        self.dpd_recording_mode.currentTextChanged.connect(self.recording_mode_changed)
        self.tme_time.timeChanged.connect(self.time_changed)
        self.dpd_codec.currentTextChanged.connect(self.codec_changed)

        self.btn_apply = self.btnbox_buttons.button(QDialogButtonBox.StandardButton.Apply)
        self.btn_apply.clicked.connect(self.apply)

        if self.temp_config.FIXED_CODEC:
            self.dpd_codec.setEnabled(False)

        self.recording_mode_changed()

    @Trace.trace(logger)
    def recording_mode_changed(self, *_):
        recording_mode = self.dpd_recording_mode.currentText()
        logger.info("Recording Mode Selected: %s", recording_mode)
        if recording_mode == "" or recording_mode is None:
            recording_mode = None
        if recording_mode == "Timed":
            self.tme_time.setEnabled(True)
            self.tme_time.setReadOnly(False)
        else:
            self.tme_time.setEnabled(False)
            self.tme_time.setReadOnly(True)
        self.temp_config.mode = recording_mode

    @Trace.trace(logger)
    def time_changed(self, *_):
        recording_duration = self.tme_time.time().msecsSinceStartOfDay() / 1000
        logger.info("Recording Duration Selected: %s", recording_duration)
        self.temp_config.duration = recording_duration

    @Trace.trace(logger)
    def codec_changed(self, *_):
        codec = self.dpd_codec.currentText()
        logger.info("Codec Selected: %s", codec)
        if codec == "" or codec is None:
            codec = None
        self.temp_config.codec = codec

    @Trace.trace(logger)
    def apply(self):
        self.model.set_recording_config(self.temp_config)

    @Trace.trace(logger)
    def accept(self):
        if self.temp_config != self.model.recording_config:
            self.apply()
        super().accept()
