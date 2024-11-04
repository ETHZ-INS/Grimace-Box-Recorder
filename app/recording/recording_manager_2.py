import logging
import time
from pathlib import Path

import cv2
from PySide6.QtCore import QObject, QThread

from app.config.camera import CameraConfig
from app.config.grimace import GrimaceConfig
from app.config.pose_top import PoseTopConfig
from app.config.recording import RecordingConfig
from app.config.video_files import VideoFilesConfig
from app.dataflow.qvariable import QVariable
from app.model.files import FILE_TYPES, FileBuilder
from app.model.grimace_recorder_model import GrimaceRecorderModel, RecordingState, ApplicationState
from app.recording.camera_recorder.camera_factory import CameraFactory
from app.recording.camera_recorder.dual_camera_recorder import DualCameraRecorder
from app.recording.front_video_pipeline_builder import FrontVideoPipelineBuilder
from app.recording.grimace_analysis_builder import GrimaceAnalyzerBuilder
from app.recording.pose_estimator_builder import PoseEstimatorBuilder
from app.recording.recording_timer import RecordingTimer
from app.recording.top_video_pipeline_builder import TopVideoPipelineBuilder
from app.recording.video_writer_builder import VideoWriterBuilder
from util.trace import Trace

logger = logging.getLogger("grimace_box."+__name__)


class RecordingManager(QObject):
    @Trace.trace(logger)
    def __init__(self, model: GrimaceRecorderModel):
        super(RecordingManager, self).__init__()

        self.model = model

        self.camera_recorder = DualCameraRecorder()
        self.camera_recorder.top_error_signal.connect(self.model.recording.set_top_camera_error)
        self.camera_recorder.front_error_signal.connect(self.model.recording.set_front_camera_error)

        self.top_video_pipeline_builder = TopVideoPipelineBuilder()
        self.front_video_pipeline_builder = FrontVideoPipelineBuilder()

        self.model.recording.recording_state_signal.connect(self.on_recording_state_changed)

        self.model.recording.top_camera_config_signal.connect(self.on_top_camera_config_changed)
        self.model.recording.front_camera_config_signal.connect(self.on_front_camera_config_changed)

        self.model.recording.recording_config_signal.connect(self.on_recording_config_changed)
        self.model.recording.video_files_config_signal.connect(self.on_video_files_config_changed)
        self.model.recording.grimace_config_signal.connect(self.on_grimace_config_changed)
        self.model.recording.pose_config_signal.connect(self.on_pose_config_changed)

        self.model.recording.all_configs_signal.connect(self.on_all_config_changed)

        self.model.recording.top_camera_error_signal.connect(self.on_camera_error)
        self.model.recording.front_camera_error_signal.connect(self.on_camera_error)

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
        self.front_video_pipeline_builder.set_results_preview_queue(self.model.recording.grimace_results)

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
        self.model.recording.set_recording_timer_time(timestamp)

    @Trace.trace(logger)
    def apply_top_camera_config(self, config: CameraConfig):
        self.camera_recorder.stop()
        self.camera_recorder.set_top_camera(None)

        try:
            camera_source = CameraFactory.create_camera(config)
        except Exception as e:
            self.model.recording.set_top_camera_error(str(e))
            camera_source = None

        self.camera_recorder.set_top_camera(camera_source)

    @Trace.trace(logger)
    def apply_front_camera_config(self, config: CameraConfig):
        self.camera_recorder.stop()
        self.camera_recorder.set_front_camera(None)

        try:
            camera_source = CameraFactory.create_camera(config)
        except Exception as e:
            self.model.recording.set_front_camera_error(str(e))
            camera_source = None

        self.camera_recorder.set_front_camera(camera_source)

    @Trace.trace(logger)
    def _find_max_recording_number(self, target_dir: Path):
        max_recording_number = 0
        for file_type_name, file_type in FILE_TYPES.items():
            files = target_dir.glob(file_type.glob_pattern)
            numbers = [int(file.stem.split("_")[-1]) for file in files]
            if numbers:
                max_recording_number = max(max_recording_number, max(numbers))
        return max_recording_number

    @Trace.trace(logger)
    def _update_recording_number(self):
        if self.model.recording.video_files_config.target_directory is None:
            self.model.recording.set_recording_number(1)
        else:
            try:
                target_dir = Path(self.model.recording.video_files_config.target_directory)
                max_recording_number = self._find_max_recording_number(target_dir)
                self.model.recording.set_recording_number(max_recording_number + 1)
            except Exception as e:
                self.model.recording.set_recording_number(1)
                self.model.recording.set_recording_not_ready(f"Error reading target directory: {e}")
                return

    @Trace.trace(logger)
    def apply_video_files_config(self, config: VideoFilesConfig):
        self._update_recording_number()

    @Trace.trace(logger)
    def apply_recording_config(self, config: RecordingConfig):
        pass

    @Trace.trace(logger)
    def apply_grimace_config(self, config: GrimaceConfig):
        gab = GrimaceAnalyzerBuilder()
        gab.set_model_version(config.grimace_model)
        gab.set_devices(config.frame_quality_device, config.face_cropper_device, config.grimace_scoring_device)

        self.front_video_pipeline_builder.set_frame_quality_scorer(gab.build_frame_quality_scorer())
        self.front_video_pipeline_builder.set_face_cropper(gab.build_face_cropper())
        self.front_video_pipeline_builder.set_grimace_scorer(gab.build_grimace_scorer())

    @Trace.trace(logger)
    def apply_pose_config(self, config: PoseTopConfig):
        peb = PoseEstimatorBuilder()
        peb.set_model_version(config.pose_model)
        peb.set_device(config.pose_device)

        self.top_video_pipeline_builder.set_pose_estimator_model(peb.build_pose_estimator_model())
        self.top_video_pipeline_builder.set_top_pose_keypoints(peb.get_pose_keypoints())
        self.top_video_pipeline_builder.set_pose_preview_enabled(config.show_preview)

    @Trace.trace(logger)
    def on_top_camera_config_changed(self, config: CameraConfig):
        self.model.recording.set_recording_changing_config("Applying Camera Config...")
        self.apply_top_camera_config(config)
        self.model.recording.config_applied_signal.emit()
        self.model.recording.set_recording_idle()

    @Trace.trace(logger)
    def on_front_camera_config_changed(self, config: CameraConfig):
        self.model.recording.set_recording_changing_config("Applying Camera Config...")
        self.apply_front_camera_config(config)
        self.model.recording.config_applied_signal.emit()
        self.model.recording.set_recording_idle()

    @Trace.trace(logger)
    def on_recording_config_changed(self, config: RecordingConfig):
        self.model.recording.set_recording_changing_config("Applying Recording Config...")
        self.apply_recording_config(config)
        self.model.recording.config_applied_signal.emit()
        self.model.recording.set_recording_idle()

    @Trace.trace(logger)
    def on_video_files_config_changed(self, config: VideoFilesConfig):
        self.model.recording.set_recording_changing_config("Applying Video Files Config...")
        self.apply_video_files_config(config)
        self.model.recording.config_applied_signal.emit()
        self.model.recording.set_recording_idle()

    @Trace.trace(logger)
    def on_grimace_config_changed(self, config: GrimaceConfig):
        self.model.recording.set_recording_changing_config("Initializing Grimace Analyzer...")
        self.apply_grimace_config(config)
        self.model.recording.config_applied_signal.emit()
        self.model.recording.set_recording_idle()

    @Trace.trace(logger)
    def on_pose_config_changed(self, config: PoseTopConfig):
        self.model.recording.set_recording_changing_config("Initializing Pose Estimator...")
        self.apply_pose_config(config)
        self.model.recording.config_applied_signal.emit()
        self.model.recording.set_recording_idle()

    @Trace.trace(logger)
    def on_all_config_changed(self, top_camera_config: CameraConfig, front_camera_config: CameraConfig,
                              recording_config: RecordingConfig, video_files_config: VideoFilesConfig,
                              grimace_config: GrimaceConfig, pose_config: PoseTopConfig):
        self.model.recording.set_recording_changing_config("Applying all configurations...")
        self.apply_top_camera_config(top_camera_config)
        self.apply_front_camera_config(front_camera_config)
        self.apply_recording_config(recording_config)
        self.apply_video_files_config(video_files_config)
        self.apply_grimace_config(grimace_config)
        self.apply_pose_config(pose_config)
        self.model.recording.config_applied_signal.emit()
        self.model.recording.set_recording_idle()

    @Trace.trace(logger)
    def on_recording_state_changed(self, recording_state: str, *_):
        if recording_state == RecordingState.STARTING:
            self.start_recording()
        elif recording_state == RecordingState.STOPPING:
            self.stop_recording()
        elif recording_state == RecordingState.IDLE:
            if self.model.application_state == ApplicationState.CLOSING:
                return
            self.model.recording.set_recording_changing_config("Starting preview...")
            self.start_preview()
            #self.model.recording.config_applied_signal.emit()
            self.check_ready()

    @Trace.trace(logger)
    def start_preview(self):
        self.stop()

        self.camera_recorder.set_top_camera(None)
        self.camera_recorder.set_front_camera(None)

        try:
            top_camera_source = CameraFactory.create_camera(self.model.recording.top_camera_config)
        except Exception as e:
            if self.model.recording.top_camera_error is None:
                self.model.recording.set_top_camera_error(str(e))
            top_camera_source = None

        try:
            front_camera_source = CameraFactory.create_camera(self.model.recording.front_camera_config)
        except Exception as e:
            if self.model.recording.front_camera_error is None:
                self.model.recording.set_front_camera_error(str(e))
            front_camera_source = None

        if top_camera_source is not None:
            self.top_video_pipeline_builder.set_target_frame_rate(top_camera_source.get_fps())
            self.top_video_pipeline = self.top_video_pipeline_builder.build(preview=True)
            self.camera_recorder.set_top_camera(top_camera_source)
            self.camera_recorder.top_camera.set_video_buffer(self.top_video_pipeline.input_queue)
            self.top_video_pipeline.start()
            self.model.recording.set_top_camera_error(None)

        if front_camera_source is not None:
            self.front_video_pipeline = self.front_video_pipeline_builder.build(preview=True)
            self.camera_recorder.set_front_camera(front_camera_source)
            self.camera_recorder.front_camera.set_video_buffer(self.front_video_pipeline.input_queue)
            self.front_video_pipeline.start()
            self.model.recording.set_front_camera_error(None)

        if top_camera_source is not None or front_camera_source is not None:
            self.camera_recorder.start()

    @Trace.trace(logger)
    def stop(self):
        self.camera_recorder.stop()
        self.camera_recorder.wait()

        if self.top_video_pipeline is not None:
            self.top_video_pipeline.wait()
            self.top_video_pipeline = None

        if self.front_video_pipeline is not None:
            self.front_video_pipeline.wait()
            self.front_video_pipeline = None

        # TODO: This is a hack to prevent the camera from being closed and reopened when starting the recording
        #  There should be a better way to do this
        #self.camera_recorder.set_top_camera(None)
        #self.camera_recorder.set_front_camera(None)

    @Trace.trace(logger)
    def prepare_recording(self, top_camera_source, front_camera_source):
        recording_name = self.model.recording.recording_name
        target_directory = Path(self.model.recording.video_files_config.target_directory)
        recording_number = self.model.recording.recording_number

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

        fourcc = cv2.VideoWriter.fourcc(*self.model.recording.recording_config.codec)
        frames_per_interval = round(self.model.recording.grimace_config.frame_interval * front_camera_source.get_fps())
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

        front_vwb = VideoWriterBuilder()
        front_vwb.set_video_file(front_video_file)
        front_vwb.set_timestamp_file(front_timestamp_file)
        front_vwb.set_fourcc(fourcc)
        front_vwb.set_width(front_camera_source.get_width())
        front_vwb.set_height(front_camera_source.get_height())
        front_vwb.set_fps(front_camera_source.get_fps())

        self.front_video_pipeline_builder.set_video_writer(front_vwb.build())
        self.front_video_pipeline_builder.set_grimace_results_file(grimace_results_file)

    @Trace.trace(logger)
    def start_recording(self):
        self.stop()

        #top_camera_source = CameraFactory.create_camera(self.model.recording.top_camera_config)
        #front_camera_source = CameraFactory.create_camera(self.model.recording.front_camera_config)

        #if top_camera_source is None or front_camera_source is None:
        #    raise ValueError("Both cameras must be set to start recording")

        if self.camera_recorder.top_camera is None or self.camera_recorder.front_camera is None:
            raise ValueError("Both cameras must be set to start recording")

        self.prepare_recording(self.camera_recorder.top_camera.source, self.camera_recorder.front_camera.source)

        self.top_video_pipeline_builder.set_target_frame_rate(self.camera_recorder.top_camera.source.get_fps())
        self.top_video_pipeline = self.top_video_pipeline_builder.build()
        recording_duration = self.model.recording.recording_config.duration if self.model.recording.recording_config.mode == "Timed" else None
        self.recording_timer = RecordingTimer(self.top_video_pipeline.input_queue, recording_duration)
        self.recording_timer.time_signal.connect(self.on_timestamp)
        self.recording_timer.stop_signal.connect(self.model.recording.set_recording_stopping)

        self.front_video_pipeline = self.front_video_pipeline_builder.build()

        self.camera_recorder.top_camera.set_video_buffer(self.recording_timer)
        self.camera_recorder.front_camera.set_video_buffer(self.front_video_pipeline.input_queue)

        self.top_video_pipeline.core_error_signal.connect(self.on_recording_error)
        self.front_video_pipeline.core_error_signal.connect(self.on_recording_error)

        self.top_video_pipeline.analysis_error_signal.connect(self.on_recording_error)
        self.front_video_pipeline.analysis_error_signal.connect(self.on_recording_error)

        self.top_video_pipeline.start()
        self.front_video_pipeline.start()

        self.recording_timer.start()
        self.camera_recorder.start()

        self.model.recording.set_recording_running()

    @Trace.trace(logger)
    def stop_recording(self):
        self.stop()
        self.model.recording.set_recording_name(None)
        self._update_recording_number()
        self.model.recording.set_recording_idle()

    @Trace.trace(logger)
    def is_ready(self) -> str | None:
        if self.camera_recorder.top_camera is None:
            return "Top camera not properly configured"
        if self.camera_recorder.front_camera is None:
            return "Front camera not properly configured"
        if self.model.recording.video_files_config.target_directory is None:
            return "Target directory not selected"

    @Trace.trace(logger)
    def check_ready(self):
        reason = self.is_ready()
        if reason is None:
            self.model.recording.set_recording_ready()
        else:
            self.model.recording.set_recording_not_ready(reason)

    @Trace.trace(logger, level=logging.WARNING)
    def recording_error(self, error: str):
        self.model.recording.set_recording_error(error)
        self.model.recording.set_recording_stopping()

    @Trace.trace(logger, level=logging.WARNING)
    def on_camera_error(self, error: str):
        if error is None:
            return

        if self.model.recording.recording_state == RecordingState.STARTING or self.model.recording.recording_state == RecordingState.RECORDING:
            self.recording_error(error)
        else:
            self.stop()
            self.model.recording.set_recording_idle()

    @Trace.trace(logger, level=logging.WARNING)
    def on_recording_error(self, error: str):
        if error is None:
            return

        self.recording_error(error)
