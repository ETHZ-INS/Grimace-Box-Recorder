import logging
from datetime import timedelta

from app.model.grimace_recorder_model import GrimaceRecorderModel, RecordingState
from util.trace import Trace

logger = logging.getLogger("grimace_box."+__name__)

OVERVIEW_TEMPLATE = """
## Overview for {recording_state}:  
Target Directory:\t{target_directory}  
Recording Number:\t{recording_number}  
Recording Identifier:\t{recording_name}  
Recording Duration:\t{recording_duration}  
Grimace Model:\t{grimace_model}  
Grimace Scoring Interval:\t{grimace_scoring_interval}  
Pose Model:\t\t{pose_model}  
Pose Preview:\t\t{pose_preview}
"""


class OverviewRenderer:
    """
    Renders an overview in markdown format for the current recording configuration.
    """
    def __init__(self, model: GrimaceRecorderModel):
        self.model = model
        self.model.recording.recording_state_signal.connect(self.render)
        self.model.recording.recording_config_signal.connect(self.render)
        self.model.recording.video_files_config_signal.connect(self.render)
        self.model.recording.grimace_config_signal.connect(self.render)
        self.model.recording.pose_config_signal.connect(self.render)
        self.model.recording.recording_number_signal.connect(self.render)
        self.model.recording.recording_name_signal.connect(self.render)
        self.model.ask_for_identifier_signal.connect(self.render)
        self.render()

    @Trace.trace(logger)
    def render(self, *_):
        if self.model.recording.recording_state in [RecordingState.RECORDING, RecordingState.STOPPING]:
            recording_state = "Current Recording"
        else:
            recording_state = "Next Recording"

        if self.model.recording.video_files_config.target_directory is None:
            target_directory = "<span style='color:red'><i>Not Set</i></span>"
        else:
            target_directory = self.model.recording.video_files_config.target_directory

        if self.model.recording.recording_config.mode == "Manual":
            recording_duration = "Manual"
        elif self.model.recording.recording_config.mode == "Timed":
            recording_duration = self.model.recording.recording_config.duration
            if recording_duration is not None:
                recording_duration = str(timedelta(seconds=recording_duration))
            else:
                recording_duration = "Not Configured"
        else:
            recording_duration = "error"

        if self.model.recording.recording_name is None:
            if self.model.ask_for_identifier and self.model.recording.recording_state in [RecordingState.READY, RecordingState.NOT_READY]:
                recording_name = "<span style='color:gray'><i>Will be asked at the start of the recording</i></span>"
            else:
                recording_name = "<span style='color:gray'><i>None</i></span>"
        else:
            recording_name = self.model.recording.recording_name

        frame_interval_seconds = round(self.model.recording.grimace_config.frame_interval)

        minutes = frame_interval_seconds // 60
        seconds = frame_interval_seconds % 60

        minutes_str = f"{minutes} Minutes" if minutes > 1 else ("1 Minute" if minutes == 1 else "")
        seconds_str = f"{seconds} Seconds" if seconds > 1 else ("1 Second" if seconds == 1 else "")

        grimace_scoring_interval_str = minutes_str + (" " if minutes and seconds else "") + seconds_str

        pose_preview = "Enabled" if self.model.recording.pose_config.show_preview else "Disabled"

        overview = OVERVIEW_TEMPLATE.format(
            target_directory=target_directory,
            recording_state=recording_state,
            recording_number=self.model.recording.recording_number,
            recording_name=recording_name,
            recording_duration=recording_duration,
            grimace_model=self.model.recording.grimace_config.grimace_model,
            grimace_scoring_interval=grimace_scoring_interval_str,
            pose_model=self.model.recording.pose_config.pose_model,
            pose_preview=pose_preview
        )

        self.model.set_overview_text(overview)
