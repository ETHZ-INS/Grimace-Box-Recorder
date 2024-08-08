from typing import Optional

from app.config.camera import CameraConfig


class CameraConfigValidator:
    @classmethod
    def _validate(cls, camera_config: CameraConfig) -> Optional[str]:
        if camera_config is None:
            return "Config is null"

        if camera_config.fps is None:
            return "FPS is null"

        if camera_config.fps <= 0:
            return "FPS is invalid"

        # Our camera can't handle FPS lower than 1
        if camera_config.fps <= 1:
            return "FPS is too low"

    @classmethod
    def validate(cls, camera_config: CameraConfig) -> Optional[str]:
        try:
            return cls._validate(camera_config)
        except Exception as e:
            return str(e)
