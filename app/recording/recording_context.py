import time

from PySide6.QtCore import QObject, Signal


class RecordingContext(QObject):
    stop_signal = Signal()

    def __init__(self, recording_duration: float = None):
        super(RecordingContext, self).__init__()

        self.recording_duration = recording_duration

        self.started = False
        self.recording = False
        self.start_time = None
        self.latest_time = None
        self.stop_time = None

    def recording_time(self):
        if not self.started:
            return 0.0
        if self.stop_time is not None:
            return self.stop_time - self.start_time
        return self.latest_time - self.start_time

    def set_latest_time(self, latest_time: float):
        self.latest_time = latest_time

    def start(self, start_time: float = None):
        self.started = True
        self.recording = True
        self.start_time = start_time if start_time is not None else time.time()
        self.stop_time = None

    def stop(self, stop_time: float = None):
        if not self.started or not self.recording:
            return
        self.stop_time = stop_time if stop_time is not None else self.latest_time
        self.recording = False
        print("Recording stopped")
        self.stop_signal.emit()

    def should_stop(self, stop_time: float = None):
        if not self.started or self.recording_duration is None:
            return False
        stop_time = stop_time if stop_time is not None else self.latest_time
        return stop_time - self.start_time >= self.recording_duration
