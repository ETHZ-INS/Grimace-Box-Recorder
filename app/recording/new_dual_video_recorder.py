import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, Optional

import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal
from pypylon import pylon

from app.config.camera import CameraConfig
from app.dataflow.qqueue import QQueue
from app.dataflow.qvariable import QVariable
from app.recording.recording_context import RecordingContext

import logging

from util.trace import Trace

logger = logging.getLogger("grimace_recorder.app.recording.dual_video_recorder")


class CameraSource(ABC):
    @abstractmethod
    def get_width(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_height(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_fps(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def grab_frame(self) -> (bool, int, float, np.ndarray):
        raise NotImplementedError

    @abstractmethod
    def start(self):
        raise NotImplementedError

    @abstractmethod
    def stop(self):
        raise NotImplementedError

    def close(self):
        pass


class PylonCameraSource(CameraSource):
    def __init__(self, camera: pylon.InstantCamera):
        self.camera = camera
        self.width = camera.Width.GetValue()
        self.height = camera.Height.GetValue()

        if hasattr(camera, 'AcquisitionFrameRateAbs'):
            self.fps = camera.AcquisitionFrameRateAbs.GetValue()
        else:
            self.fps = camera.AcquisitionFrameRate.GetValue()

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def get_fps(self):
        return self.fps

    def start(self):
        self.camera.StartGrabbing(pylon.GrabStrategy_OneByOne)

    def stop(self):
        self.camera.StopGrabbing()

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
            # The emulated pylon cameras return 0 for timestamp
            timestamp = None
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


class FileCameraSource(CameraSource):
    def __init__(self, video_file: str):
        self.video_file = video_file
        self.vc = cv2.VideoCapture(video_file)
        self.width = int(self.vc.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.vc.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = float(self.vc.get(cv2.CAP_PROP_FPS))
        self.start_time = None
        self.last_frame_time = None
        self.frame_number = 0

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def get_fps(self):
        return self.fps

    def start(self):
        pass

    def stop(self):
        pass

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
                raise Exception("Unable to read next video frame")
            if len(frame.shape) == 2:
                frame = frame[:, :, np.newaxis]
            if frame.shape[2] > 1:
                #frame = np.mean(frame, axis=2, keepdims=True)
                frame = frame[:, :, :1]
            self.last_frame_time = next_frame_time
            self.frame_number += 1
            return True, self.frame_number, next_frame_time, frame
        else:
            return False, None, None, None


def build_pylon_camera_source(config: CameraConfig):
    tlf = pylon.TlFactory.GetInstance()
    devices = tlf.EnumerateDevices()
    if len(devices) == 0:
        raise ValueError("No devices found")
    devices = [device for device in devices if device.GetSerialNumber() == config.camera_id]
    if len(devices) == 0:
        raise ValueError(f"Device with serial number {config.camera_id} not found")
    camera = pylon.InstantCamera(tlf.CreateDevice(devices[0]))

    camera.Open()

    if config.config_file is not None:
        pylon.FeaturePersistence.Load(config.config_file, camera.GetNodeMap(), True)

    if hasattr(camera, 'AcquisitionFrameRateAbs'):
        camera.AcquisitionFrameRateAbs.SetValue(config.fps)
    else:
        camera.AcquisitionFrameRate.SetValue(config.fps)

    camera.AcquisitionFrameRateEnable.SetValue(True)

    camera.MaxNumBuffer = 1000

    return PylonCameraSource(camera)


def build_file_camera_source(config: CameraConfig):
    return FileCameraSource(config.video_file)


def build_camera_source(config: CameraConfig):
    if config.camera_type == "Pylon":
        return build_pylon_camera_source(config)
    elif config.camera_type == "Video File":
        return build_file_camera_source(config)
    else:
        raise ValueError(f"Unknown Camera Type: {config.camera_type}")


class DualCameraRecorder(QThread):
    """
    Using a single thread to grab frames from two cameras
    More efficient and less error-prone than using two threads
    """

    top_error_signal = Signal(str)
    front_error_signal = Signal(str)
    stop_signal = Signal()

    class Camera:
        @Trace.trace(logger)
        def __init__(self, source: CameraSource):
            self.source = source
            self.timestamp_offset = None

            self.preview_buffer: Optional[QVariable] = None
            self.video_buffer: Optional[QQueue] = None
            self.grimace_buffer: Optional[QQueue] = None

            self.timestamp_history = [0] * 10
            self.fps = 0.0

            self.last_frame_number: Optional[int] = None
            self.frame_index = 0

            self.dropped_frames = 0
            self.buffer_fill_level = 0.0

        def get_width(self):
            return self.source.get_width()

        def get_height(self):
            return self.source.get_height()

        @Trace.trace(logger)
        def set_preview_buffer(self, preview_buffer: QVariable):
            self.preview_buffer = preview_buffer

        @Trace.trace(logger)
        def set_video_buffer(self, video_buffer: QQueue):
            self.video_buffer = video_buffer

        @Trace.trace(logger)
        def set_grimace_buffer(self, grimace_buffer: QQueue):
            self.grimace_buffer = grimace_buffer

        def set_timestamp_offset(self, timestamp: float):
            self.timestamp_offset = timestamp

        def reset_frame_index(self):
            self.frame_index = 0

        def reset_frame_number(self):
            self.last_frame_number = None

        def reset_dropped_frames(self):
            self.dropped_frames = 0

        def reset_timestamp_history(self):
            self.timestamp_history = [0] * 10

        def reset_timestamp_offset(self):
            self.timestamp_offset = None

        @Trace.trace(logger)
        def reset(self):
            self.reset_frame_index()
            self.reset_frame_number()
            self.reset_dropped_frames()
            self.reset_timestamp_history()
            self.reset_timestamp_offset()

        def close(self):
            self.source.close()

    @Trace.trace(logger)
    def __init__(self):
        super(DualCameraRecorder, self).__init__()

        self.top_camera: Optional[DualCameraRecorder.Camera] = None
        self.front_camera: Optional[DualCameraRecorder.Camera] = None

        self.recording_context: Optional[RecordingContext] = None

        self.running = False

    @Trace.trace(logger)
    def set_top_camera(self, source: CameraSource | None, start: bool = True):
        if self.running:
            self.stop()
            self.wait()

        if self.top_camera is not None:
            self.top_camera.close()
            self.top_camera = None

        if source is not None:
            self.top_camera = DualCameraRecorder.Camera(source)

        if start:
            self.start()

    @Trace.trace(logger)
    def set_front_camera(self, source: CameraSource | None, start: bool = True):
        if self.running:
            self.stop()
            self.wait()

        if self.front_camera is not None:
            self.front_camera.close()
            self.front_camera = None

        if source is not None:
            self.front_camera = DualCameraRecorder.Camera(source)

        if start:
            self.start()

    @Trace.trace(logger)
    def set_recording_context(self, recording_context: RecordingContext):
        self.recording_context = recording_context

    def handle_frame(self, camera: Camera, frame: np.ndarray, timestamp: float):
        if camera.timestamp_offset is None:
            camera.set_timestamp_offset(timestamp)

        normalized_timestamp = timestamp - camera.timestamp_offset

        recording_context = self.recording_context

        if recording_context is not None:
            if not recording_context.started:
                recording_context.start(normalized_timestamp)
            recording_context.set_latest_time(normalized_timestamp)
            if recording_context.recording and recording_context.should_stop():
                self.stop_signal.emit()

        elapsed = timestamp - camera.timestamp_history[camera.frame_index % 10]
        camera.timestamp_history[camera.frame_index % 10] = timestamp

        fps = 10 / elapsed
        camera.fps = fps

        video_buffer = camera.video_buffer
        if video_buffer is not None:
            video_buffer.enqueue((frame, camera.frame_index, normalized_timestamp))

        grimace_buffer = camera.grimace_buffer
        if grimace_buffer is not None:
            grimace_buffer.enqueue((frame, camera.frame_index, normalized_timestamp))

        frame = frame.copy()
        frame = cv2.putText(frame, f"{fps:.2f} FPS", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        #if "psBC" in camera.source.video_file:
        #    yolo_frame = np.concatenate([frame, frame, frame], axis=2)
        #    instance = self.top_pose_estimator.get_instance(yolo_frame)
        #    for point in instance.pose:
        #        if point.conf > 0.5:
        #            x = round(point.x * frame.shape[1])
        #            y = round(point.y * frame.shape[0])
        #            frame = cv2.circle(frame,(x, y),radius=5, thickness=-1,color=(255,0,0))

        preview_buffer = camera.preview_buffer
        if preview_buffer is not None:
            preview_buffer.set(frame)

        #num_buffered_frames = camera.camera.NumReadyBuffers.GetValue()
        #camera.buffer_fill_level = num_buffered_frames / 1000

        camera.frame_index += 1

    @Trace.trace(logger)
    def run(self):
        top_camera = self.top_camera
        front_camera = self.front_camera

        if top_camera is not None:
            top_camera.reset()
        if front_camera is not None:
            front_camera.reset()

        if top_camera is not None:
            try:
                top_camera.source.start()
            except KeyboardInterrupt:
                return
            except Exception as e:
                logger.exception("Error starting grabbing from top camera")
                self.top_error_signal.emit(str(e))
                top_camera.close()
                top_camera = None

        if front_camera is not None:
            try:
                front_camera.source.start()
            except KeyboardInterrupt:
                return
            except Exception as e:
                logger.exception("Error starting grabbing from front camera")
                self.front_error_signal.emit(str(e))
                front_camera.close()
                front_camera = None

        while self.running:
            any_frames = False

            if top_camera is not None:
                try:
                    ret, frame_number, timestamp, frame = self.top_camera.source.grab_frame()
                    if ret:
                        self.handle_frame(top_camera, frame, timestamp)
                        any_frames = True
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.exception("Error grabbing frame from top camera")
                    top_camera.close()
                    top_camera = None
                    self.top_error_signal.emit(str(e))

            if front_camera is not None:
                try:
                    ret, frame_number, timestamp, frame = self.front_camera.source.grab_frame()
                    if ret:
                        self.handle_frame(front_camera, frame, timestamp)
                        any_frames = True
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.exception("Error grabbing frame from front camera")
                    front_camera.close()
                    front_camera = None
                    self.front_error_signal.emit(str(e))

            if not any_frames:
                # No frames were grabbed, sleep for a short time
                # (This could be increased to reduce CPU usage, but may cause latency and stuttering in preview)
                # The cameras will still be grabbing frames in the background and storing them in their buffers
                time.sleep(0.01)

        if top_camera is not None:
            top_camera.source.stop()
            if top_camera.video_buffer is not None:
                top_camera.video_buffer.close()
            if top_camera.grimace_buffer is not None:
                top_camera.grimace_buffer.close()
        if front_camera is not None:
            front_camera.source.stop()
            if front_camera.video_buffer is not None:
                front_camera.video_buffer.close()
            if front_camera.grimace_buffer is not None:
                front_camera.grimace_buffer.close()

    @Trace.trace(logger)
    def start(self, priority=QThread.Priority.InheritPriority):
        self.running = True
        super(DualCameraRecorder, self).start(priority)

    @Trace.trace(logger)
    def stop(self):
        self.running = False

    @Trace.trace(logger)
    def close(self):
        top_camera = self.top_camera
        if top_camera is not None:
            top_camera.close()
        front_camera = self.front_camera
        if front_camera is not None:
            front_camera.close()
