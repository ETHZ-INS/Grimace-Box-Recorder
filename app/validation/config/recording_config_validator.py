from typing import Optional

from app.config.recording import RecordingConfig


class RecordingConfigValidator:
    @classmethod
    def _validate(cls, recording_config: RecordingConfig) -> Optional[str]:
        if recording_config.mode is None:
            return "Timing mode is null"

        if recording_config.mode is None:
            return "Naming mode is null"

        if recording_config.mode not in recording_config.MODES:
            return "Naming mode is invalid, must be one of: " + ", ".join(recording_config.MODES)

        if recording_config.duration is None:
            return "Recording duration is null"

        if recording_config.duration <= 0:
            return "Recording duration is invalid"

        if recording_config.codec is None:
            return "Codec is null"

        if recording_config.codec not in recording_config.CODECS:
            return "Codec is invalid, must be one of: " + ", ".join(recording_config.CODECS)

    @classmethod
    def validate(cls, recording_config: RecordingConfig) -> Optional[str]:
        try:
            return cls._validate(recording_config)
        except Exception as e:
            return str(e)
