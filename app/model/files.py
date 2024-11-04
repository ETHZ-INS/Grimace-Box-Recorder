import logging
from dataclasses import dataclass

from util.trace import Trace

logger = logging.getLogger("grimace_box."+__name__)


@dataclass(frozen=True)
class FileType:
    template: str
    glob_pattern: str


FILE_TYPES = {
    "top_video": FileType("{prefix}top_{recording_number}.avi", "*top_*.avi"),
    "front_video": FileType("{prefix}front_{recording_number}.avi", "*front_*.avi"),
    "top_timestamps": FileType("{prefix}top_{recording_number}.csv", "*top_*.csv"),
    "front_timestamps": FileType("{prefix}front_{recording_number}.csv", "*front_*.csv"),
    "top_pose_estimation_results": FileType("{prefix}top_pose_estimation_{recording_number}.csv", "*top_pose_estimation_*.csv"),
    "front_pose_estimation_results": FileType("{prefix}front_pose_estimation_{recording_number}.csv", "*front_pose_estimation_*.csv"),
    "grimace_results": FileType("{prefix}grimace_analysis_{recording_number}.csv", "*grimace_analysis_*.csv"),
}


class FileBuilder:
    def __init__(self, prefix: str, recording_number: int):
        self.prefix = prefix
        self.recording_number = recording_number

    @Trace.trace(logger)
    def build(self, file_type_name: str) -> str:
        file_type = FILE_TYPES.get(file_type_name)
        if file_type is None:
            raise ValueError(f"Unknown file type: {file_type_name}")

        return file_type.template.format(prefix=self.prefix, recording_number=self.recording_number)
