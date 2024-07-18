import time
from abc import ABC, abstractmethod

from PySide6.QtCore import QThread

from app.dataflow.qqueue import QQueue


class QueueReader(QThread):
    def __init__(self, queue: QQueue, wait_time: float = 0.01):
        super(QueueReader, self).__init__()

        self.queue = queue
        self.wait_time = wait_time

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
        finally:
            self.close()
            self.running = False

    def stop(self):
        self.running = False
