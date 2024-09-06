from typing import TypeVar, List

from app.dataflow.qqueue import IQueue

T = TypeVar('T')


class QueueForker(IQueue):
    def __init__(self, queues: List[IQueue]):
        self.queues = queues

    def enqueue(self, item):
        for queue in self.queues:
            queue.enqueue(item)

    def close(self):
        for queue in self.queues:
            queue.close()
