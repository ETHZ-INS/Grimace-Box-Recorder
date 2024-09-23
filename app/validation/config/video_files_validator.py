from typing import Optional

from app.config.video_files import VideoFilesConfig


class VideoFilesConfigValidator:
    @classmethod
    def validate(cls, video_files: VideoFilesConfig) -> Optional[str]:
        if video_files is None:
            return "Config is null"
