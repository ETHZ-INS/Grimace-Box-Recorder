from typing import Optional

from app.config.grimace import GrimaceConfig


class GrimaceConfigValidator:
    @classmethod
    def _validate(cls, grimace_config: GrimaceConfig) -> Optional[str]:
        if grimace_config.enabled is None:
            return "Grimace enabled is null"

        if grimace_config.grimace_model is None:
            return "Grimace model is null"

        if grimace_config.grimace_model not in grimace_config.GRIMACE_MODELS:
            return "Grimace model is invalid, must be one of: " + ", ".join(grimace_config.GRIMACE_MODELS)

        if grimace_config.frame_interval is None:
            return "Frame interval is null"

        if grimace_config.frame_interval <= 0:
            return "Frame interval is invalid"

        if grimace_config.frame_interval > 300:
            return "Frame interval is too high"

        if grimace_config.frame_quality_device is None:
            return "Frame quality device is null"

        if grimace_config.face_cropper_device is None:
            return "Face cropper device is null"

        if grimace_config.grimace_scoring_device is None:
            return "Grimace scoring device is null"

    @classmethod
    def validate(cls, grimace_config: GrimaceConfig) -> Optional[str]:
        try:
            return cls._validate(grimace_config)
        except Exception as e:
            return str(e)
