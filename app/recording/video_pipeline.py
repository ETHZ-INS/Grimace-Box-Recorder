import logging
from typing import List

from PySide6.QtCore import Signal, QObject

from app.dataflow.qqueue import IQueue
from app.process.process import IProcess
from util.trace import Trace

logger = logging.getLogger("grimace_box."+__name__)


class VideoPipelineMeta(type(QObject), type(IProcess)):
    pass


class VideoPipeline(QObject, IProcess, metaclass=VideoPipelineMeta):
    core_error_signal = Signal(str)
    analysis_error_signal = Signal(str)

    @Trace.trace(logger)
    def __init__(self, core_processes: List[IProcess], analysis_processes: List, input_queue: IQueue):
        super().__init__()

        self.core_processes = core_processes
        self.analysis_processes = analysis_processes
        self.input_queue = input_queue

        for process in self.core_processes:
            process.on_error(self.core_error_signal.emit)
        for process in self.analysis_processes:
            process.on_error(self.analysis_error_signal.emit)

    @Trace.trace(logger)
    def start(self):
        for process in self.core_processes + self.analysis_processes:
            process.start()

    @Trace.trace(logger)
    def stop(self):
        # Stop everything ungracefully. For example in case of error.
        for process in self.core_processes + self.analysis_processes:
            process.stop()

    @Trace.trace(logger)
    def stop_analysis(self):
        # Stop only the analysis processes. If an error occurs in the analysis, the core processes should continue.
        for process in self.analysis_processes:
            process.stop()

    @Trace.trace(logger)
    def wait(self, timeout: int = None) -> bool:
        stopped = True
        for process in self.core_processes + self.analysis_processes:
            stopped &= process.wait(timeout)
        return stopped

    @Trace.trace(logger)
    def wait_analysis(self):
        stopped = True
        for process in self.analysis_processes:
            stopped &= process.wait()
        return stopped

    @Trace.trace(logger, level=logging.WARNING)
    def on_error(self, func):
        self.core_error_signal.connect(func)

    @Trace.trace(logger, level=logging.WARNING)
    def on_analysis_error(self, func):
        self.analysis_error_signal.connect(func)

    def check_health(self, *args, **kwargs) -> dict:
        report = {}
        warnings = {}

        # Merge the health reports from all processes
        for process in self.core_processes + self.analysis_processes:
            process_report = process.check_health(*args, **kwargs)
            warnings.update(process_report["warnings"])
            report.update(process_report)

        report["warnings"] = warnings

        return report
