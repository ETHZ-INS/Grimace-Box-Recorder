import time
from typing import Tuple

import cv2
import numpy as np
from PySide6.QtCore import QThread

from app.dataflow.qlist import QList
from app.dataflow.qqueue import QQueue
from app.dataflow.queue_reader import QueueReader
from grimace.frame_cropper import FrameCropper
from grimace.frame_quality_scorer import FrameQualityScorer
from grimace.grimace_scorer import GrimaceScorer


class GrimaceAnalyzerV1(QueueReader):
    def __init__(self, frame_quality_scorer: FrameQualityScorer, frame_cropper: FrameCropper,
                 grimace_scorer: GrimaceScorer, input_buffer: QQueue,
                 output_buffer: QQueue[Tuple[int, float, np.ndarray]], output_list: QList,
                 batch_size: int = 16, min_score: float = 3.25 / 6, frames_per_interval: int = 1800):
        super(GrimaceAnalyzerV1, self).__init__(input_buffer, wait_time=0.01)

        self.frame_quality_scorer = frame_quality_scorer
        self.frame_cropper = frame_cropper
        self.grimace_scorer = grimace_scorer

        self.output_buffer = output_buffer
        self.output_list = output_list

        self.batch_size = batch_size
        self.min_score = min_score
        self.frames_per_interval = frames_per_interval

        self.running_interval_frames = []
        self.running_interval_scores = []
        self.running_batch = []

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

    def process_interval(self):
        interval_size = min(self.frames_per_interval, len(self.running_interval_frames))

        interval_frames = self.running_interval_frames[:interval_size]
        self.running_interval_frames = self.running_interval_frames[interval_size:]
        interval_scores = self.running_interval_scores[:interval_size]
        self.running_interval_scores = self.running_interval_scores[interval_size:]

        while True:
            # Try to crop the frame with the highest score until a frame can be cropped
            max_score = max(interval_scores)

            if max_score < self.min_score:
                self.output_list.append((None, None))
                break

            max_score_index = np.argmax(interval_scores)
            frame, frame_index, timestamp = interval_frames[max_score_index]
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)

            cropped_frame = self.frame_cropper.crop(frame)
            if cropped_frame is None:
                # If the frame could not be cropped, set the score to -1 to prevent it from being selected again
                interval_scores[max_score_index] = -1
            else:
                grimace_scores = self.grimace_scorer.score(cropped_frame)

                self.output_list.append((cropped_frame, grimace_scores))
                self.output_buffer.enqueue((frame_index, timestamp, grimace_scores))
                break

    def process_item(self, item):
        frame = item
        self.running_batch.append(frame)

        if len(self.running_batch) < self.batch_size:
            return

        self.process_batch()

        if len(self.running_interval_frames) < self.frames_per_interval:
            return

        self.process_interval()

    def then(self):
        if len(self.running_batch) > 0:
            self.process_batch()

        # Process remaining frames in the interval if the interval is filled at least 90%
        if len(self.running_interval_frames) > self.frames_per_interval * 0.9:
            self.process_interval()

    def close(self):
        self.output_buffer.close()
