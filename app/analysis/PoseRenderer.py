import cv2

from app.dataflow.qqueue import IQueue


class PoseRenderer(IQueue):
    def __init__(self, output_queue: IQueue):
        self.output_queue = output_queue

    def enqueue(self, item):
        frame, frame_number, timestamp, instance = item

        if instance is not None and instance.pose is not None:
            frame = frame.copy()
            for point in instance.pose:
                if point is not None and point.conf > 0.2:
                    x = int(point.x * frame.shape[1])
                    y = int(point.y * frame.shape[0])
                    cv2.circle(frame, (x, y), 5, (255, 255, 255), -1)

        self.output_queue.enqueue((frame, frame_number, timestamp))

    def close(self):
        self.output_queue.close()
