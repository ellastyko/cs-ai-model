from PyQt5.QtCore import QObject, pyqtSignal

class EventDispatcher(QObject):
    # App modes
    GLMAP_MODE       = pyqtSignal(str)
    VIDEOSTREAM_MODE = pyqtSignal(str)
    LIVE_MODE        = pyqtSignal(str)

    # Location preview
    title_changed = pyqtSignal(str)
    image_changed = pyqtSignal(str)

    # GL
    map_changed   = pyqtSignal(str)

# Глобальный синглтон
dispatcher = EventDispatcher()
