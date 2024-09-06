from PySide6.QtCore import QObject, Signal

from app.dataflow.qqueue import IQueue


class QListMeta(type(QObject), type(IQueue)):
    pass


class QList(QObject, IQueue, metaclass=QListMeta):
    """
    A thread-safe list with signals for changes
    """

    list_changed = Signal()
    list_cleared = Signal()

    def __init__(self):
        super(QList, self).__init__()
        self.items = []

    def enqueue(self, item):
        self.items.append(item)
        self.list_changed.emit()

    def remove(self, item):
        self.items.remove(item)
        self.list_changed.emit()

    def clear(self):
        self.items.clear()
        self.list_cleared.emit()
        self.list_changed.emit()

    def close(self):
        # TODO: Does this need to do anything?
        pass
