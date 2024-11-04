import logging
import time

import numpy as np
from pypylon import pylon

from app.recording.camera_recorder.source.base_source import CameraSource
from util.trace import Trace

logger = logging.getLogger("grimace_box."+__name__)


class PylonCameraSource(CameraSource):
    @Trace.trace(logger)
    def __init__(self, camera: pylon.InstantCamera):
        self.camera = camera
        self.width = camera.Width.GetValue()
        self.height = camera.Height.GetValue()

        if hasattr(camera, 'AcquisitionFrameRateAbs'):
            self.fps = camera.AcquisitionFrameRateAbs.GetValue()
        else:
            self.fps = camera.AcquisitionFrameRate.GetValue()

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
        self.camera.StartGrabbing(pylon.GrabStrategy_OneByOne)

    @Trace.trace(logger)
    def stop(self):
        self.camera.StopGrabbing()

    @Trace.trace(logger)
    def close(self):
        self.camera.StopGrabbing()
        self.camera.Close()

    def process_grab_result(self, grab_result: pylon.GrabResult) -> (bool, int, float, np.ndarray):
        if not grab_result.IsValid():
            # I think this means there is no new frame available, but it might be the other one
            grab_result.Release()
            return False, None, None, None

        if not grab_result.GrabSucceeded():
            # TODO: Is this exception worthy?
            grab_result.Release()
            return False, None, None, None

        timestamp = grab_result.GetTimeStamp()
        if timestamp == 0:
            # The emulated pylon cameras (for test purposes only) return 0 for timestamp
            timestamp = time.time()
        else:
            timestamp = timestamp / 125000000

        frame_number = grab_result.GetImageNumber()

        frame = grab_result.GetArray()
        if len(frame.shape) == 2:
            frame = frame[:, :, np.newaxis]

        return True, frame_number, timestamp, frame

    def grab_frame(self) -> (bool, int, float, np.ndarray):
        if self.camera.IsCameraDeviceRemoved():
            raise Exception("Camera is not connected")

        if not self.camera.IsOpen():
            raise Exception("Camera is not open")

        if not self.camera.IsGrabbing():
            raise Exception("Camera is not grabbing")

        grab_result = self.camera.RetrieveResult(0, pylon.TimeoutHandling_Return)

        try:
            return self.process_grab_result(grab_result)
        finally:
            grab_result.Release()
