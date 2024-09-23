import time

from PySide6.QtCore import QObject, QThread

from app.model.grimace_recorder_model import GrimaceRecorderModel


class RecordingManager(QObject):
    def __init__(self, model: GrimaceRecorderModel):
        super(RecordingManager, self).__init__()

        self.model = model

        self.model.recording_state_signal.connect(self.on_recording_state_changed)
        self.model.top_camera_config_signal.connect(self.on_config_changed)
        self.model.front_camera_config_signal.connect(self.on_config_changed)
        self.model.video_files_config_signal.connect(self.on_config_changed)
        self.model.recording_config_signal.connect(self.on_config_changed)
        self.model.grimace_config_signal.connect(self.on_config_changed)
        self.model.pose_config_signal.connect(self.on_config_changed)

        self.thread = QThread()
        self.moveToThread(self.thread)
        self.thread.start()

    def on_recording_state_changed(self, recording_state: str):
        if recording_state == "starting":
            self.start_recording()
        elif recording_state == "stopping":
            self.stop_recording()

    def start_recording(self):
        time.sleep(2)
        self.model.set_recording_running()

    def stop_recording(self):
        time.sleep(2)
        self.model.set_recording_name(None)
        self.check_ready()

    def is_ready(self) -> str | None:
        return None

    def check_ready(self):
        reason = self.is_ready()
        if reason is None:
            self.model.set_recording_ready()
        else:
            self.model.set_recording_not_ready(reason)

    def on_config_changed(self):
        if self.model.recording_state in ["ready", "not_ready"]:
            self.check_ready()
