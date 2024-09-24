import json
from pathlib import Path
from typing import Tuple

from app.config.camera import CameraConfig
from app.config.grimace import GrimaceConfig
from app.config.pose_top import PoseTopConfig
from app.config.recording import RecordingConfig
from app.config.video_files import VideoFilesConfig

Config = Tuple[CameraConfig, CameraConfig, RecordingConfig, VideoFilesConfig, GrimaceConfig, PoseTopConfig]


class ConfigV1Parser:
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
            target_directory=json_config["target_directory"]
        )

    @classmethod
    def parse_grimace_config(cls, json_config: dict) -> GrimaceConfig:
        return GrimaceConfig(
            grimace_model=json_config["grimace_model"],
            frame_interval=json_config["frame_interval"],
            frame_quality_device=json_config["frame_quality_device"],
            face_cropper_device=json_config["face_cropper_device"],
            grimace_scoring_device=json_config["grimace_scoring_device"],
        )

    @classmethod
    def parse_pose_config(cls, json_config: dict) -> PoseTopConfig:
        return PoseTopConfig(
            show_preview=json_config["show_preview"],
            pose_model=json_config["pose_model"],
            pose_device=json_config["pose_device"],
        )

    @classmethod
    def parse(cls, json_config: dict) -> Config:
        camera_top_config = ConfigV1Parser.parse_camera_config(json_config["camera_top"])
        camera_front_config = ConfigV1Parser.parse_camera_config(json_config["camera_front"])
        recording_config = ConfigV1Parser.parse_recording_config(json_config["recording"])
        video_files_config = ConfigV1Parser.parse_video_files_config(json_config["video_files"])
        grimace_config = ConfigV1Parser.parse_grimace_config(json_config["grimace"])
        pose_top_config = ConfigV1Parser.parse_pose_config(json_config["pose_top"])

        return (camera_top_config, camera_front_config, recording_config,
                video_files_config, grimace_config, pose_top_config)


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
            "target_directory": video_files_config.target_directory
        }

    @classmethod
    def serialize_grimace_config(cls, grimace_config: GrimaceConfig) -> dict:
        return {
            "grimace_model": grimace_config.grimace_model,
            "frame_interval": grimace_config.frame_interval,
            "frame_quality_device": grimace_config.frame_quality_device,
            "face_cropper_device": grimace_config.face_cropper_device,
            "grimace_scoring_device": grimace_config.grimace_scoring_device,
        }

    @classmethod
    def serialize_pose_config(cls, pose_config: PoseTopConfig):
        return {
            "show_preview": pose_config.show_preview,
            "pose_model": pose_config.pose_model,
            "pose_device": pose_config.pose_device,
        }

    @classmethod
    def serialize(cls, config: Config) -> dict:
        camera_top_config = config[0]
        camera_front_config = config[1]
        recording_config = config[2]
        video_files_config = config[3]
        grimace_config = config[4]
        pose_top_config = config[5]

        return {
            "version": "v1",
            "camera_top": ConfigSerializer.serialize_camera_config(camera_top_config),
            "camera_front": ConfigSerializer.serialize_camera_config(camera_front_config),
            "recording": ConfigSerializer.serialize_recording_config(recording_config),
            "video_files": ConfigSerializer.serialize_video_files_config(video_files_config),
            "grimace": ConfigSerializer.serialize_grimace_config(grimace_config),
            "pose_top": ConfigSerializer.serialize_pose_config(pose_top_config),
        }


class JsonConfigSerializer:
    @classmethod
    def load(cls, config_file: Path) -> Config:
        with config_file.open("r") as f:
            json_config = json.load(f)

        version = json_config["version"]

        if version == "v1":
            parser = ConfigV1Parser
        else:
            raise ValueError(f"Unknown config version: {version}")

        return parser.parse(json_config)

    @classmethod
    def save(cls, config_file: Path, config: Config):
        config_dict = ConfigSerializer.serialize(config)

        with config_file.open("w") as f:
            json.dump(config_dict, f, indent=4)
