from pathlib import Path

import cv2

from app.dataflow.qqueue import QQueue
from app.process.queue_process import QueueProcess

import logging

from util.trace import Trace

logger = logging.getLogger("grimace_box."+__name__)


class BufferVideoWriter(QueueProcess):
    @Trace.trace(logger)
    def __init__(self, video_writer: cv2.VideoWriter, queue_size: int, timestamp_file: Path = None):
        super(BufferVideoWriter, self).__init__(queue_size, wait_time=0.01)

        self.video_writer = video_writer
        self.timestamp_file = timestamp_file

        self.timestamp_file_handle = None

    @Trace.trace(logger)
    def setup(self):
        if self.timestamp_file is not None:
            self.timestamp_file_handle = self.timestamp_file.open("w+")
            self.timestamp_file_handle.write("frame_index,timestamp\n")

    def process_item(self, item):
        frame, frame_index, timestamp = item
        self.video_writer.write(frame)
        if self.timestamp_file_handle is not None:
            self.timestamp_file_handle.write(f"{frame_index},{timestamp}\n")

    @Trace.trace(logger)
    def close(self):
        if self.timestamp_file_handle is not None:
            self.timestamp_file_handle.close()
        self.video_writer.release()

    def check_health(self, *args, prefix: str = "", fill_threshold: float = 0.1, **kwargs) -> dict:
        report = {"warnings": {}}

        queue_fill_level = self.queue.get_fill_level()
        report[prefix+"video_writer_queue_fill_level"] = queue_fill_level

        warning = None
        if queue_fill_level > fill_threshold:
            warning = f"Video writer queue fill level: {queue_fill_level * 100:.2f}%"
        report["warnings"][prefix+"video_writer_queue_fill"] = warning

        return report
