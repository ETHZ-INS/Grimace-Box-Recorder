from pathlib import Path
from typing import Optional

import cv2

from app.recording.video_writer import BufferVideoWriter


class VideoWriterBuilder:
    def __init__(self):
        self.video_file: Path | None = None
        self.timestamp_file: Path | None = None

        self.fourcc: int | None = None
        self.width: int | None = None
        self.height: int | None = None
        self.fps: float | None = None

    def set_video_file(self, video_file: Path) -> 'VideoWriterBuilder':
        self.video_file = video_file
        return self

    def set_timestamp_file(self, timestamp_file: Path) -> 'VideoWriterBuilder':
        self.timestamp_file = timestamp_file
        return self

    def set_fourcc(self, fourcc: int) -> 'VideoWriterBuilder':
        self.fourcc = fourcc
        return self

    def set_width(self, width: int) -> 'VideoWriterBuilder':
        self.width = width
        return self

    def set_height(self, height: int) -> 'VideoWriterBuilder':
        self.height = height
        return self

    def set_fps(self, fps: float) -> 'VideoWriterBuilder':
        self.fps = fps
        return self

    def build(self) -> BufferVideoWriter:
        if self.video_file is None:
            raise ValueError("Video file not configured")
        if self.timestamp_file is None:
            raise ValueError("Timestamp file not configured")
        if self.fourcc is None:
            raise ValueError("Video codec not configured")
        if self.width is None:
            raise ValueError("Video width not configured")
        if self.height is None:
            raise ValueError("Video height not configured")
        if self.fps is None:
            raise ValueError("Video FPS not configured")

        video_writer = cv2.VideoWriter(str(self.video_file), self.fourcc, self.fps, (self.width, self.height), isColor=False)
        return BufferVideoWriter(video_writer, 1000, self.timestamp_file)

    def get_not_ready_reason(self) -> Optional[str]:
        if self.video_file is None:
            return "Video file not configured"

        if self.timestamp_file is None:
            return "Timestamp file not configured"

        if self.fourcc is None:
            return "Video codec not configured"

        # Width, height and fps are not checked because they need the camera source,
        # which is only built when starting the recording

        return None
