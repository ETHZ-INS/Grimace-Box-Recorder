from pypylon import pylon

from app.config.camera import CameraConfig
from app.recording.camera_recorder.source.base_source import CameraSource
from app.recording.camera_recorder.source.file_source import FileCameraSource
from app.recording.camera_recorder.source.pylon_source import PylonCameraSource


class CameraFactory:
    @staticmethod
    def create_pylon_camera(config: CameraConfig) -> CameraSource:
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

    @staticmethod
    def create_video_file_camera(config: CameraConfig) -> CameraSource:
        return FileCameraSource(config.video_file)

    @staticmethod
    def create_camera(config: CameraConfig) -> CameraSource:
        if config.camera_type == "Pylon":
            return CameraFactory.create_pylon_camera(config)
        elif config.camera_type == "Video File":
            return CameraFactory.create_video_file_camera(config)
        else:
            raise ValueError(f"Unknown camera type: {config.camera_type}")
