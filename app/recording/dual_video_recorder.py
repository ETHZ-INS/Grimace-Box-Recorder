import time
from pathlib import Path
from typing import Union, Optional

import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal
from pypylon import pylon

from app.dataflow.qqueue import QQueue
from app.dataflow.qvariable import QVariable
from app.recording.recording_context import RecordingContext

import logging

from util.trace import Trace

logger = logging.getLogger("grimace_recorder.app.recording.dual_video_recorder")


class PylonDualCameraRecorder(QThread):
    """
    Using a single thread to grab frames from two cameras
    More efficient and less error-prone than using two threads
    """

    top_error_signal = Signal(str)
    front_error_signal = Signal(str)
    stop_signal = Signal()

    class Camera:
        @Trace.trace(logger)
        def __init__(self, camera: Union[pylon.InstantCamera, str], fps: float = 30.0, config_file: Path = None):
            self.target_fps = fps
            self.config_file = config_file
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

            if isinstance(camera, str):
                tlf = pylon.TlFactory.GetInstance()
                devices = tlf.EnumerateDevices()
                if len(devices) == 0:
                    raise ValueError("No devices found")
                devices = [device for device in devices if device.GetSerialNumber() == camera]
                if len(devices) == 0:
                    raise ValueError(f"Device with serial number {camera} not found")
                camera = pylon.InstantCamera(tlf.CreateDevice(devices[0]))

            if not camera.IsOpen():
                camera.Open()

            self.serial_number = camera.GetDeviceInfo().GetSerialNumber()
            self.width = camera.Width.GetValue()
            self.height = camera.Height.GetValue()

            if config_file is not None:
                pylon.FeaturePersistence.Load(str(config_file), camera.GetNodeMap(), True)

            if hasattr(camera, 'AcquisitionFrameRateAbs'):
                camera.AcquisitionFrameRateAbs.SetValue(fps)
            else:
                camera.AcquisitionFrameRate.SetValue(fps)

            camera.AcquisitionFrameRateEnable.SetValue(True)

            camera.MaxNumBuffer = 1000

            self.camera = camera

        def get_width(self):
            return self.width

        def get_height(self):
            return self.height

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

    @Trace.trace(logger)
    def __init__(self):
        super(PylonDualCameraRecorder, self).__init__()

        self.top_camera: Optional[PylonDualCameraRecorder.Camera] = None
        self.front_camera: Optional[PylonDualCameraRecorder.Camera] = None

        self.recording_context: Optional[RecordingContext] = None

        self.running = False

    @Trace.trace(logger)
    def set_top_camera(self, camera: Optional[Union[pylon.InstantCamera, str]], fps: float = 30.0, config_file: Path = None, start: bool = True):
        if self.running:
            self.stop()
            self.wait()

        if self.top_camera is not None:
            self.top_camera.camera.Close()
            self.top_camera = None

        if camera is not None:
            self.top_camera = PylonDualCameraRecorder.Camera(camera, fps, config_file)

        if start:
            self.start()

    @Trace.trace(logger)
    def set_front_camera(self, camera: Optional[Union[pylon.InstantCamera, str]], fps: float = 30.0, config_file: Path = None, start: bool = True):
        if self.running:
            self.stop()
            self.wait()

        if self.front_camera is not None:
            self.front_camera.camera.Close()
            self.front_camera = None

        if camera is not None:
            self.front_camera = PylonDualCameraRecorder.Camera(camera, fps, config_file)

        if start:
            self.start()

    @Trace.trace(logger)
    def set_recording_context(self, recording_context: RecordingContext):
        self.recording_context = recording_context

    @Trace.trace(logger)
    def synchronize_camera_clocks(self):
        execute_functions = []
        if self.top_camera is not None:
            execute_functions.append(self.top_camera.camera.GevTimestampControlReset.Execute)
        if self.front_camera is not None:
            execute_functions.append(self.front_camera.camera.GevTimestampControlReset.Execute)
        for execute_function in execute_functions:
            execute_function()

    @Trace.trace(logger)
    def synchronize_camera_frames(self, top_camera: pylon.InstantCamera, front_camera: pylon.InstantCamera, frame_interval: float):
        top_grab_result = top_camera.RetrieveResult(1000, pylon.TimeoutHandling_Return)
        front_grab_result = front_camera.RetrieveResult(1000, pylon.TimeoutHandling_Return)

        if (not top_grab_result.IsValid() or not top_grab_result.GrabSucceeded()
                or not front_grab_result.IsValid() or not front_grab_result.GrabSucceeded()):
            top_grab_result.Release()
            front_grab_result.Release()
            raise RuntimeError("Unable to synchronize cameras")

        top_frame_timestamp = top_grab_result.GetTimeStamp()
        front_frame_timestamp = front_grab_result.GetTimeStamp()
        top_grab_result.Release()
        front_grab_result.Release()

        frame_interval *= 125000000

        if top_frame_timestamp < (front_frame_timestamp - frame_interval/2):
            num_frames_to_skip = round((front_frame_timestamp-top_frame_timestamp)/frame_interval)
            print("Num frames to skip:", num_frames_to_skip)
            for i in range(num_frames_to_skip):
                top_grab_result = top_camera.RetrieveResult(1000, pylon.TimeoutHandling_Return)
                if not top_grab_result.IsValid() or not top_grab_result.GrabSucceeded():
                    top_grab_result.Release()
                    raise RuntimeError("Unable to synchronize cameras")
                top_frame_timestamp = top_grab_result.GetTimeStamp()
                top_grab_result.Release()
        elif front_frame_timestamp < (top_frame_timestamp - frame_interval/2):
            num_frames_to_skip = round((top_frame_timestamp-front_frame_timestamp)/frame_interval)
            print("Num frames to skip:", num_frames_to_skip)
            for i in range(num_frames_to_skip):
                front_grab_result = front_camera.RetrieveResult(1000, pylon.TimeoutHandling_Return)
                if not front_grab_result.IsValid() or not front_grab_result.GrabSucceeded():
                    front_grab_result.Release()
                    raise RuntimeError("Unable to synchronize cameras")
                front_frame_timestamp = front_grab_result.GetTimeStamp()
                front_grab_result.Release()

        if abs(top_frame_timestamp - front_frame_timestamp) > frame_interval / 2:
            raise RuntimeError("Unable to synchronize cameras")

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

        preview_buffer = camera.preview_buffer
        if preview_buffer is not None:
            preview_buffer.set(frame)

        num_buffered_frames = camera.camera.NumReadyBuffers.GetValue()
        camera.buffer_fill_level = num_buffered_frames / 1000

        camera.frame_index += 1

    def grab_frame(self, camera: Camera) -> bool:
        if camera is None:
            raise TypeError("Camera is None")

        if camera.camera.IsCameraDeviceRemoved():
            raise Exception("Camera is not connected")

        if not camera.camera.IsOpen():
            raise Exception("Camera is not open")

        if not camera.camera.IsGrabbing():
            raise Exception("Camera is not grabbing")

        grab_result = camera.camera.RetrieveResult(0, pylon.TimeoutHandling_Return)

        try:
            if not grab_result.IsValid():
                grab_result.Release()
                return False

            if not grab_result.GrabSucceeded():
                grab_result.Release()
                return False

            timestamp = grab_result.GetTimeStamp()
            if timestamp == 0:
                timestamp = time.time()
            else:
                timestamp = timestamp / 125000000

            frame_number = grab_result.GetImageNumber()
            if camera.last_frame_number is not None and frame_number != camera.last_frame_number + 1:
                # TODO Document why inter-packet-delay had to be set to 3000
                print("Frame dropped", camera.last_frame_number, frame_number)
                camera.dropped_frames += 1
            camera.last_frame_number = frame_number

            frame = grab_result.GetArray()
            if len(frame.shape) == 2:
                frame = frame[:, :, np.newaxis]

            self.handle_frame(camera, frame, timestamp)
            return True
        finally:
            grab_result.Release()

    @Trace.trace(logger)
    def run(self):
        top_camera = self.top_camera
        front_camera = self.front_camera

        if top_camera is not None:
            top_camera.reset()
        if front_camera is not None:
            front_camera.reset()

        if top_camera is not None and front_camera is not None:
            try:
                self.synchronize_camera_clocks()
            except Exception as e:
                logger.warning("Failed to synchronize camera clocks: %s", str(e), stack_info=True)

        if top_camera is not None:
            try:
                top_camera.camera.StartGrabbing(pylon.GrabStrategy_OneByOne)
            except KeyboardInterrupt:
                return
            except Exception as e:
                logger.exception("Error starting grabbing from top camera")
                self.top_error_signal.emit(str(e))
                top_camera.camera.Close()
                top_camera = None

        if front_camera is not None:
            try:
                front_camera.camera.StartGrabbing(pylon.GrabStrategy_OneByOne)
            except KeyboardInterrupt:
                return
            except Exception as e:
                logger.exception("Error starting grabbing from front camera")
                self.front_error_signal.emit(str(e))
                front_camera.camera.Close()
                front_camera = None

        if top_camera is not None and front_camera is not None:
            if top_camera.target_fps != front_camera.target_fps:
                logger.warning("Unable to synchronize camera frames as they have different fps")
            else:
                try:
                    self.synchronize_camera_frames(top_camera.camera, front_camera.camera, 1/top_camera.target_fps)
                except Exception as e:
                    logger.warning("Failed to synchronize camera frames: %s", str(e))

        while self.running:
            any_frames = False

            if top_camera is not None:
                try:
                    frame_grabbed = self.grab_frame(top_camera)
                    any_frames |= frame_grabbed
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.exception("Error grabbing frame from top camera")
                    top_camera.camera.Close()
                    top_camera = None
                    self.top_error_signal.emit(str(e))

            if front_camera is not None:
                try:
                    frame_grabbed = self.grab_frame(front_camera)
                    any_frames |= frame_grabbed
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.exception("Error grabbing frame from front camera")
                    front_camera.camera.Close()
                    front_camera = None
                    self.front_error_signal.emit(str(e))

            if not any_frames:
                # No frames were grabbed, sleep for a short time
                # (This could be increased to reduce CPU usage, but may cause latency and stuttering in preview)
                # The cameras will still be grabbing frames in the background and storing them in their buffers
                time.sleep(0.01)

        if top_camera is not None:
            top_camera.camera.StopGrabbing()
            if top_camera.video_buffer is not None:
                top_camera.video_buffer.close()
            if top_camera.grimace_buffer is not None:
                top_camera.grimace_buffer.close()
        if front_camera is not None:
            front_camera.camera.StopGrabbing()
            if front_camera.video_buffer is not None:
                front_camera.video_buffer.close()
            if front_camera.grimace_buffer is not None:
                front_camera.grimace_buffer.close()

    @Trace.trace(logger)
    def start(self, priority=QThread.Priority.InheritPriority):
        self.running = True
        super(PylonDualCameraRecorder, self).start(priority)

    @Trace.trace(logger)
    def stop(self):
        self.running = False

    @Trace.trace(logger)
    def close(self):
        top_camera = self.top_camera
        if top_camera is not None:
            top_camera.camera.Close()
        front_camera = self.front_camera
        if front_camera is not None:
            front_camera.camera.Close()

