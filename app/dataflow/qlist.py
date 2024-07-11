from PySide6.QtCore import QObject, Signal


class QList(QObject):
    """
    A thread-safe list with signals for changes
    """

    list_changed = Signal()
    list_cleared = Signal()

    def __init__(self):
        super(QList, self).__init__()
        self.items = []

    def append(self, item):
        self.items.append(item)
        self.list_changed.emit()

    def remove(self, item):
        self.items.remove(item)
        self.list_changed.emit()

    def clear(self):
        self.items.clear()
        self.list_cleared.emit()
        self.list_changed.emit()
