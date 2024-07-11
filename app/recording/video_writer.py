import time

import cv2
from PySide6.QtCore import QThread

from app.dataflow.qqueue import QQueue


class BufferVideoWriter(QThread):
    def __init__(self, video_writer: cv2.VideoWriter, video_buffer: QQueue):
        super(BufferVideoWriter, self).__init__()

        self.video_writer = video_writer
        self.video_buffer = video_buffer

        self.running = False

    def run(self):
        self.running = True
        ended = False
        while self.running or not ended:
            while not self.video_buffer.is_empty():
                item = self.video_buffer.dequeue()
                if item is QQueue.End:
                    self.running = False
                    ended = True
                    break

                frame, frame_index, timestamp = item
                self.video_writer.write(frame)
            time.sleep(0.01)
        print("Video writer stopped")
        self.video_writer.release()
        print("Video writer released")

    def stop(self):
        self.running = False
