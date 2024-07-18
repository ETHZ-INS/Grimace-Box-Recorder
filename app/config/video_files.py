from dataclasses import dataclass, field
from typing import Optional, Dict


@dataclass
class VideoFilesConfig:
    target_directory: Optional[str] = None
    naming_mode: Optional[str] = "Incremental Number"
    top_templates: Dict[str, str] = field(default_factory=dict)
    front_templates: Dict[str, str] = field(default_factory=dict)
    grimace_results_templates: Dict[str, str] = field(default_factory=dict)

    NAMING_MODES = ["Incremental Number", "Start Time", "Custom Template"]
