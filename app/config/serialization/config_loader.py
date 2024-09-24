import logging
import time
from pathlib import Path

from PySide6.QtCore import QObject, QThread

from app.config.serialization.json_serializer import JsonConfigSerializer
from app.model.grimace_recorder_model import GrimaceRecorderModel
from app.validation.config.camera_config_validator import CameraConfigValidator
from app.validation.config.grimace_config_validator import GrimaceConfigValidator
from app.validation.config.recording_config_validator import RecordingConfigValidator
from app.validation.config.video_files_validator import VideoFilesConfigValidator

logger = logging.getLogger("grimace_recorder.config.serialization.config_loader")


class ConfigLoader(QObject):
    def __init__(self, model: GrimaceRecorderModel):
        super(ConfigLoader, self).__init__()

        self.model = model

        self.model.recording_state_signal.connect(self.on_recording_state_changed)

        self.thread = QThread()
        self.moveToThread(self.thread)
        self.thread.start()

    def on_recording_state_changed(self, recording_state: str):
        if recording_state == "loading" and self.model.config_file is not None:
            self.load(Path(self.model.config_file))

    def load(self, path: Path):
        self.model.set_progress_dialog("Loading Configuration", "Loading Configuration File...")

        try:
            config = JsonConfigSerializer.load(path)
        except Exception as e:
            logger.warning("Error loading configuration file: %s", e)
            self.model.finish_progress_dialog()
            self.model.set_message_box("Error Loading Configuration", f"Error loading configuration file:\n{e}")
            return

        self.model.set_progress_dialog_progress("Validating Configuration...", 10)

        top_camera_config = config[0]
        front_camera_config = config[1]
        recording_config = config[2]
        video_files_config = config[3]
        grimace_config = config[4]
        pose_top_config = config[5]

        error = CameraConfigValidator.validate(top_camera_config)
        if error is not None:
            logger.warning("Error loading top camera config: %s %s", error, top_camera_config)
            self.model.finish_progress_dialog()
            self.model.set_message_box("Error Loading Configuration", f"Error loading top camera config:\n{error}")
            return

        error = CameraConfigValidator.validate(front_camera_config)
        if error is not None:
            logger.warning("Error loading front camera config: %s %s", error, front_camera_config)
            self.model.finish_progress_dialog()
            self.model.set_message_box("Error Loading Configuration", f"Error loading front camera config:\n{error}")
            return

        error = RecordingConfigValidator.validate(recording_config)
        if error is not None:
            logger.warning("Error loading recording config: %s %s", error, recording_config)
            self.model.finish_progress_dialog()
            self.model.set_message_box("Error Loading Configuration", f"Error loading recording config:\n{error}")
            return

        error = VideoFilesConfigValidator.validate(video_files_config)
        if error is not None:
            logger.warning("Error loading video files config: %s %s", error, video_files_config)
            self.model.finish_progress_dialog()
            self.model.set_message_box("Error Loading Configuration", f"Error loading video files config:\n{error}")
            return

        error = GrimaceConfigValidator.validate(grimace_config)
        if error is not None:
            logger.warning("Error loading grimace config: %s %s", error, grimace_config)
            self.model.finish_progress_dialog()
            self.model.set_message_box("Error Loading Configuration", f"Error loading grimace config:\n{error}")
            return

        error = None
        if error is not None:
            logger.warning("Error loading pose top config: %s %s", error, pose_top_config)
            self.model.finish_progress_dialog()
            self.model.set_message_box("Error Loading Configuration", f"Error loading pose top config:\n{error}")
            return

        self.model.set_progress_dialog_progress("Applying Configuration...", 20)

        self.model.set_top_camera_config(top_camera_config)
        self.model.set_front_camera_config(front_camera_config)
        time.sleep(2)
        self.model.set_progress_dialog_progress("Applying Configuration...", 40)
        self.model.set_recording_config(recording_config)
        time.sleep(1)
        self.model.set_progress_dialog_progress("Applying Configuration...", 50)
        self.model.set_video_files_config(video_files_config)
        time.sleep(1)
        self.model.set_progress_dialog_progress("Applying Configuration...", 60)
        self.model.set_grimace_config(grimace_config)
        time.sleep(2)
        self.model.set_progress_dialog_progress("Applying Configuration...", 80)
        self.model.set_pose_config(pose_top_config)
        time.sleep(2)
        self.model.finish_progress_dialog()
