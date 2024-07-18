import csv
from pathlib import Path
from typing import Tuple

import numpy as np

from app.dataflow.qqueue import QQueue
from app.dataflow.queue_reader import QueueReader


class GrimaceResultWriter(QueueReader):
    def __init__(self, target_file: Path, grimace_results_buffer: QQueue[Tuple[int, float, np.ndarray]]):
        super(GrimaceResultWriter, self).__init__(grimace_results_buffer, wait_time=1)

        self.target_file = target_file

        self.running = False

    def setup(self):
        self.running = True
        with self.target_file.open("w+", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["frame_index", "timestamp", "eye", "nose", "cheek", "ear", "whisker", "average"])

    def process_item(self, item):
        frame_index, timestamp, grimace_scores = item

        grimace_scores = grimace_scores.astype(float)
        grimace_scores[grimace_scores == 3] = np.nan
        avg_score = np.nanmean(grimace_scores)

        nan_indices = np.isnan(grimace_scores)
        grimace_scores = grimace_scores.astype(str)
        grimace_scores[nan_indices] = ""

        with self.target_file.open("a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([frame_index, timestamp, *grimace_scores, avg_score])
