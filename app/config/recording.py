from dataclasses import dataclass
from typing import Optional


@dataclass
class RecordingConfig:
    mode: Optional[str] = "Manual"
    duration: float = 600.0
    codec: str = "FMP4"

    MODES = ["Manual", "Timed"]
    CODECS = ["FMP4", "FFV1", "H264"]
    FIXED_CODEC = True
