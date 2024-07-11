import threading

import numpy as np
from PySide6.QtCore import QObject, Signal


class QVariable(QObject):
    """
    A thread-safe variable
    Sends a signal when the value is set, but only if it has been read since the last set
    so the receiver only reacts to the newest value and reacts only once
    """
    value_set = Signal()

    def __init__(self):
        super(QVariable, self).__init__()

        self.value = None
        self.read_since_set = True

        self.lock = threading.Lock()

    def set(self, value: np.ndarray):
        with self.lock:
            self.value = value
            if self.read_since_set:
                self.read_since_set = False
                self.value_set.emit()

    def get(self) -> np.ndarray:
        with self.lock:
            self.read_since_set = True
            return self.value

    def ready(self) -> bool:
        return self.value is not None
