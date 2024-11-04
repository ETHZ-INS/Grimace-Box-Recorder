import logging

from pypylon import pylon, genicam

from app.config.camera import CameraConfig
from app.recording.camera_recorder.source.base_source import CameraSource
from app.recording.camera_recorder.source.file_source import FileCameraSource
from app.recording.camera_recorder.source.pylon_source import PylonCameraSource
from util.trace import Trace


logger = logging.getLogger("grimace_box."+__name__)


class CameraFactory:
    @staticmethod
    @Trace.trace(logger)
    def create_pylon_camera(config: CameraConfig) -> CameraSource | None:
        if config.camera_id is None:
            return None

        tlf = pylon.TlFactory.GetInstance()
        devices = tlf.EnumerateDevices()
        devices = [device for device in devices if device.GetSerialNumber() == config.camera_id]
        if len(devices) == 0:
            raise ValueError(f"Device with serial number {config.camera_id} not found")
        camera = pylon.InstantCamera(tlf.CreateDevice(devices[0]))

        camera.Open()

        if config.config_file is not None:
            pylon.FeaturePersistence.Load(config.config_file, camera.GetNodeMap(), True)

        #if config.fps is None or config.fps < 2:
        #    raise ValueError("FPS must be at least 2")

        #if hasattr(camera, 'AcquisitionFrameRateAbs'):
        #    camera.AcquisitionFrameRateAbs.SetValue(config.fps)
        #else:
        #    camera.AcquisitionFrameRate.SetValue(config.fps)

        #camera.AcquisitionFrameRateEnable.SetValue(True)

        # TODO: Make this configurable
        camera.MaxNumBuffer = 1000

        return PylonCameraSource(camera)

    @staticmethod
    @Trace.trace(logger)
    def create_video_file_camera(config: CameraConfig) -> CameraSource | None:
        if config.video_file is None:
            return None
        return FileCameraSource(config.video_file)

    @staticmethod
    @Trace.trace(logger)
    def create_camera(config: CameraConfig) -> CameraSource | None:
        """
        Return the correct camera source based on the camera type.

        :return: CameraSource if the camera config is valid and complete,
        None if the camera config is valid but incomplete
        :raises: ValueError if the camera config is invalid
        """
        if config.camera_type == "Pylon":
            return CameraFactory.create_pylon_camera(config)
        elif config.camera_type == "Video File":
            return CameraFactory.create_video_file_camera(config)
        else:
            raise ValueError(f"Unknown camera type: {config.camera_type}")
