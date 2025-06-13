from PyQt5.QtCore import QObject, pyqtSignal

class EventDispatcher(QObject):

    title_changed = pyqtSignal(str)
    image_changed = pyqtSignal(str)
    map_changed = pyqtSignal(str)

# Глобальный синглтон
dispatcher = EventDispatcher()
