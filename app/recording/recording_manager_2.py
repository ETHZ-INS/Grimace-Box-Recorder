from pathlib import Path

import cv2
from PySide6.QtCore import QObject, QThread

from app.config.grimace import GrimaceConfig
from app.config.pose_top import PoseTopConfig
from app.dataflow.qvariable import QVariable
from app.model.files import FILE_TYPES, FileBuilder
from app.model.grimace_recorder_model import GrimaceRecorderModel
from app.recording.camera_recorder.camera_factory import CameraFactory
from app.recording.camera_recorder.dual_camera_recorder import DualCameraRecorder
from app.recording.front_video_pipeline_builder import FrontVideoPipelineBuilder
from app.recording.grimace_analysis_builder import GrimaceAnalyzerBuilder
from app.recording.pose_estimator_builder import PoseEstimatorBuilder
from app.recording.recording_timer import RecordingTimer
from app.recording.top_video_pipeline_builder import TopVideoPipelineBuilder
from app.recording.video_writer_builder import VideoWriterBuilder


class RecordingManager(QObject):
    def __init__(self, model: GrimaceRecorderModel):
        super(RecordingManager, self).__init__()

        self.model = model

        self.camera_recorder = DualCameraRecorder()

        self.top_video_pipeline_builder = TopVideoPipelineBuilder()
        self.front_video_pipeline_builder = FrontVideoPipelineBuilder()

        self.model.recording_state_signal.connect(self.on_recording_state_changed)
        self.model.top_camera_config_signal.connect(self.on_top_camera_config_changed)
        self.model.front_camera_config_signal.connect(self.on_front_camera_config_changed)

        self.model.video_files_config_signal.connect(self.on_video_files_config_changed)
        self.model.grimace_config_signal.connect(self.on_grimace_config_changed)
        self.model.pose_config_signal.connect(self.on_pose_config_changed)

        self.thread = QThread()
        self.moveToThread(self.thread)
        self.thread.start()

        # TODO: Is this the way?
        self.top_preview_queue = QVariable()
        self.top_preview_queue.value_set.connect(self.on_top_preview_frame)
        self.front_preview_queue = QVariable()
        self.front_preview_queue.value_set.connect(self.on_front_preview_frame)

        self.top_video_pipeline_builder.set_preview_queue(self.top_preview_queue)
        self.front_video_pipeline_builder.set_preview_queue(self.front_preview_queue)

        self.top_video_pipeline = None
        self.front_video_pipeline = None
        self.recording_timer = None

    def on_top_preview_frame(self):
        frame = self.top_preview_queue.get()
        self.model.set_top_camera_frame(frame[0])

    def on_front_preview_frame(self):
        frame = self.front_preview_queue.get()
        self.model.set_front_camera_frame(frame[0])

    def on_timestamp(self, timestamp: float):
        self.model.set_recording_timer_time(timestamp)

    def on_top_camera_config_changed(self, config):
        self.camera_recorder.stop()
        self.camera_recorder.set_top_camera(None)

        camera_source = CameraFactory.create_camera(config)
        self.camera_recorder.set_top_camera(camera_source)
        self.camera_recorder.top_camera.set_video_buffer(self.top_preview_queue)
        self.camera_recorder.start()

        self.start_preview()
        self.check_ready()

    def on_front_camera_config_changed(self, config):
        self.camera_recorder.stop()
        self.camera_recorder.set_front_camera(None)

        camera_source = CameraFactory.create_camera(config)
        self.camera_recorder.set_front_camera(camera_source)
        self.camera_recorder.front_camera.set_video_buffer(self.front_preview_queue)
        self.camera_recorder.start()

        self.start_preview()
        self.check_ready()

    def _find_max_recording_number(self, target_dir: Path):
        max_recording_number = 0
        for file_type_name, file_type in FILE_TYPES.items():
            files = target_dir.glob(file_type.glob_pattern)
            numbers = [int(file.stem.split("_")[-1]) for file in files]
            if numbers:
                max_recording_number = max(max_recording_number, max(numbers))
        return max_recording_number

    def _update_recording_number(self):
        if self.model.video_files_config.target_directory is None:
            self.model.set_recording_number(1)
        else:
            try:
                target_dir = Path(self.model.video_files_config.target_directory)
                max_recording_number = self._find_max_recording_number(target_dir)
                self.model.set_recording_number(max_recording_number + 1)
            except Exception as e:
                self.model.set_recording_number(1)
                self.model.set_recording_not_ready(f"Error reading target directory: {e}")
                return

    def on_video_files_config_changed(self):
        self._update_recording_number()
        self.check_ready()

    def on_grimace_config_changed(self, config: GrimaceConfig):
        self.model.set_recording_not_ready("Initializing Grimace Analyzer...")

        gab = GrimaceAnalyzerBuilder()
        gab.set_model_version(config.grimace_model)
        gab.set_devices(config.frame_quality_device, config.face_cropper_device, config.grimace_scoring_device)

        self.front_video_pipeline_builder.set_frame_quality_scorer(gab.build_frame_quality_scorer())
        self.front_video_pipeline_builder.set_face_cropper(gab.build_face_cropper())
        self.front_video_pipeline_builder.set_grimace_scorer(gab.build_grimace_scorer())

        self.check_ready()

    def on_pose_config_changed(self, config: PoseTopConfig):
        self.model.set_recording_not_ready("Initializing Pose Estimator...")

        peb = PoseEstimatorBuilder()
        peb.set_model_version(config.pose_model)
        peb.set_device(config.pose_device)

        self.top_video_pipeline_builder.set_pose_estimator_model(peb.build_pose_estimator_model())
        self.top_video_pipeline_builder.set_top_pose_keypoints(peb.get_pose_keypoints())
        self.top_video_pipeline_builder.set_pose_preview_enabled(config.show_preview)

        self.start_preview()
        self.check_ready()

    def on_recording_state_changed(self, recording_state: str):
        if recording_state == "starting":
            self.start_recording()
        elif recording_state == "stopping":
            self.stop_recording()

    def start_preview(self):
        self.stop()

        top_camera_source = CameraFactory.create_camera(self.model.top_camera_config)
        front_camera_source = CameraFactory.create_camera(self.model.front_camera_config)

        if top_camera_source is not None:
            self.top_video_pipeline = self.top_video_pipeline_builder.build(preview=True)
            self.camera_recorder.set_top_camera(top_camera_source)
            self.camera_recorder.top_camera.set_video_buffer(self.top_video_pipeline.input_queue)
            self.top_video_pipeline.start()

        if front_camera_source is not None:
            self.front_video_pipeline = self.front_video_pipeline_builder.build(preview=True)
            self.camera_recorder.set_front_camera(front_camera_source)
            self.camera_recorder.front_camera.set_video_buffer(self.front_video_pipeline.input_queue)
            self.front_video_pipeline.start()

        if top_camera_source is not None or front_camera_source is not None:
            self.camera_recorder.start()

    def stop(self):
        print("Stopping...")

        self.camera_recorder.stop()
        self.camera_recorder.wait()

        if self.top_video_pipeline is not None:
            self.top_video_pipeline.wait()
            self.top_video_pipeline = None

        if self.front_video_pipeline is not None:
            self.front_video_pipeline.wait()
            self.front_video_pipeline = None

        print("Stopped!")

        self.camera_recorder.set_top_camera(None)
        self.camera_recorder.set_front_camera(None)

    def prepare_recording(self, top_camera_source, front_camera_source):
        recording_name = self.model.recording_name
        target_directory = Path(self.model.video_files_config.target_directory)
        recording_number = self.model.recording_number

        prefix = recording_name + "_" if recording_name is not None else ""

        file_builder = FileBuilder(prefix, recording_number)

        top_video_filename = file_builder.build("top_video")
        front_video_filename = file_builder.build("front_video")
        top_timestamp_filename = file_builder.build("top_timestamps")
        front_timestamp_filename = file_builder.build("front_timestamps")
        grimace_results_filename = file_builder.build("grimace_results")
        pose_estimation_results_filename = file_builder.build("top_pose_estimation_results")

        top_video_file = Path(target_directory) / top_video_filename
        front_video_file = Path(target_directory) / front_video_filename
        top_timestamp_file = Path(target_directory) / top_timestamp_filename
        front_timestamp_file = Path(target_directory) / front_timestamp_filename
        grimace_results_file = Path(target_directory) / grimace_results_filename
        pose_estimation_results_file = Path(target_directory) / pose_estimation_results_filename

        fourcc = cv2.VideoWriter.fourcc(*self.model.recording_config.codec)
        frames_per_interval = round(self.model.grimace_config.frame_interval * front_camera_source.get_fps())
        self.front_video_pipeline_builder.set_frames_per_interval(frames_per_interval)

        top_vwb = VideoWriterBuilder()
        top_vwb.set_video_file(top_video_file)
        top_vwb.set_timestamp_file(top_timestamp_file)
        top_vwb.set_fourcc(fourcc)
        top_vwb.set_width(top_camera_source.get_width())
        top_vwb.set_height(top_camera_source.get_height())
        top_vwb.set_fps(top_camera_source.get_fps())

        self.top_video_pipeline_builder.set_video_writer(top_vwb.build())
        self.top_video_pipeline_builder.set_pose_results_file(pose_estimation_results_file)
        self.top_video_pipeline_builder.set_target_frame_rate(front_camera_source.get_fps())

        front_vwb = VideoWriterBuilder()
        front_vwb.set_video_file(front_video_file)
        front_vwb.set_timestamp_file(front_timestamp_file)
        front_vwb.set_fourcc(fourcc)
        front_vwb.set_width(front_camera_source.get_width())
        front_vwb.set_height(front_camera_source.get_height())
        front_vwb.set_fps(front_camera_source.get_fps())

        self.front_video_pipeline_builder.set_video_writer(front_vwb.build())
        self.front_video_pipeline_builder.set_grimace_results_file(grimace_results_file)

    def start_recording(self):
        self.stop()

        top_camera_source = CameraFactory.create_camera(self.model.top_camera_config)
        front_camera_source = CameraFactory.create_camera(self.model.front_camera_config)

        if top_camera_source is None or front_camera_source is None:
            raise ValueError("Both cameras must be set to start recording")

        self.prepare_recording(top_camera_source, front_camera_source)

        self.top_video_pipeline = self.top_video_pipeline_builder.build()
        recording_duration = self.model.recording_config.duration if self.model.recording_config.mode == "Timed" else None
        self.recording_timer = RecordingTimer(self.top_video_pipeline.input_queue, recording_duration)
        self.recording_timer.time_signal.connect(self.on_timestamp)
        self.recording_timer.stop_signal.connect(self.model.set_recording_stopping)

        self.camera_recorder.set_top_camera(top_camera_source)
        self.camera_recorder.top_camera.set_video_buffer(self.recording_timer)
        self.top_video_pipeline.start()

        self.front_video_pipeline = self.front_video_pipeline_builder.build()
        self.camera_recorder.set_front_camera(front_camera_source)
        self.camera_recorder.front_camera.set_video_buffer(self.front_video_pipeline.input_queue)
        self.front_video_pipeline.start()

        self.recording_timer.start()
        self.camera_recorder.start()

        self.model.set_recording_running()

    def stop_recording(self):
        self.stop()
        self.model.set_recording_name(None)
        self._update_recording_number()
        self.start_preview()
        self.check_ready()

    def is_ready(self) -> str | None:
        if self.camera_recorder.top_camera is None:
            return "Top camera not properly configured"
        if self.camera_recorder.front_camera is None:
            return "Front camera not properly configured"
        if self.model.video_files_config.target_directory is None:
            return "Target directory not selected"

    def check_ready(self):
        reason = self.is_ready()
        if reason is None:
            self.model.set_recording_ready()
        else:
            self.model.set_recording_not_ready(reason)

    def on_config_changed(self):
        if self.model.recording_state in ["ready", "not_ready"]:
            self.check_ready()
