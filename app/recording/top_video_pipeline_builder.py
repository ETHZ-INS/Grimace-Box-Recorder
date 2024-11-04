import logging
from pathlib import Path
from typing import List, Optional

from app.analysis.PoseRenderer import PoseRenderer
from app.analysis.pose_tracking_results_writer import PoseEstimationResultWriter
from app.analysis.top_pose_estimator_v1 import TopPoseEstimatorV1
from app.dataflow.qqueue import IQueue
from app.dataflow.queue_forker import QueueForker
from app.dataflow.queue_pacer import QueuePacer
from app.recording.FPSRenderer import FPSRenderer
from app.recording.video_pipeline import VideoPipeline
from app.recording.video_writer import BufferVideoWriter
from grimace.pose_model import PoseModel
from util.trace import Trace

logger = logging.getLogger("grimace_box."+__name__)


class TopVideoPipelineBuilder:
    @Trace.trace(logger)
    def __init__(self):
        self.pose_preview_enabled = False

        self.preview_queue: IQueue | None = None

        self.video_writer: BufferVideoWriter | None = None

        self.pose_estimator_model: PoseModel | None = None
        self.pose_results_file: Path | None = None
        self.top_pose_keypoints: List[str] | None = None

        self.target_frame_rate: float | None = None

    @Trace.trace(logger)
    def set_pose_preview_enabled(self, pose_preview_enabled: bool) -> 'TopVideoPipelineBuilder':
        self.pose_preview_enabled = pose_preview_enabled
        return self

    @Trace.trace(logger)
    def set_preview_queue(self, preview_queue: IQueue) -> 'TopVideoPipelineBuilder':
        self.preview_queue = preview_queue
        return self

    @Trace.trace(logger)
    def set_video_writer(self, video_writer: BufferVideoWriter) -> 'TopVideoPipelineBuilder':
        self.video_writer = video_writer
        return self

    @Trace.trace(logger)
    def set_pose_estimator_model(self, pose_estimator_model: PoseModel) -> 'TopVideoPipelineBuilder':
        self.pose_estimator_model = pose_estimator_model
        return self

    @Trace.trace(logger)
    def set_pose_results_file(self, pose_results_file: Path) -> 'TopVideoPipelineBuilder':
        self.pose_results_file = pose_results_file
        return self

    @Trace.trace(logger)
    def set_top_pose_keypoints(self, top_pose_keypoints: List[str]) -> 'TopVideoPipelineBuilder':
        self.top_pose_keypoints = top_pose_keypoints
        return self

    @Trace.trace(logger)
    def set_target_frame_rate(self, target_frame_rate: float) -> 'TopVideoPipelineBuilder':
        self.target_frame_rate = target_frame_rate
        return self

    @Trace.trace(logger)
    def build_pose_results_writer(self) -> PoseEstimationResultWriter:
        if self.pose_results_file is None:
            raise ValueError("pose_results_file is not set")
        if self.top_pose_keypoints is None:
            raise ValueError("top_pose_keypoints is not set")

        return PoseEstimationResultWriter(self.pose_results_file, 1000, self.top_pose_keypoints)

    @Trace.trace(logger)
    def build_pose_estimator(self, output_queue: IQueue, batch_size: int) -> TopPoseEstimatorV1:
        if self.pose_estimator_model is None:
            raise ValueError("pose_estimator_model is not set")

        return TopPoseEstimatorV1(self.pose_estimator_model, 1000, output_queue, batch_size)

    @Trace.trace(logger)
    def build_pacer(self, output_queue: IQueue) -> QueuePacer:
        if self.target_frame_rate is None:
            raise ValueError("target_frame_rate is not set")

        return QueuePacer(1000, output_queue, rate=self.target_frame_rate)

    @Trace.trace(logger)
    def build(self, preview: bool = False) -> VideoPipeline:
        if self.preview_queue is None:
            raise ValueError("preview_queue is not set")

        if preview:
            analysis_services = []
            if self.pose_preview_enabled:
                preview_queue = PoseRenderer(FPSRenderer(self.preview_queue))

                pacer = self.build_pacer(preview_queue)
                analysis_services.append(pacer)

                pose_output_queue = QueueForker([pacer.queue])
                pose_estimator = self.build_pose_estimator(pose_output_queue, batch_size=4)
                analysis_services.append(pose_estimator)

                camera_queue = pose_estimator.queue
            else:
                preview_queue = FPSRenderer(self.preview_queue)
                camera_queue = preview_queue
            return VideoPipeline([], analysis_services, camera_queue)

        if self.video_writer is None:
            raise ValueError("video_writer is not set")

        core_services = []
        analysis_services = []

        core_services.append(self.video_writer)

        pose_results_writer = self.build_pose_results_writer()
        analysis_services.append(pose_results_writer)

        if self.pose_preview_enabled:
            preview_queue = PoseRenderer(FPSRenderer(self.preview_queue))

            pacer = self.build_pacer(preview_queue)
            analysis_services.append(pacer)

            pose_output_queue = QueueForker([pose_results_writer.queue, pacer.queue])
            pose_estimator = self.build_pose_estimator(pose_output_queue, batch_size=4)

            analysis_services.append(pose_estimator)
            camera_queue = QueueForker([self.video_writer.queue, pose_estimator.queue])
        else:
            preview_queue = FPSRenderer(self.preview_queue)

            pose_output_queue = QueueForker([pose_results_writer.queue])

            pose_estimator = self.build_pose_estimator(pose_output_queue, batch_size=4)

            analysis_services.append(pose_estimator)
            camera_queue = QueueForker([self.video_writer.queue, pose_estimator.queue, preview_queue])

        return VideoPipeline(core_services, analysis_services, camera_queue)

    def get_not_ready_reason(self) -> Optional[str]:
        if self.preview_queue is None:
            return "Preview queue not properly configured"

        # Video writer is not checked because it requires the camera source,
        # which is only built when starting the recording

        # Same for the target frame rate

        #if self.pose_enabled and self.pose_preview_enabled:
        #    if self.target_frame_rate is None:
        #        return "Target frame rate not properly configured"

        if self.pose_estimator_model is None:
            return "Pose estimator model not properly configured"
        if self.pose_results_file is None:
            return "Pose results file not properly configured"
        if self.top_pose_keypoints is None:
            return "Top pose keypoints not properly configured"

        return None
