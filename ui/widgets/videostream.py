from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtGui import QImage, QPixmap
import numpy as np

class VideoGLWidget(QOpenGLWidget):
    def __init__(self):
        super().__init__()
        self.frame = None

    def update_frame(self, frame: np.ndarray):
        self.frame = frame
        self.update()

    def paintGL(self):
        if self.frame is not None:
            h, w, _ = self.frame.shape
            img = QImage(self.frame.data, w, h, QImage.Format_RGB888).rgbSwapped()
            painter = QPainter(self)
            painter.drawImage(0, 0, img)
            painter.end()

    def stop(self):
        self.frame = None