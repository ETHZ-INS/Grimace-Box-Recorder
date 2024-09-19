from copy import deepcopy
from typing import Literal

import numpy as np
from PySide6.QtCore import QObject, Signal

from app.config.camera import CameraConfig
from app.config.grimace import GrimaceConfig
from app.config.pose_top import PoseTopConfig
from app.config.recording import RecordingConfig
from app.config.video_files import VideoFilesConfig


class GrimaceRecorderModel(QObject):
    """
    A model class containing all data for the Grimace Recorder UI.
    Signals are used to notify the UI of changes made to the data.
    """
    debug_mode_signal = Signal(bool)

    top_camera_config_signal = Signal(CameraConfig)
    front_camera_config_signal = Signal(CameraConfig)
    video_files_config_signal = Signal(VideoFilesConfig)
    recording_config_signal = Signal(RecordingConfig)
    grimace_config_signal = Signal(GrimaceConfig)
    pose_config_signal = Signal(PoseTopConfig)

    # type is object because it can be string or None
    # If it was str, None values would be converted to empty strings, which is wrong
    recording_state_signal = Signal(str, object, object)
    recording_timer_time_signal = Signal(float)

    recording_number_signal = Signal(int)
    # type is object because it can be string or None
    recording_name_signal = Signal(object)

    top_camera_frame_signal = Signal(np.ndarray)
    front_camera_frame_signal = Signal(np.ndarray)

    # type is object because it can be string or None
    top_camera_error_signal = Signal(object)
    front_camera_error_signal = Signal(object)

    overview_text_signal = Signal(str)
    warnings_text_signal = Signal(str)

    def __init__(self):
        super(GrimaceRecorderModel, self).__init__()

        self.debug_mode = False

        self.top_camera_config = CameraConfig()
        self.front_camera_config = CameraConfig()
        self.video_files_config = VideoFilesConfig()
        self.recording_config = RecordingConfig()
        self.grimace_config = GrimaceConfig()
        self.pose_config = PoseTopConfig()

        self.recording_state: Literal["ready", "not_ready", "starting", "recording", "stopping"] = "not_ready"
        self.recording_state_reason = "Not ready to record."
        self.recording_error = None

        self.recording_number = 1
        self.recording_name = None

        self.auto_stop = False
        self.recording_timer_time = 0.0

        self.top_camera_frame = None
        self.front_camera_frame = None

        self.top_camera_error = None
        self.front_camera_error = None

        self.overview_text = None
        self.warnings_text = None

    def set_debug_mode(self, debug_mode: bool):
        self.debug_mode = debug_mode
        self.debug_mode_signal.emit(debug_mode)

    def set_auto_stop(self, auto_stop: bool):
        self.auto_stop = auto_stop

    def set_top_camera_config(self, top_camera_config: CameraConfig):
        print("set_top_camera_config", top_camera_config)
        self.top_camera_config = deepcopy(top_camera_config)
        self.top_camera_config_signal.emit(top_camera_config)

    def set_front_camera_config(self, front_camera_config: CameraConfig):
        print("set_front_camera_config", front_camera_config)
        self.front_camera_config = deepcopy(front_camera_config)
        self.front_camera_config_signal.emit(front_camera_config)

    def set_video_files_config(self, video_files_config: VideoFilesConfig):
        print("set_video_files_config", video_files_config)
        self.video_files_config = deepcopy(video_files_config)
        self.video_files_config_signal.emit(video_files_config)

    def set_recording_config(self, recording_config: RecordingConfig):
        print("set_recording_config", recording_config)
        self.recording_config = deepcopy(recording_config)
        self.recording_config_signal.emit(recording_config)

    def set_grimace_config(self, grimace_config: GrimaceConfig):
        print("set_grimace_config", grimace_config)
        self.grimace_config = deepcopy(grimace_config)
        self.grimace_config_signal.emit(grimace_config)

    def set_pose_config(self, pose_config: PoseTopConfig):
        print("set_pose_config", pose_config)
        self.pose_config = deepcopy(pose_config)
        self.pose_config_signal.emit(pose_config)

    def set_recording_ready(self):
        self.recording_state = "ready"
        self.recording_state_reason = None
        self.recording_state_signal.emit(self.recording_state, self.recording_state_reason, self.recording_error)

    def set_recording_not_ready(self, reason: str):
        self.recording_state = "not_ready"
        self.recording_state_reason = reason
        self.recording_state_signal.emit(self.recording_state, self.recording_state_reason, self.recording_error)

    def set_recording_starting(self):
        # This transitioning state tells the recording manager that it should start the recording
        self.recording_state = "starting"
        self.recording_state_reason = None
        self.recording_state_signal.emit(self.recording_state, self.recording_state_reason, self.recording_error)

    def set_recording_running(self):
        self.recording_state = "recording"
        self.recording_state_reason = None
        self.recording_state_signal.emit(self.recording_state, self.recording_state_reason, self.recording_error)

    def set_recording_stopping(self):
        # This transitioning state tells the recording manager that it should stop the recording
        self.recording_state = "stopping"
        self.recording_state_reason = None
        self.recording_state_signal.emit(self.recording_state, self.recording_state_reason, self.recording_error)

    def set_recording_number(self, recording_number: int):
        self.recording_number = recording_number
        self.recording_number_signal.emit(recording_number)

    def set_recording_name(self, recording_name: str | None):
        self.recording_name = recording_name
        self.recording_name_signal.emit(recording_name)

    def set_recording_error(self, error: str):
        self.recording_error = error
        self.recording_state_signal.emit(self.recording_state, self.recording_state_reason, self.recording_error)

    def set_recording_timer_time(self, recording_time: float):
        self.recording_timer_time = recording_time
        self.recording_timer_time_signal.emit(recording_time)

    def set_top_camera_frame(self, top_camera_frame):
        self.top_camera_frame = top_camera_frame
        self.top_camera_frame_signal.emit(top_camera_frame)

    def set_front_camera_frame(self, front_camera_frame):
        self.front_camera_frame = front_camera_frame
        self.front_camera_frame_signal.emit(front_camera_frame)

    def set_top_camera_error(self, top_camera_error: str):
        self.top_camera_error = top_camera_error
        self.top_camera_error_signal.emit(top_camera_error)

    def set_front_camera_error(self, front_camera_error: str):
        self.front_camera_error = front_camera_error
        self.front_camera_error_signal.emit(front_camera_error)

    def set_overview_text(self, overview_text: str):
        self.overview_text = overview_text
        self.overview_text_signal.emit(overview_text)

    def set_warnings_text(self, warnings_text: str):
        self.warnings_text = warnings_text
        self.warnings_text_signal.emit(warnings_text)
