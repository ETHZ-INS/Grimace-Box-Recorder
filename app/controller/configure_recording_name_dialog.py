from PySide6.QtCore import QTime
from PySide6.QtWidgets import QDialog, QDialogButtonBox

import logging

from app.layout.recording_name_dialog import Ui_DRecordingName
from app.model.grimace_recorder_model import GrimaceRecorderModel
from util.trace import Trace

logger = logging.getLogger("grimace_box."+__name__)


PREVIEW_FILES = [
    "top_{recording_number}.avi",
    "front_{recording_number}.avi",
    "grimace_results_{recording_number}.csv",
    "pose_estimation_results_{recording_number}.csv"
]


class ConfigureRecordingName(Ui_DRecordingName, QDialog):
    @Trace.trace(logger)
    def __init__(self, parent, model: GrimaceRecorderModel):
        super().__init__(parent)
        self.setupUi(self)

        self.model = model

        self.txt_recording_name.textChanged.connect(self.recording_name_changed)

        self.btnbox_buttons.accepted.connect(self.accept)
        self.btnbox_buttons.rejected.connect(self.reject)

        self.recording_name_changed()
        self.setMaximumSize(1000, 1000)
        self.adjustSize()
        self.setFixedSize(self.size())

    @Trace.trace(logger)
    def recording_name_changed(self, *_):
        recording_name = self.txt_recording_name.text()
        recording_name = None if recording_name == "" else recording_name
        recording_number = self.model.recording.recording_number

        prefix = "" if recording_name is None or recording_name == "" else recording_name + "_"
        preview_files = [prefix+file.format(recording_number=recording_number) for file in PREVIEW_FILES]
        preview = "\n".join(preview_files)
        self.lbl_preview.setText(preview)

    @Trace.trace(logger)
    def accept(self):
        recording_name = self.txt_recording_name.text()
        recording_name = None if recording_name == "" else recording_name
        self.model.recording.set_recording_name(recording_name)
        super().accept()
