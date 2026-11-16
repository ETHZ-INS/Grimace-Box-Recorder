import dataclasses
from dataclasses import dataclass
from typing import List

import numpy as np


@dataclass(slots=True)
class Point:
    conf: float
    x: float
    y: float


@dataclass(slots=True)
class PoseInstance:
    conf: float
    box: np.ndarray
    pose: List[Point] = dataclasses.field(default_factory=list)


class NoPoseModel:
    def get_instance(self, frame: np.ndarray) -> PoseInstance | None:
        return None

    def get_instances(self, frames: List[np.ndarray]) -> List[PoseInstance | None]:
        return [None] * len(frames)
