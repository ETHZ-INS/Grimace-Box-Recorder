from app.dataflow.qqueue import QQueue, IQueue
from app.process.queue_process import QueueProcess


class QueuePacer(QueueProcess):
    def __init__(self, queue_size: int, output_queue: IQueue, rate: float):
        # TODO: find a better way to do pacing
        super().__init__(queue_size, wait_time=1/rate*0.95-0.005, catch_up=False)
        self.output_queue = output_queue
        self.rate = rate

    def process_item(self, item):
        self.output_queue.enqueue(item)

    def finish(self):
        pass

    def close(self):
        pass
