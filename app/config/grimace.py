from dataclasses import dataclass
from typing import Optional


@dataclass
class GrimaceConfig:
    enabled: bool = False
    grimace_model: Optional[str] = "V1 SuperScorer"
    frame_interval: float = 60.0
    frame_quality_device: str = "cpu"
    face_cropper_device: str = "cpu"
    grimace_scoring_device: str = "cpu"
