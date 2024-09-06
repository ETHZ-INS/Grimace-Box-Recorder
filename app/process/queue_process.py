import time
from typing import Callable

from PySide6.QtCore import QThread, Signal

from app.dataflow.qqueue import QQueue, IQueue
from app.process.process import IProcess


class QueueProcessMeta(type(QThread), type(IProcess)):
    pass


class QueueProcess(QThread, IProcess, metaclass=QueueProcessMeta):
    """
    A process that processes items from a queue. Uses a thread to check the queue for items.
    Processes items until the queue is empty, then waits for a short time before checking again.
    The process ends gracefully when the End object is read from the input queue.
    """
    error_signal = Signal(str)

    def __init__(self, queue_size: int, wait_time: float = 0.01, raise_if_full: bool = False, catch_up: bool = True):
        super(QueueProcess, self).__init__()

        self.queue = QQueue(queue_size)
        self.wait_time = wait_time
        self.raise_if_full = raise_if_full
        # If catch_up is True, the process will process all items in the queue before waiting
        # If False, the process will only process one item then wait
        # This is a work around for the QueuePacer process, which should only process one item at a time
        self.catch_up = catch_up

        self.running = False
        self.error = None

    def setup(self):
        # Override this method to perform setup tasks. Open files, etc.
        pass

    def process_item(self, item):
        # Override this method to define how to process an item from the queue
        pass

    def finish(self):
        # Override this method to perform tasks after the queue is empty.
        # This is mainly used for the grimace analyzer to process the remaining frames in the batch
        pass

    def close(self):
        # Override this method to perform cleanup tasks. Close files, output queues, etc.
        pass

    def wait(self, timeout: int = None):
        return super().wait() if timeout is None else super().wait(timeout)

    def enqueue(self, item):
        self.queue.enqueue(item)

    def process_until_empty(self) -> bool:
        while not self.queue.is_empty():
            if self.raise_if_full and self.queue.get_fill_level() > 0.99:
                raise RuntimeError("Queue is full")

            item = self.queue.dequeue()
            if not self.running:
                return False
            if item is QQueue.End:
                return False

            self.process_item(item)
            if not self.catch_up:
                break
        return True

    def process_until_finished(self):
        while self.running:
            if not self.process_until_empty():
                break
            time.sleep(self.wait_time)

    def run(self):
        self.running = True

        try:
            self.setup()
            self.process_until_finished()
            self.finish()
        except Exception as e:
            self.error = str(e)
            self.error_signal.emit(self.error)
            raise e
        finally:
            self.running = False
            # TODO: Is this safe?
            self.close()

    def stop(self):
        # Close the input queue early and stop the process at the next opportunity
        self.running = False
        self.queue.close()

    def on_error(self, func: Callable):
        self.error_signal.connect(func)
