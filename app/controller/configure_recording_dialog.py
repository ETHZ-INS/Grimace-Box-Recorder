from dataclasses import replace

from PySide6.QtCore import Signal, QTime
from PySide6.QtWidgets import QDialog, QDialogButtonBox

from app.config.camera import CameraConfig
from app.config.recording import RecordingConfig
from app.layout.configure_recording_dialog import Ui_DConfigureRecording

import logging

logger = logging.getLogger("grimace_recorder.app.analysis.configure_recording_dialog")


class ConfigureRecording(Ui_DConfigureRecording, QDialog):
    applied_signal = Signal(CameraConfig)

    def __init__(self, parent, recording_config: RecordingConfig):
        logger.debug("FUN ConfigureRecording.__init__")
        super().__init__(parent)
        self.setupUi(self)

        self.recording_config = replace(recording_config)
        self.last_recording_config = replace(recording_config)

        self.dpd_recording_mode.clear()
        self.dpd_recording_mode.addItems(recording_config.MODES)

        if recording_config.mode is not None:
            self.dpd_recording_mode.setCurrentText(recording_config.mode)
        else:
            self.dpd_recording_mode.setCurrentIndex(-1)
            self.tme_time.setEnabled(False)

        self.dpd_codec.clear()
        self.dpd_codec.addItems(recording_config.CODECS)

        if recording_config.codec is not None:
            self.dpd_codec.setCurrentText(recording_config.codec)
        else:
            self.dpd_codec.setCurrentIndex(-1)

        self.tme_time.setTime(QTime(0, 0).addMSecs(int(recording_config.duration * 1000)))

        self.dpd_recording_mode.currentTextChanged.connect(self.recording_mode_changed)
        self.tme_time.timeChanged.connect(self.time_changed)
        self.dpd_codec.currentTextChanged.connect(self.codec_changed)

        self.btn_apply = self.btnbox_buttons.button(QDialogButtonBox.StandardButton.Apply)
        self.btn_apply.clicked.connect(self.apply)

        self.recording_mode_changed()
        logger.debug("FUNEND ConfigureRecording.__init__")

    def recording_mode_changed(self):
        logger.debug("FU ConfigureRecording.recording_mode_changed")
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
        self.recording_config.mode = recording_mode

    def time_changed(self):
        logger.debug("FU ConfigureRecording.time_changed")
        recording_duration = self.tme_time.time().msecsSinceStartOfDay() / 1000
        logger.info("Recording Duration Selected: %s", recording_duration)
        self.recording_config.duration = recording_duration

    def codec_changed(self):
        logger.debug("FU ConfigureRecording.codec_changed")
        codec = self.dpd_codec.currentText()
        logger.info("Codec Selected: %s", codec)
        if codec == "" or codec is None:
            codec = None
        self.recording_config.codec = codec

    def apply(self):
        logger.debug("FUN ConfigureRecording.apply")
        self.last_recording_config = replace(self.recording_config)
        self.applied_signal.emit(self.recording_config)
        logger.debug("FUNEND ConfigureRecording.apply")

    def accept(self):
        logger.debug("FUN ConfigureRecording.accept")
        if self.recording_config != self.last_recording_config:
            self.apply()
        super().accept()
        logger.debug("FUNEND ConfigureRecording.accept")
