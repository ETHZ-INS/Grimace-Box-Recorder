from PySide6.QtCore import QObject, Signal

from app.dataflow.qqueue import IQueue


class RecordingTimerMeta(type(QObject), type(IQueue)):
    pass


class RecordingTimer(QObject, IQueue, metaclass=RecordingTimerMeta):
    """
    Keeps track of the recording time by inspecting the timestamps of the items that are passed through the queue.
    """
    stop_signal = Signal()
    time_signal = Signal(float)

    def __init__(self, output_queue: IQueue, duration: float = None):
        super().__init__()

        self.output_queue = output_queue

        self.duration = duration

        self.started = False
        self.finished = False

        self.start_time = None
        self.latest_time = None
        self.stop_time = None

    def _should_stop(self):
        if not self.started or self.start_time is None:
            return False

        if self.duration is None:
            return False

        if self.latest_time is None:
            return False

        if self.latest_time - self.start_time < self.duration:
            return False

        return True

    def start(self):
        self.started = True
        self.finished = False
        self.start_time = None
        self.latest_time = None
        self.stop_time = None

    def stop(self):
        self.finished = True
        self.stop_time = self.latest_time
        self.stop_signal.emit()

    def enqueue(self, item):
        timestamp = item[2]
        self.latest_time = timestamp
        self.time_signal.emit(timestamp)

        if self.started and self.start_time is None:
            self.start_time = timestamp

        # TODO: Should we still enqueue items after the recording has finished? Probably yes, as it's only on one side.
        self.output_queue.enqueue(item)

        if self._should_stop():
            self.stop()

    def close(self):
        self.output_queue.close()
