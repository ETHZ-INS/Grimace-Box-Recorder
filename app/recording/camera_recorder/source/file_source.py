import logging
import time

import cv2
import numpy as np

from app.recording.camera_recorder.source.base_source import CameraSource
from util.trace import Trace

logger = logging.getLogger("grimace_box."+__name__)


class FileCameraSource(CameraSource):
    @Trace.trace(logger)
    def __init__(self, video_file: str):
        self.video_file = video_file
        self.vc = cv2.VideoCapture(video_file)
        self.width = int(self.vc.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.vc.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = float(self.vc.get(cv2.CAP_PROP_FPS))
        self.start_time = None
        self.last_frame_time = None
        self.frame_number = 0

    @Trace.trace(logger)
    def get_width(self):
        return self.width

    @Trace.trace(logger)
    def get_height(self):
        return self.height

    @Trace.trace(logger)
    def get_fps(self):
        return self.fps

    @Trace.trace(logger)
    def start(self):
        pass

    @Trace.trace(logger)
    def stop(self):
        pass

    @Trace.trace(logger)
    def close(self):
        self.vc.release()

    def grab_frame(self) -> (bool, int, float, np.ndarray):
        now = time.time()
        if self.start_time is None:
            self.start_time = now

        next_frame_time = self.start_time + (self.frame_number+1) * (1 / self.fps)

        if self.last_frame_time is None or now > next_frame_time:
            ret, frame = self.vc.read()
            if not ret:
                self.vc.set(cv2.CAP_PROP_POS_FRAMES, 0)
                return False, None, None, None
            if len(frame.shape) == 2:
                frame = frame[:, :, np.newaxis]
            if frame.shape[2] > 1:
                #frame = np.mean(frame, axis=2, keepdims=True)
                frame = frame[:, :, :1]
                frame = np.ascontiguousarray(frame)
            self.last_frame_time = next_frame_time
            self.frame_number += 1
            return True, self.frame_number, next_frame_time, frame
        else:
            return False, None, None, None
