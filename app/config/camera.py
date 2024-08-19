from dataclasses import dataclass
from typing import Optional


@dataclass
class CameraConfig:
    camera_type: str = "Pylon"
    camera_id: Optional[str] = None
    config_file: Optional[str] = None
    fps: float = 30.0
    video_file: Optional[str] = None
