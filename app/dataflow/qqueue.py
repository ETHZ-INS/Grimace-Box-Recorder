import threading
from typing import Generic, TypeVar, List, Optional, Union

from PySide6.QtCore import QObject, Signal

T = TypeVar('T')


class QQueue(QObject, Generic[T]):
    """
    A thread-safe queue with a fixed maximum length
    implemented using a circular buffer
    If the queue is full, the oldest element is overwritten
    """

    End = object()

    item_added = Signal()
    item_removed = Signal()

    def __init__(self, size: int, name: str = "Queue"):
        super(QQueue, self).__init__()

        self.size = size
        self.queue = [None] * size
        self.head = 0
        self.tail = 0
        self.full = False
        self.lock = threading.Lock()

        self.name = name

    def enqueue(self, item: Union[T, End]):
        with self.lock:
            self.queue[self.tail] = item
            if self.full:
                self.head = (self.head + 1) % self.size  # move head forward if queue is full
            self.tail = (self.tail + 1) % self.size
            self.full = self.tail == self.head

            if self.tail % 30 == 0:
                fill_level = self._get_fill_level()
                if fill_level > 0.1:
                    print(f"Queue {self.name}: fill level {fill_level*100:.2f}%")

            self.item_added.emit()

    def dequeue(self) -> Union[Optional[T], End]:
        with self.lock:
            if self._is_empty():
                return None  # queue is empty
            item = self.queue[self.head]
            self.queue[self.head] = None
            self.head = (self.head + 1) % self.size
            self.full = False
            self.item_removed.emit()
            return item

    def close(self):
        self.enqueue(self.End)

    def _is_empty(self):
        return not self.full and self.head == self.tail

    def is_empty(self):
        with self.lock:
            return self._is_empty()

    def is_full(self):
        return self.full

    def _get_num_elements(self):
        if self.full:
            return self.size
        return (self.tail - self.head) % self.size

    def get_num_elements(self):
        with self.lock:
            return self._get_num_elements()

    def _get_fill_level(self):
        return self._get_num_elements() / self.size

    def get_fill_level(self):
        with self.lock:
            return self._get_fill_level()
