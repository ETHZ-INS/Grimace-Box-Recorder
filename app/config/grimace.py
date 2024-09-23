from dataclasses import dataclass
from typing import Optional


@dataclass
class GrimaceConfig:
    grimace_model: Optional[str] = "V1 - HohlBot"
    frame_interval: float = 10.0
    frame_quality_device: str = "cuda:0"
    face_cropper_device: str = "cuda:0"
    grimace_scoring_device: str = "cuda:0"

    GRIMACE_MODELS = ["V1 - HohlBot", "Demo (Fake Mouse)"]
    FRAME_INTERVAL_OPTIONS = [
        ("5 Seconds", 5.0),
        ("10 Seconds", 10.0),
        ("20 Seconds", 20.0),
        ("30 Seconds", 30.0),
        ("1 Minute", 60.0),
    ]
    FIXED_DEVICE = True
