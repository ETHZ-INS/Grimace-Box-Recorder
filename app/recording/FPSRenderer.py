import logging

import cv2

from app.dataflow.qqueue import IQueue
from util.trace import Trace

logger = logging.getLogger("grimace_box."+__name__)


class FPSRenderer(IQueue):
    @Trace.trace(logger)
    def __init__(self, output_queue: IQueue, timestamp_history_size: int = 10):
        self.output_queue = output_queue
        self.timestamp_history_size = timestamp_history_size

        self.timestamp_history = []
        self.timestamp_index = 0

    @Trace.trace(logger)
    def reset(self):
        self.timestamp_history = []
        self.timestamp_index = 0

    def enqueue(self, item):
        frame, frame_number, timestamp = item

        if len(self.timestamp_history) < self.timestamp_history_size:
            self.timestamp_history.append(timestamp)
        else:
            self.timestamp_history[self.timestamp_index] = timestamp
        self.timestamp_index = (self.timestamp_index + 1) % self.timestamp_history_size

        if len(self.timestamp_history) > 1:
            if len(self.timestamp_history) < self.timestamp_history_size:
                oldest_timestamp = self.timestamp_history[0]
            else:
                oldest_timestamp = self.timestamp_history[self.timestamp_index]
            time_diff = timestamp - oldest_timestamp
            # TODO: Prevent division by zero. Can this be done better?
            if time_diff > 0.00001:
                fps = (len(self.timestamp_history) - 1) / time_diff
            else:
                fps = 0.0
        else:
            fps = 0.0

        frame = frame.copy()
        # TODO: deactivated due to lab meeting feedback. Remove properly if definitely not needed anymore
        #frame = cv2.putText(frame, f"{fps:.2f} FPS", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        self.output_queue.enqueue((frame, frame_number, timestamp))

    @Trace.trace(logger)
    def close(self):
        self.output_queue.close()
