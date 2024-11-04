import logging
import time
from pathlib import Path

from PySide6.QtCore import QObject, QThread

from app.config.serialization.json_serializer import JsonConfigSerializer
from app.model.grimace_recorder_model import GrimaceRecorderModel, RecordingState
from app.validation.config.camera_config_validator import CameraConfigValidator
from app.validation.config.grimace_config_validator import GrimaceConfigValidator
from app.validation.config.recording_config_validator import RecordingConfigValidator
from app.validation.config.video_files_validator import VideoFilesConfigValidator
from util.trace import Trace

logger = logging.getLogger("grimace_box."+__name__)


class ConfigLoader(QObject):
    @Trace.trace(logger)
    def __init__(self, model: GrimaceRecorderModel):
        super(ConfigLoader, self).__init__()

        self.model = model

        self.model.loading_signal.connect(self.on_loading)
        self.model.recording.recording_state_signal.connect(self.on_state_changed)

        self.loading = False

        self.thread = QThread()
        self.moveToThread(self.thread)
        self.thread.start()

    @Trace.trace(logger)
    def on_loading(self, loading: bool):
        if loading and self.model.config_file is not None:
            self.loading = True
            self.load(Path(self.model.config_file))

    @Trace.trace(logger)
    def on_state_changed(self, recording_state: RecordingState, *_):
        if self.loading and recording_state in [RecordingState.READY, RecordingState.NOT_READY]:
            self.model.progress_dialog.finish()
            self.loading = False

    @Trace.trace(logger)
    def load(self, path: Path):
        self.model.progress_dialog.start("Loading Configuration", "Loading Configuration File...")

        try:
            config = JsonConfigSerializer.load(path)
        except Exception as e:
            logger.warning("Error loading configuration file: %s", e)
            self.model.progress_dialog.finish()
            self.model.message_box.show("Error Loading Configuration", f"Error loading configuration file:\n{e}")
            return

        self.model.progress_dialog.set_progress("Validating Configuration...", 10)

        top_camera_config = config[0]
        front_camera_config = config[1]
        recording_config = config[2]
        video_files_config = config[3]
        grimace_config = config[4]
        pose_top_config = config[5]

        error = CameraConfigValidator.validate(top_camera_config)
        if error is not None:
            logger.warning("Error loading top camera config: %s %s", error, top_camera_config)
            self.model.progress_dialog.finish()
            self.model.message_box.show("Error Loading Configuration", f"Error loading top camera config:\n{error}")
            return

        error = CameraConfigValidator.validate(front_camera_config)
        if error is not None:
            logger.warning("Error loading front camera config: %s %s", error, front_camera_config)
            self.model.progress_dialog.finish()
            self.model.message_box.show("Error Loading Configuration", f"Error loading front camera config:\n{error}")
            return

        error = RecordingConfigValidator.validate(recording_config)
        if error is not None:
            logger.warning("Error loading recording config: %s %s", error, recording_config)
            self.model.progress_dialog.finish()
            self.model.message_box.show("Error Loading Configuration", f"Error loading recording config:\n{error}")
            return

        error = VideoFilesConfigValidator.validate(video_files_config)
        if error is not None:
            logger.warning("Error loading video files config: %s %s", error, video_files_config)
            self.model.progress_dialog.finish()
            self.model.message_box.show("Error Loading Configuration", f"Error loading video files config:\n{error}")
            return

        error = GrimaceConfigValidator.validate(grimace_config)
        if error is not None:
            logger.warning("Error loading grimace config: %s %s", error, grimace_config)
            self.model.progress_dialog.finish()
            self.model.message_box.show("Error Loading Configuration", f"Error loading grimace config:\n{error}")
            return

        error = None
        if error is not None:
            logger.warning("Error loading pose top config: %s %s", error, pose_top_config)
            self.model.progress_dialog.finish()
            self.model.message_box.show("Error Loading Configuration", f"Error loading pose top config:\n{error}")
            return

        self.model.progress_dialog.set_progress("Applying Configuration...", 40)

        self.model.recording.set_all_configs(top_camera_config, front_camera_config, video_files_config,
                                             recording_config, grimace_config, pose_top_config)

        self.model.set_loading(False)

    @Trace.trace(logger)
    def save(self, path: Path):
        config = (
            self.model.recording.top_camera_config,
            self.model.recording.front_camera_config,
            self.model.recording.recording_config,
            self.model.recording.video_files_config,
            self.model.recording.grimace_config,
            self.model.recording.pose_config
        )

        JsonConfigSerializer.save(path, config)
