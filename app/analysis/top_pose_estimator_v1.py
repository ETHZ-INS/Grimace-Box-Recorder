import numpy as np

from app.dataflow.qqueue import QQueue, IQueue
from app.process.queue_process import QueueProcess

import logging

from grimace.pose_model import PoseModel
from util.trace import Trace

logger = logging.getLogger("grimace_recorder.app.analysis.top_pose_estimator")


class TopPoseEstimatorV1(QueueProcess):
    @Trace.trace(logger)
    def __init__(self, top_pose_estimator_model: PoseModel, queue_size: int,
                 output_queue: IQueue, batch_size: int = 4):
        super(TopPoseEstimatorV1, self).__init__(queue_size, wait_time=0.01, raise_if_full=True)

        self.top_pose_estimator_model = top_pose_estimator_model

        self.output_queue = output_queue

        self.batch_size = batch_size

        self.running_batch = []

    @Trace.trace(logger)
    def setup(self):
        self.running_batch = []

    def process_batch(self):
        batch_size = min(self.batch_size, len(self.running_batch))

        batch_frames = self.running_batch[:batch_size]
        self.running_batch = self.running_batch[batch_size:]

        batch_frame_images = [np.concatenate([frame[0], frame[0], frame[0]], axis=2) for frame in batch_frames]

        batch_instances = self.top_pose_estimator_model.get_instances(batch_frame_images)

        for frame, instance in zip(batch_frames, batch_instances):
            self.output_queue.enqueue((*frame, instance))

    def process_item(self, item):
        self.running_batch.append(item)

        if len(self.running_batch) < self.batch_size:
            return

        self.process_batch()

    @Trace.trace(logger)
    def finish(self):
        if len(self.running_batch) > 0:
            self.process_batch()

    @Trace.trace(logger)
    def close(self):
        self.output_queue.close()

    def check_health(self, *args, prefix: str = "", fill_threshold: float = 0.1, **kwargs) -> dict:
        report = {"warnings": {}}

        queue_fill_level = self.queue.get_fill_level()
        report[prefix+"pose_estimation_queue_fill_level"] = queue_fill_level

        warning = None
        if queue_fill_level > fill_threshold:
            warning = f"Pose estimation queue fill level: {queue_fill_level * 100:.2f}%"
        report["warnings"][prefix+"pose_estimation_queue_fill"] = warning

        return report
