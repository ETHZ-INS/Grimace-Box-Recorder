from pathlib import Path

import cv2

from app.dataflow.qqueue import QQueue
from app.dataflow.queue_reader import QueueReader


class BufferVideoWriter(QueueReader):
    def __init__(self, video_writer: cv2.VideoWriter, video_buffer: QQueue, timestamp_file: Path = None):
        super(BufferVideoWriter, self).__init__(video_buffer, wait_time=0.01)

        self.video_writer = video_writer
        self.timestamp_file = timestamp_file

        self.timestamp_file_handle = None

    def setup(self):
        if self.timestamp_file is not None:
            self.timestamp_file_handle = self.timestamp_file.open("w+")
            self.timestamp_file_handle.write("frame_index,timestamp\n")

    def process_item(self, item):
        frame, frame_index, timestamp = item
        self.video_writer.write(frame)
        if self.timestamp_file_handle is not None:
            self.timestamp_file_handle.write(f"{frame_index},{timestamp}\n")

    def close(self):
        if self.timestamp_file_handle is not None:
            self.timestamp_file_handle.close()
        self.video_writer.release()
