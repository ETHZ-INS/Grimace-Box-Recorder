import threading

import numpy as np
from PySide6.QtCore import QObject, Signal

from app.dataflow.qqueue import IQueue


class QVariableMeta(type(QObject), type(IQueue)):
    pass


class QVariable(QObject, IQueue, metaclass=QVariableMeta):
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

    def enqueue(self, value):
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

    def close(self):
        # TODO: Is it a good idea that the preview buffer just does nothing on close?
        #   If it would close, it would have to be recreated when the recording is stopped
        #   Right now it works because it's reopened in every case, but how should the UI respond if the
        #   flow of frames actually stopped?
        pass
