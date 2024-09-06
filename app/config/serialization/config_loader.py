import json
from pathlib import Path
from typing import Tuple

from app.config.camera import CameraConfig
from app.config.grimace import GrimaceConfig
from app.config.pose_top import PoseTopConfig
from app.config.recording import RecordingConfig
from app.config.video_files import VideoFilesConfig


class ConfigV1Loader:
    @classmethod
    def parse_camera_config(cls, json_config: dict) -> CameraConfig:
        return CameraConfig(
            camera_type=json_config["camera_type"],
            camera_id=json_config["camera_id"],
            config_file=json_config["config_file"],
            fps=json_config["fps"],
            video_file=json_config["video_file"],
        )

    @classmethod
    def parse_recording_config(cls, json_config: dict) -> RecordingConfig:
        return RecordingConfig(
            mode=json_config["recording_mode"],
            duration=json_config["recording_duration"],
        )

    @classmethod
    def parse_video_files_config(cls, json_config: dict) -> VideoFilesConfig:
        return VideoFilesConfig(
            target_directory=json_config["target_directory"],
            naming_mode=json_config["naming_mode"],
            top_templates=json_config["top_templates"],
            front_templates=json_config["front_templates"],
            grimace_results_templates=json_config["grimace_results_template"],
            pose_results_templates=json_config["pose_results_template"]
        )

    @classmethod
    def parse_grimace_config(cls, json_config: dict) -> GrimaceConfig:
        return GrimaceConfig(
            enabled=json_config["enabled"],
            grimace_model=json_config["grimace_model"],
            frame_interval=json_config["frame_interval"],
            frame_quality_device=json_config["frame_quality_device"],
            face_cropper_device=json_config["face_cropper_device"],
            grimace_scoring_device=json_config["grimace_scoring_device"],
        )

    @classmethod
    def parse_pose_config(cls, json_config: dict) -> PoseTopConfig:
        return PoseTopConfig(
            enabled=json_config["enabled"],
            show_preview=json_config["show_preview"],
            pose_model=json_config["pose_model"],
            pose_device=json_config["pose_device"],
        )

    @classmethod
    def parse(cls, json_config: dict) -> Tuple[CameraConfig, CameraConfig, RecordingConfig, VideoFilesConfig, GrimaceConfig, PoseTopConfig]:
        camera_top_config = ConfigV1Loader.parse_camera_config(json_config["camera_top"])
        camera_front_config = ConfigV1Loader.parse_camera_config(json_config["camera_front"])
        recording_config = ConfigV1Loader.parse_recording_config(json_config["recording"])
        video_files_config = ConfigV1Loader.parse_video_files_config(json_config["video_files"])
        grimace_config = ConfigV1Loader.parse_grimace_config(json_config["grimace"])
        pose_top_config = ConfigV1Loader.parse_pose_config(json_config["pose_top"])

        return camera_top_config, camera_front_config, recording_config, video_files_config, grimace_config, pose_top_config


class ConfigSerializer:
    @classmethod
    def serialize_camera_config(cls, camera_config: CameraConfig) -> dict:
        return {
            "camera_type": camera_config.camera_type,
            "camera_id": camera_config.camera_id,
            "config_file": camera_config.config_file,
            "fps": camera_config.fps,
            "video_file": camera_config.video_file
        }

    @classmethod
    def serialize_recording_config(cls, recording_config: RecordingConfig) -> dict:
        return {
            "recording_mode": recording_config.mode,
            "recording_duration": recording_config.duration,
        }

    @classmethod
    def serialize_video_files_config(cls, video_files_config: VideoFilesConfig) -> dict:
        return {
            "target_directory": video_files_config.target_directory,
            "naming_mode": video_files_config.naming_mode,
            "top_templates": video_files_config.top_templates,
            "front_templates": video_files_config.front_templates,
            "grimace_results_template": video_files_config.grimace_results_templates,
            "pose_results_template": video_files_config.pose_results_templates,
        }

    @classmethod
    def serialize_grimace_config(cls, grimace_config: GrimaceConfig) -> dict:
        return {
            "enabled": grimace_config.enabled,
            "grimace_model": grimace_config.grimace_model,
            "frame_interval": grimace_config.frame_interval,
            "frame_quality_device": grimace_config.frame_quality_device,
            "face_cropper_device": grimace_config.face_cropper_device,
            "grimace_scoring_device": grimace_config.grimace_scoring_device,
        }

    @classmethod
    def serialize_pose_config(cls, pose_config: PoseTopConfig):
        return {
            "enabled": pose_config.enabled,
            "show_preview": pose_config.show_preview,
            "pose_model": pose_config.pose_model,
            "pose_device": pose_config.pose_device,
        }


class ConfigLoader:
    @classmethod
    def load(cls, config_file: Path) -> Tuple[CameraConfig, CameraConfig, RecordingConfig, VideoFilesConfig, GrimaceConfig, PoseTopConfig]:
        with config_file.open("r") as f:
            json_config = json.load(f)

        version = json_config["version"]

        if version == "v1":
            return ConfigV1Loader.parse(json_config)

        raise ValueError(f"Unknown config version: {version}")

    @classmethod
    def save(cls, config_file: Path, camera_top_config: CameraConfig, camera_front_config: CameraConfig,
             recording_config: RecordingConfig, video_files_config: VideoFilesConfig, grimace_config: GrimaceConfig,
             pose_top_config: PoseTopConfig):
        with config_file.open("w") as f:
            json.dump({
                "version": "v1",
                "camera_top": ConfigSerializer.serialize_camera_config(camera_top_config),
                "camera_front": ConfigSerializer.serialize_camera_config(camera_front_config),
                "recording": ConfigSerializer.serialize_recording_config(recording_config),
                "video_files": ConfigSerializer.serialize_video_files_config(video_files_config),
                "grimace": ConfigSerializer.serialize_grimace_config(grimace_config),
                "pose_top": ConfigSerializer.serialize_pose_config(pose_top_config),
            }, f, indent=4)
