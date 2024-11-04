import os
from pathlib import Path
from typing import Tuple

import yaml

config_folder = Path(os.getenv('LOCALAPPDATA')) / "Grimace Recorder" / "config"

camera_ids_file = config_folder / "camera_ids.yaml"

def load_camera_ids() -> Tuple[str | None, str | None]:
    if not camera_ids_file.exists():
        return None, None

    with open(camera_ids_file, 'r') as f:
        data = yaml.safe_load(f)

        return data.get("top"), data.get("front")