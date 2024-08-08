import time

from PySide6.QtCore import QThread, Signal

from app.dataflow.qqueue import QQueue


class QueueReader(QThread):
    error_signal = Signal(str)

    def __init__(self, queue: QQueue, wait_time: float = 0.01, raise_if_full: bool = False):
        super(QueueReader, self).__init__()

        self.queue = queue
        self.wait_time = wait_time
        self.raise_if_full = raise_if_full

        self.running = False
        self.error = None

    def setup(self):
        pass

    def process_item(self, item):
        pass

    def then(self):
        pass

    def close(self):
        pass

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
            self.then()
        except Exception as e:
            self.error = str(e)
            self.error_signal.emit(self.error)
            raise e
        finally:
            self.close()
            self.running = False

    def stop(self):
        self.running = False
