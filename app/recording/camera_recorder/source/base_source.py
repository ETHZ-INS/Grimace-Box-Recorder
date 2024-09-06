from abc import ABC, abstractmethod

import numpy as np


class CameraSource(ABC):
    @abstractmethod
    def get_width(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_height(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_fps(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def grab_frame(self) -> (bool, int, float, np.ndarray):
        raise NotImplementedError

    @abstractmethod
    def start(self):
        raise NotImplementedError

    @abstractmethod
    def stop(self):
        raise NotImplementedError

    def close(self):
        pass
