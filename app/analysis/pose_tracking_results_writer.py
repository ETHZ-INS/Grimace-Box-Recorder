import csv
from pathlib import Path
from typing import Tuple, List

from app.dataflow.qqueue import QQueue
from app.process.queue_process import QueueProcess

import logging

from grimace.pose_model import PoseInstance
from util.trace import Trace

logger = logging.getLogger("grimace_box."+__name__)


class PoseEstimationResultWriter(QueueProcess):
    @Trace.trace(logger)
    def __init__(self, target_file: Path, queue_size: int, bodyparts: List[str]):
        super(PoseEstimationResultWriter, self).__init__(queue_size, wait_time=0.01)

        self.target_file = target_file
        self.bodyparts = bodyparts

        self.target_file_handler = None
        self.csv_writer = None

        self.running = False

    @Trace.trace(logger)
    def setup(self):
        # The grimace results only come in like every 10 seconds, or even longer,
        # so we just open the file when needed instead of keeping it open the whole time
        self.running = True
        self.target_file_handler = self.target_file.open("w+", newline="")
        self.csv_writer = csv.writer(self.target_file_handler)
        header_row = ["frame_index", "confidence"]
        for bodypart in self.bodyparts:
            header_row.append(bodypart + "_confidence")
            header_row.append(bodypart + "_x")
            header_row.append(bodypart + "_y")
        self.csv_writer.writerow(header_row)

    def process_item(self, item):
        frame, frame_index, timestamp, instance = item

        if instance is None:
            return

        row = [frame_index, instance.conf]
        for point in instance.pose:
            row.append(point.conf)
            row.append(point.x)
            row.append(point.y)
        self.csv_writer.writerow(row)

    @Trace.trace(logger)
    def close(self):
        if self.target_file_handler is not None:
            self.target_file_handler.close()

    def check_health(self, *args, prefix: str = "", fill_threshold: float = 0.1, **kwargs) -> dict:
        report = {"warnings": {}}

        queue_fill_level = self.queue.get_fill_level()
        report[prefix+"pose_estimation_results_writer_queue_fill_level"] = queue_fill_level

        warning = None
        if queue_fill_level > fill_threshold:
            warning = f"Pose estimation results writer queue fill level: {queue_fill_level * 100:.2f}%"
        report["warnings"][prefix+"pose_estimation_results_writer_queue_fill"] = warning

        return report
