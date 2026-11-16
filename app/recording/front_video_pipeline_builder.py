import logging
from pathlib import Path
from typing import Optional

from app.analysis.grimace_analyzer_v1 import GrimaceAnalyzerV1
from app.analysis.grimace_results_writer import GrimaceResultWriter
from app.dataflow.qqueue import IQueue, QQueue
from app.dataflow.queue_forker import QueueForker
from app.recording.video_pipeline import VideoPipeline
from app.recording.video_writer import BufferVideoWriter
from grimace.frame_cropper import FrameCropper
from grimace.frame_quality_scorer import FrameQualityScorer
from grimace.grimace_scorer import GrimaceScorer
from util.trace import Trace

logger = logging.getLogger("grimace_box."+__name__)


class FrontVideoPipelineBuilder:
    @Trace.trace(logger)
    def __init__(self):
        self.preview_queue: IQueue | None = None
        self.results_preview_queue: IQueue | None = None

        self.video_writer: BufferVideoWriter | None = None

        self.frame_quality_scorer: FrameQualityScorer | None = None
        self.face_cropper: FrameCropper | None = None
        self.grimace_scorer: GrimaceScorer | None = None

        self.frames_per_interval: int | None = None

        self.grimace_results_file: Path | None = None

    @Trace.trace(logger)
    def set_preview_queue(self, preview_queue: IQueue) -> 'FrontVideoPipelineBuilder':
        self.preview_queue = preview_queue
        return self

    @Trace.trace(logger)
    def set_results_preview_queue(self, results_preview_queue: IQueue) -> 'FrontVideoPipelineBuilder':
        self.results_preview_queue = results_preview_queue
        return self

    @Trace.trace(logger)
    def set_video_writer(self, video_writer: BufferVideoWriter) -> 'FrontVideoPipelineBuilder':
        self.video_writer = video_writer
        return self

    # TODO: These may change with different model versions, so it might be better to pass the entire analyzer object
    @Trace.trace(logger)
    def set_frame_quality_scorer(self, frame_quality_scorer: FrameQualityScorer) -> 'FrontVideoPipelineBuilder':
        self.frame_quality_scorer = frame_quality_scorer
        return self

    @Trace.trace(logger)
    def set_face_cropper(self, face_cropper: FrameCropper) -> 'FrontVideoPipelineBuilder':
        self.face_cropper = face_cropper
        return self

    @Trace.trace(logger)
    def set_grimace_scorer(self, grimace_scorer: GrimaceScorer) -> 'FrontVideoPipelineBuilder':
        self.grimace_scorer = grimace_scorer
        return self

    @Trace.trace(logger)
    def set_frames_per_interval(self, frames_per_interval: int) -> 'FrontVideoPipelineBuilder':
        self.frames_per_interval = frames_per_interval
        return self

    @Trace.trace(logger)
    def set_grimace_results_file(self, grimace_results_file: Path) -> 'FrontVideoPipelineBuilder':
        self.grimace_results_file = grimace_results_file
        return self

    @Trace.trace(logger)
    def build_grimace_analyzer_service(self, output_queue: IQueue) -> GrimaceAnalyzerV1:
        if self.frame_quality_scorer is None:
            raise ValueError("frame_quality_scorer is not set")
        if self.face_cropper is None:
            raise ValueError("face_cropper is not set")
        if self.grimace_scorer is None:
            raise ValueError("grimace_scorer is not set")
        if self.frames_per_interval is None:
            raise ValueError("frames_per_interval is not set")
        if self.results_preview_queue is None:
            raise ValueError("results_preview_queue is not set")

        # TODO: add results preview queue and make it configurable
        return GrimaceAnalyzerV1(self.frame_quality_scorer, self.face_cropper, self.grimace_scorer,
                                 1000, output_queue, self.results_preview_queue, batch_size=16, min_score=4.25 / 6,
                                 frames_per_interval=self.frames_per_interval)

    @Trace.trace(logger)
    def build_grimace_results_writer(self) -> GrimaceResultWriter:
        if self.grimace_results_file is None:
            raise ValueError("grimace_results_file is not set")

        return GrimaceResultWriter(self.grimace_results_file, 1000)

    @Trace.trace(logger)
    def build(self, preview: bool = False) -> VideoPipeline:
        if self.preview_queue is None:
            raise ValueError("preview_queue is not set")

        if preview:
            return VideoPipeline([], [], self.preview_queue)

        if self.video_writer is None:
            raise ValueError("video_writer is not set")

        core_services = []
        analysis_services = []

        core_services.append(self.video_writer)

        grimace_results_writer = self.build_grimace_results_writer()
        analysis_services.append(grimace_results_writer)

        grimace_output_queue = QueueForker([grimace_results_writer.queue])

        grimace_scorer_service = self.build_grimace_analyzer_service(grimace_output_queue)
        analysis_services.append(grimace_scorer_service)

        camera_queue = QueueForker([self.video_writer.queue, grimace_scorer_service.queue, self.preview_queue])

        return VideoPipeline(core_services, analysis_services, camera_queue)

    @Trace.trace(logger)
    def get_not_ready_reason(self) -> Optional[str]:
        if self.preview_queue is None:
            return "Preview queue not properly configured"

        # Video writer is not checked because it requires the camera source,
        # which is only built when starting the recording

        # Same for frames_per_interval

        if self.frame_quality_scorer is None:
            return "frame_quality_scorer is not set"
        if self.face_cropper is None:
            return "face_cropper is not set"
        if self.grimace_scorer is None:
            return "grimace_scorer is not set"
        if self.grimace_results_file is None:
            return "grimace_results_file is not set"

        return None
