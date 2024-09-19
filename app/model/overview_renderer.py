from datetime import timedelta

from app.model.grimace_recorder_model import GrimaceRecorderModel


OVERVIEW_TEMPLATE = """
## Overview for {recording_state}:  
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
        self.model.recording_state_signal.connect(self.render)
        self.model.recording_config_signal.connect(self.render)
        self.model.grimace_config_signal.connect(self.render)
        self.model.pose_config_signal.connect(self.render)
        self.model.recording_number_signal.connect(self.render)
        self.model.recording_name_signal.connect(self.render)
        self.render()

    def render(self):
        if self.model.recording_state in ["recording", "stopping"]:
            recording_state = "Current Recording"
        else:
            recording_state = "Next Recording"

        if self.model.recording_config.mode == "Manual":
            recording_duration = "Manual"
        elif self.model.recording_config.mode == "Timed":
            recording_duration = self.model.recording_config.duration
            if recording_duration is not None:
                recording_duration = str(timedelta(seconds=recording_duration))
            else:
                recording_duration = "Not Configured"
        else:
            recording_duration = "error"

        if self.model.recording_name is None:
            recording_name = "<span style='color:gray'><i>Will be asked at the start of the recording</i></span>"
        elif self.model.recording_name == "":
            recording_name = "<span style='color:gray'><i>None</i></span>"
        else:
            recording_name = self.model.recording_name

        frame_interval_seconds = round(self.model.grimace_config.frame_interval)

        minutes = frame_interval_seconds // 60
        seconds = frame_interval_seconds % 60

        minutes_str = f"{minutes} Minutes" if minutes > 1 else ("1 Minute" if minutes == 1 else "")
        seconds_str = f"{seconds} Seconds" if seconds > 1 else ("1 Second" if seconds == 1 else "")

        grimace_scoring_interval_str = minutes_str + (" " if minutes and seconds else "") + seconds_str

        pose_preview = "Enabled" if self.model.pose_config.show_preview else "Disabled"

        overview = OVERVIEW_TEMPLATE.format(
            recording_state=recording_state,
            recording_number=self.model.recording_number,
            recording_name=recording_name,
            recording_duration=recording_duration,
            grimace_model=self.model.grimace_config.grimace_model,
            grimace_scoring_interval=grimace_scoring_interval_str,
            pose_model=self.model.pose_config.pose_model,
            pose_preview=pose_preview
        )

        self.model.set_overview_text(overview)

    def __del__(self):
        self.model.recording_state_signal.disconnect(self.render)
        self.model.recording_config_signal.disconnect(self.render)
        self.model.grimace_config_signal.disconnect(self.render)
        self.model.pose_config_signal.disconnect(self.render)
