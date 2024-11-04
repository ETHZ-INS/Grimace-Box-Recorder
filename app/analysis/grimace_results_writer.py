import csv
from pathlib import Path
from typing import Tuple

import numpy as np

from app.dataflow.qqueue import QQueue
from app.process.queue_process import QueueProcess

import logging

from util.trace import Trace

logger = logging.getLogger("grimace_box."+__name__)


class GrimaceResultWriter(QueueProcess):
    @Trace.trace(logger)
    def __init__(self, target_file: Path, queue_size: int):
        super(GrimaceResultWriter, self).__init__(queue_size, wait_time=1)

        self.target_file = target_file

        self.running = False

    @Trace.trace(logger)
    def setup(self):
        # The grimace results only come in like every 10 seconds, or even longer,
        # so we just open the file when needed instead of keeping it open the whole time
        self.running = True
        with self.target_file.open("w+", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["frame_index", "timestamp", "eye", "nose", "cheek", "ear", "whisker", "average"])

    @Trace.trace(logger)
    def process_item(self, item):
        frame_index, timestamp, grimace_scores = item

        # grimace_scores is a numpy array containing the individual scores for the 5 AUs as integers
        grimace_scores = grimace_scores.astype(float)
        # Grimace score 3 means the AU was unable to be scored, so set it to nan before calculating the mean
        grimace_scores[grimace_scores == 3] = np.nan
        avg_score = np.nanmean(grimace_scores)

        nan_indices = np.isnan(grimace_scores)
        grimace_scores = grimace_scores.astype(str)
        grimace_scores[nan_indices] = ""

        with self.target_file.open("a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([frame_index, timestamp, *grimace_scores, avg_score])

    def check_health(self, *args, prefix: str = "", fill_threshold: float = 0.1, **kwargs) -> dict:
        report = {"warnings": {}}

        queue_fill_level = self.queue.get_fill_level()
        report[prefix+"grimace_results_writer_queue_fill_level"] = queue_fill_level

        warning = None
        if queue_fill_level > fill_threshold:
            warning = f"Grimace results writer queue fill level: {queue_fill_level * 100:.2f}%"
        report["warnings"][prefix+"grimace_results_writer_queue_fill"] = warning

        return report
