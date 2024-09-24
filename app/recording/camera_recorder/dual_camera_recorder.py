import time
from typing import Optional

import numpy as np
from PySide6.QtCore import QThread, Signal
from pypylon import pylon

from app.config.camera import CameraConfig
from app.dataflow.qqueue import QQueue, IQueue
from app.recording.camera_recorder.source.base_source import CameraSource
from app.recording.camera_recorder.source.file_source import FileCameraSource
from app.recording.camera_recorder.source.pylon_source import PylonCameraSource
from app.recording.recording_context import RecordingContext

import logging

from grimace.camera_identifier import CameraIdentifier
from util.trace import Trace

logger = logging.getLogger("grimace_recorder.app.recording.dual_video_recorder")


def build_pylon_camera_source(config: CameraConfig):
    tlf = pylon.TlFactory.GetInstance()
    devices = tlf.EnumerateDevices()
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

            self.video_buffer: Optional[QQueue] = None

            self.timestamp_history = [0] * 10
            self.fps = 0.0

            self.last_frame_number: Optional[int] = None
            self.frame_index = 0

            self.dropped_frames = 0
            self.buffer_fill_level = 0.0

            self.camera_identifier_scores = []

            # TODO: This is a temporary solution
            self.target_fps = 30.0

        def get_width(self):
            return self.source.get_width()

        def get_height(self):
            return self.source.get_height()

        @Trace.trace(logger)
        def set_video_buffer(self, video_buffer: IQueue):
            self.video_buffer = video_buffer

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
    def __init__(self, camera_identifier: CameraIdentifier):
        super(DualCameraRecorder, self).__init__()

        self.camera_identifier = camera_identifier

        self.top_camera: Optional[DualCameraRecorder.Camera] = None
        self.front_camera: Optional[DualCameraRecorder.Camera] = None

        self.recording_context: Optional[RecordingContext] = None

        self.running = False

    @Trace.trace(logger)
    def set_top_camera(self, source: CameraSource | None):
        if self.running:
            raise Exception("Cannot change camera source while recorder is running")

        # TODO: Now that i open the camera before setting the source, there's an error if i try to use the same camera
        #  Temp solution is to first set the source to None, then set the new source
        #  Maybe make a close method that closes the camera and sets the source to None
        #  so the caller has the responsibility to close the camera before setting a new source
        if self.top_camera is not None:
            self.top_camera.close()
            self.top_camera = None

        if source is not None:
            self.top_camera = DualCameraRecorder.Camera(source)

    @Trace.trace(logger)
    def set_front_camera(self, source: CameraSource | None):
        if self.running:
            raise Exception("Cannot change camera source while recorder is running")

        if self.front_camera is not None:
            self.front_camera.close()
            self.front_camera = None

        if source is not None:
            self.front_camera = DualCameraRecorder.Camera(source)

    @Trace.trace(logger)
    def set_recording_context(self, recording_context: RecordingContext | None):
        self.recording_context = recording_context

    def handle_frame(self, camera: Camera, frame: np.ndarray, timestamp: float):
        if camera.timestamp_offset is None:
            camera.set_timestamp_offset(timestamp)

        # TODO: This is a temporary solution
        if len(camera.camera_identifier_scores) < 10 and camera.frame_index % 30 == 0:
            camera.camera_identifier_scores.append(self.camera_identifier.score(frame))

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
        if front_camera is not None:
            front_camera.source.stop()
            if front_camera.video_buffer is not None:
                front_camera.video_buffer.close()

    def check_health(self):
        report = {"warnings": {}}

        top_camera = self.top_camera
        front_camera = self.front_camera

        for camera, name in [(top_camera, "top"), (front_camera, "front")]:
            if camera is None:
                continue

            warning = None
            # Arbitrary threshold of 10% buffer fill. The buffer should usually be practically empty
            if camera.buffer_fill_level > 0.1:
                warning = f"{name.capitalize()} camera buffer fill level: {camera.buffer_fill_level * 100:.2f}%"
            report["warnings"][f"{name}_camera_buffer_fill"] = warning

            warning = None
            # Arbitrary threshold of 5% below target FPS. The FPS should usually be very close to the target
            if camera.fps < camera.target_fps * 0.95:
                warning = f"{name.capitalize()} camera FPS: {camera.fps:.2f} (expected {camera.target_fps})"
            report["warnings"][f"{name}_camera_fps"] = warning

            warning = None
            # Dropped frames should be 0. If not, there is probably a problem
            if camera.dropped_frames > 0:
                warning = f"{name.capitalize()} camera dropped {camera.dropped_frames} frames"
            report["warnings"][f"{name}_camera_dropped_frames"] = warning

        if top_camera is not None and front_camera is not None:
            top_mean_identifier = np.mean(top_camera.camera_identifier_scores)
            front_mean_identifier = np.mean(front_camera.camera_identifier_scores)
            warning = None
            # The camera identifier score should be close to 1 for the front camera and close to 0 for the top camera
            # If the mean identifier score is higher for the top camera, the cameras are likely switched
            if top_mean_identifier > front_mean_identifier:
                warning = "Top and front camera are likely switched. Make sure you have selected the correct devices"
            report["warnings"]["cameras_switched"] = warning

        return report

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
