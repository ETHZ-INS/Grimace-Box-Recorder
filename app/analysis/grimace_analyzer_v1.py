import cv2
import numpy as np

from app.dataflow.qqueue import QQueue, IQueue
from app.process.queue_process import QueueProcess
from grimace.frame_cropper import FrameCropper
from grimace.frame_quality_scorer import FrameQualityScorer
from grimace.grimace_scorer import GrimaceScorer

import logging

from util.trace import Trace

logger = logging.getLogger("grimace_box."+__name__)


class GrimaceAnalyzerV1(QueueProcess):
    @Trace.trace(logger)
    def __init__(self, frame_quality_scorer: FrameQualityScorer, frame_cropper: FrameCropper,
                 grimace_scorer: GrimaceScorer, queue_size: int,
                 output_buffer: IQueue, results_preview_queue: IQueue,
                 batch_size: int = 16, min_score: float = 4.25 / 6, frames_per_interval: int = 1800):
        super(GrimaceAnalyzerV1, self).__init__(queue_size, wait_time=0.01, raise_if_full=True)

        self.frame_quality_scorer = frame_quality_scorer
        self.frame_cropper = frame_cropper
        self.grimace_scorer = grimace_scorer

        self.output_buffer = output_buffer
        self.results_preview_queue = results_preview_queue

        self.batch_size = batch_size
        self.min_score = min_score
        self.frames_per_interval = frames_per_interval

        self.running_interval_frames = []
        self.running_interval_scores = []
        self.running_batch = []

    @Trace.trace(logger)
    def setup(self):
        self.running_interval_frames = []
        self.running_interval_scores = []
        self.running_batch = []

    def process_batch(self):
        batch_size = min(self.batch_size, len(self.running_batch))

        batch_frames = self.running_batch[:batch_size]
        self.running_batch = self.running_batch[batch_size:]

        batch_frame_images = [frame[0] for frame in batch_frames]

        batch_scores = self.frame_quality_scorer.score_batch(batch_frame_images)
        self.running_interval_frames.extend(batch_frames)
        self.running_interval_scores.extend(batch_scores)

    @Trace.trace(logger)
    def process_interval(self):
        interval_size = min(self.frames_per_interval, len(self.running_interval_frames))

        interval_frames = self.running_interval_frames[:interval_size]
        self.running_interval_frames = self.running_interval_frames[interval_size:]
        interval_scores = self.running_interval_scores[:interval_size]
        self.running_interval_scores = self.running_interval_scores[interval_size:]

        tries = 0
        while True:
            # Try to crop the frame with the highest score until a frame can be cropped.
            # Give up after 50 failed attempts
            max_score = max(interval_scores)

            if max_score < self.min_score or tries >= 50:  # TODO: decide on a good number of tries or make it configurable
                logger.info("No valid frame found in interval")
                if self.results_preview_queue is not None:
                    self.results_preview_queue.enqueue((None, None))
                break

            max_score_index = np.argmax(interval_scores)
            frame, frame_index, timestamp = interval_frames[max_score_index]
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)

            cropped_frame = self.frame_cropper.crop(frame)
            if cropped_frame is None:
                logger.warning("Failed to crop frame with index %s", max_score_index)
                # If the frame could not be cropped, set its score to -1 to prevent it from being selected again
                interval_scores[max_score_index] = -1
            else:
                logger.info("Successfully cropped frame with index %s", max_score_index)
                grimace_scores = self.grimace_scorer.score(cropped_frame)

                if self.results_preview_queue is not None:
                    self.results_preview_queue.enqueue((cropped_frame, grimace_scores))
                self.output_buffer.enqueue((frame_index, timestamp, grimace_scores))
                break
            tries += 1

    def process_item(self, item):
        frame = item
        self.running_batch.append(frame)

        #if random.random() < 0.01:
        #    raise Exception("Bad luck in GrimaceAnalyzer")

        if len(self.running_batch) < self.batch_size:
            return

        self.process_batch()

        if len(self.running_interval_frames) < self.frames_per_interval:
            return

        self.process_interval()

    @Trace.trace(logger)
    def finish(self):
        if len(self.running_batch) > 0:
            self.process_batch()

        # Process remaining frames in the interval if the interval is filled at least 90%
        if len(self.running_interval_frames) > self.frames_per_interval * 0.9:
            self.process_interval()

    @Trace.trace(logger)
    def close(self):
        self.output_buffer.close()

    def check_health(self, *args, prefix: str = "", fill_threshold: float = 0.1, **kwargs) -> dict:
        report = {"warnings": {}}

        queue_fill_level = self.queue.get_fill_level()
        report[prefix+"grimace_analysis_queue_fill_level"] = queue_fill_level

        warning = None
        if queue_fill_level > fill_threshold:
            warning = f"Grimace analysis queue fill level: {queue_fill_level * 100:.2f}%"
        report["warnings"][prefix+"grimace_analysis_queue_fill"] = warning

        return report
