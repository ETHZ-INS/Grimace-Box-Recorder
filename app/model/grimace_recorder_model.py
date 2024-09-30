from copy import deepcopy
from enum import Enum

import numpy as np
from PySide6.QtCore import QObject, Signal

from app.config.camera import CameraConfig
from app.config.grimace import GrimaceConfig
from app.config.pose_top import PoseTopConfig
from app.config.recording import RecordingConfig
from app.config.video_files import VideoFilesConfig
from app.dataflow.qlist import QList


class RecordingState(Enum):
    IDLE = "idle"  # The recording is not running, unknown if it is ready to record -> Try to determine if it is ready
    CHANGING_CONFIG = "changing_config"  # The recording manager is in the process of changing the configuration
    STARTING_PREVIEW = "starting_preview"  # The recording manager is in the process of starting the preview
    READY = "ready"  # The recording manager is ready to record
    NOT_READY = "not_ready"  # The recording manager is not ready to record -> Show the reason
    STARTING = "starting"  # The recording manager is in the process of starting the recording
    RECORDING = "recording"  # The recording is running
    STOPPING = "stopping"  # The recording manager is in the process of stopping the recording


class ApplicationState(Enum):
    RUNNING = "running"
    CLOSING = "closing"


class MessageBoxState(Enum):
    VISIBLE = "visible"
    HIDDEN = "hidden"


class ProgressDialogState(Enum):
    RUNNING = "running"
    FINISHED = "finished"


class MessageBoxModel(QObject):
    change_signal = Signal(MessageBoxState, object, object)

    def __init__(self):
        super(MessageBoxModel, self).__init__()

        self.state = MessageBoxState.HIDDEN
        self.title: str = ""
        self.text: str = ""

    def show(self, title: str, text: str):
        self.state = MessageBoxState.VISIBLE
        self.title = title
        self.text = text
        self.change_signal.emit(MessageBoxState.VISIBLE, title, text)

    def hide(self):
        self.state = MessageBoxState.HIDDEN
        self.title = ""
        self.text = ""
        self.change_signal.emit(MessageBoxState.HIDDEN, "", "")


class ProgressDialogModel(QObject):
    change_signal = Signal(ProgressDialogState, object, object, int)
    progress_signal = Signal(object, int)

    def __init__(self):
        super(ProgressDialogModel, self).__init__()

        self.state = ProgressDialogState.FINISHED
        self.title: str = ""
        self.text: str = ""
        self.progress: int = 0

    def start(self, title: str, text: str, progress: int = 0):
        self.state = ProgressDialogState.RUNNING
        self.title = title
        self.text = text
        self.progress = progress
        self.change_signal.emit(ProgressDialogState.RUNNING, title, text, progress)

    def finish(self):
        self.state = ProgressDialogState.FINISHED
        self.title = ""
        self.text = ""
        self.progress = 0
        self.change_signal.emit(ProgressDialogState.FINISHED, "", "", 0)

    def set_progress(self, text: str, progress: int):
        self.text = text
        self.progress = progress
        self.progress_signal.emit(text, progress)


class RecordingModel(QObject):
    # type is object because it can be string or None
    # If it was str, None values would be converted to empty strings, which is wrong
    recording_state_signal = Signal(RecordingState, object, object)
    recording_timer_time_signal = Signal(float)

    top_camera_config_signal = Signal(CameraConfig)
    front_camera_config_signal = Signal(CameraConfig)
    video_files_config_signal = Signal(VideoFilesConfig)
    recording_config_signal = Signal(RecordingConfig)
    grimace_config_signal = Signal(GrimaceConfig)
    pose_config_signal = Signal(PoseTopConfig)
    all_configs_signal = Signal(CameraConfig, CameraConfig, VideoFilesConfig, RecordingConfig, GrimaceConfig, PoseTopConfig)

    config_applied_signal = Signal()

    recording_number_signal = Signal(int)
    # type is object because it can be string or None
    recording_name_signal = Signal(object)

    # type is object because it can be string or None
    top_camera_error_signal = Signal(object)
    front_camera_error_signal = Signal(object)
    recording_error_signal = Signal(object)

    def __init__(self):
        super(RecordingModel, self).__init__()

        self.top_camera_config = CameraConfig()
        self.front_camera_config = CameraConfig()
        self.video_files_config = VideoFilesConfig()
        self.recording_config = RecordingConfig()
        self.grimace_config = GrimaceConfig()
        self.pose_config = PoseTopConfig()

        self.grimace_results = QList()

        self.recording_number = 1
        self.recording_name = None

        self.recording_state: RecordingState = RecordingState.IDLE
        self.recording_state_reason = "Not ready to record."
        self.recording_timer_time = 0.0

        self.top_camera_error = None
        self.front_camera_error = None
        self.recording_error = None

        self.grimace_analyzer_initialized = False
        self.pose_estimator_initialized = False

    def set_top_camera_config(self, top_camera_config: CameraConfig):
        print("set_top_camera_config", top_camera_config)
        self.top_camera_config = deepcopy(top_camera_config)
        self.top_camera_config_signal.emit(top_camera_config)
        self.set_top_camera_error(None)

    def set_front_camera_config(self, front_camera_config: CameraConfig):
        print("set_front_camera_config", front_camera_config)
        self.front_camera_config = deepcopy(front_camera_config)
        self.front_camera_config_signal.emit(front_camera_config)
        self.set_front_camera_error(None)

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

    def set_all_configs(self, top_camera_config: CameraConfig, front_camera_config: CameraConfig,
                        video_files_config: VideoFilesConfig, recording_config: RecordingConfig,
                        grimace_config: GrimaceConfig, pose_config: PoseTopConfig):
        self.top_camera_config = deepcopy(top_camera_config)
        self.front_camera_config = deepcopy(front_camera_config)
        self.video_files_config = deepcopy(video_files_config)
        self.recording_config = deepcopy(recording_config)
        self.grimace_config = deepcopy(grimace_config)
        self.pose_config = deepcopy(pose_config)
        self.all_configs_signal.emit(top_camera_config, front_camera_config, video_files_config,
                                     recording_config, grimace_config, pose_config)

    def apply_all_configs(self):
        # This is just used at the start of the application to apply the default configuration
        self.all_configs_signal.emit(self.top_camera_config, self.front_camera_config, self.video_files_config,
                                        self.recording_config, self.grimace_config, self.pose_config)

    def set_recording_number(self, recording_number: int):
        self.recording_number = recording_number
        self.recording_number_signal.emit(recording_number)

    def set_recording_name(self, recording_name: str | None):
        self.recording_name = recording_name
        self.recording_name_signal.emit(recording_name)

    def set_recording_idle(self):
        print("IDLE: ", self.recording_state_reason)
        self.recording_state = RecordingState.IDLE
        self.recording_state_reason = None
        self.recording_state_signal.emit(self.recording_state, self.recording_state_reason, self.recording_error)

    def set_recording_ready(self):
        print("READY: ", self.recording_state_reason)
        self.recording_state = RecordingState.READY
        self.recording_state_reason = None
        self.recording_state_signal.emit(self.recording_state, self.recording_state_reason, self.recording_error)

    def set_recording_not_ready(self, reason: str):
        print("NOT READY: ", reason)
        self.recording_state = RecordingState.NOT_READY
        self.recording_state_reason = reason
        self.recording_state_signal.emit(self.recording_state, self.recording_state_reason, self.recording_error)

    def set_recording_changing_config(self, reason: str):
        print("CHANGING CONFIG: ", reason)
        self.recording_state = RecordingState.CHANGING_CONFIG
        self.recording_state_reason = reason
        self.recording_state_signal.emit(self.recording_state, self.recording_state_reason, self.recording_error)

    def set_recording_starting(self):
        print("STARTING: ", self.recording_state_reason)
        # This transitioning state tells the recording manager that it should start the recording
        self.recording_state = RecordingState.STARTING
        self.recording_state_reason = None
        self.recording_error = None
        self.recording_state_signal.emit(self.recording_state, self.recording_state_reason, self.recording_error)

    def set_recording_running(self):
        print("RECORDING: ", self.recording_state_reason)
        self.recording_state = RecordingState.RECORDING
        self.recording_state_reason = None
        self.recording_state_signal.emit(self.recording_state, self.recording_state_reason, self.recording_error)

    def set_recording_stopping(self):
        print("STOPPING: ", self.recording_state_reason)
        # This transitioning state tells the recording manager that it should stop the recording
        self.recording_state = RecordingState.STOPPING
        self.recording_state_reason = None
        self.recording_state_signal.emit(self.recording_state, self.recording_state_reason, self.recording_error)

    def set_top_camera_error(self, top_camera_error: str | None):
        self.top_camera_error = top_camera_error
        self.top_camera_error_signal.emit(top_camera_error)

    def set_front_camera_error(self, front_camera_error: str | None):
        self.front_camera_error = front_camera_error
        self.front_camera_error_signal.emit(front_camera_error)

    def set_recording_error(self, error: str | None):
        self.recording_error = error
        # TODO: What will happen if an error occurs during state STARTING or STOPPING? Will the recording manager
        #  try to start or stop the recording again?
        self.recording_state_signal.emit(self.recording_state, self.recording_state_reason, self.recording_error)

    def set_recording_timer_time(self, recording_time: float):
        self.recording_timer_time = recording_time
        self.recording_timer_time_signal.emit(recording_time)


class GrimaceRecorderModel(QObject):
    """
    A model class containing all data for the Grimace Recorder UI.
    Signals are used to notify the UI of changes made to the data.
    """
    debug_mode_signal = Signal(bool)
    ask_for_identifier_signal = Signal(bool)

    application_state_signal = Signal(ApplicationState)

    loading_signal = Signal(bool)
    start_preview_signal = Signal()

    top_camera_frame_signal = Signal(np.ndarray)
    front_camera_frame_signal = Signal(np.ndarray)

    overview_text_signal = Signal(str)
    warnings_text_signal = Signal(str)

    def __init__(self):
        super(GrimaceRecorderModel, self).__init__()

        self.recording = RecordingModel()

        self.debug_mode = False

        self.config_file = None

        self.application_state = ApplicationState.RUNNING

        self.loading = False

        self.ask_for_identifier = True

        self.top_camera_frame = None
        self.front_camera_frame = None

        self.overview_text = None
        self.warnings_text = None

        self.message_box = MessageBoxModel()
        self.progress_dialog = ProgressDialogModel()

    def set_debug_mode(self, debug_mode: bool):
        self.debug_mode = debug_mode
        self.debug_mode_signal.emit(debug_mode)

    def set_config_file(self, config_file: str):
        self.config_file = config_file

    def set_ask_for_identifier(self, ask_for_identifier: bool):
        self.ask_for_identifier = ask_for_identifier
        self.ask_for_identifier_signal.emit(ask_for_identifier)

    def set_loading(self, loading: bool):
        self.loading = loading
        self.loading_signal.emit(loading)

    def set_application_closing(self):
        self.application_state = ApplicationState.CLOSING
        self.application_state_signal.emit(self.application_state)

    def set_top_camera_frame(self, top_camera_frame):
        self.top_camera_frame = top_camera_frame
        self.top_camera_frame_signal.emit(top_camera_frame)

    def set_front_camera_frame(self, front_camera_frame):
        self.front_camera_frame = front_camera_frame
        self.front_camera_frame_signal.emit(front_camera_frame)

    def set_overview_text(self, overview_text: str):
        self.overview_text = overview_text
        self.overview_text_signal.emit(overview_text)

    def set_warnings_text(self, warnings_text: str):
        self.warnings_text = warnings_text
        self.warnings_text_signal.emit(warnings_text)
