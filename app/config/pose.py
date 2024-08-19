from dataclasses import dataclass
from typing import Optional


@dataclass
class PoseConfig:
    enabled: bool = False
    pose_model: Optional[str] = "V1 - SuperScorer"
    pose_device: str = "cpu"

    GRIMACE_MODELS = ["V1 - SuperScorer", "Demo (Fake Mouse)"]
