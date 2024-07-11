import csv
import time
from pathlib import Path
from typing import Tuple

import numpy as np
from PySide6.QtCore import QThread

from app.dataflow.qqueue import QQueue


class GrimaceResultWriter(QThread):
    def __init__(self, target_file: Path, grimace_results_buffer: QQueue[Tuple[int, float, np.ndarray]]):
        super(GrimaceResultWriter, self).__init__()

        self.target_file = target_file
        self.grimace_results_buffer = grimace_results_buffer

        self.running = False

    def run(self):
        self.running = True
        with self.target_file.open("w+", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["frame_index", "timestamp", "eye", "nose", "cheek", "ear", "whisker", "average"])

        ended = False
        while self.running or not ended:
            while not self.grimace_results_buffer.is_empty():
                item = self.grimace_results_buffer.dequeue()
                if item is QQueue.End:
                    self.running = False
                    ended = True
                    break

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
            time.sleep(1)

        self.running = False

    def stop(self):
        self.running = False
