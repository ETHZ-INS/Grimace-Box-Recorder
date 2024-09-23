from dataclasses import dataclass, field
from typing import Optional, Dict


@dataclass
class VideoFilesConfig:
    target_directory: Optional[str] = None
