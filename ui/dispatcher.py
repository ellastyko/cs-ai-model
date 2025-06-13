from PyQt5.QtCore import QObject, pyqtSignal

class EventDispatcher(QObject):
    # Location preview
    title_changed = pyqtSignal(str)
    image_changed = pyqtSignal(str)

    # GL
    map_changed   = pyqtSignal(str)
    map_mode      = pyqtSignal(str)

# Глобальный синглтон
dispatcher = EventDispatcher()
