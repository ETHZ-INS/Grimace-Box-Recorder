from dataclasses import dataclass
from typing import Optional


@dataclass
class PoseTopConfig:
    show_preview: bool = False
    pose_model: Optional[str] = "V1 - GrimaceBoxTop"
    pose_device: str = "cuda:0"

    POSE_TOP_MODELS = ["V1 - GrimaceBoxTop", "Demo (Fake Mouse)"]
