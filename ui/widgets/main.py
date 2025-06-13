import os
from PyQt5.QtOpenGL import QGLWidget
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QFrame, QStackedLayout
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QObject
from PyQt5.QtGui import QPixmap
from OpenGL.GL import *
from OpenGL.GLU import *
from utils.colors import parse_to_rgba
from location.utils.dataset import parse_filename
from PyQt5.QtWidgets import QPushButton, QLabel
import torch
from PIL import Image
from transformers import ViTImageProcessor
from utils.models import ModelManager
from utils.helpers import open_image, delete_image
from ui.widgets.gl import GLWidget
from ui.widgets.videostream import VideoGLWidget
from ui.widgets.controller import MapControllerWidget

class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.controller = MapControllerWidget(self)
        self.view_stack = QStackedLayout()

        layout.addWidget(self.controller, stretch=1)
        layout.addLayout(self.view_stack, stretch=9)

        self.gl_widget = None
        self.video_widget = None

        # Default view
        self.show_3d_scene()

    def show_3d_scene(self):
        if self.video_widget:
            self.video_widget.stop()
            self.view_stack.removeWidget(self.video_widget)
            self.video_widget.deleteLater()
            self.video_widget = None

        if self.gl_widget is None:
            self.gl_widget = GLWidget()
            self.view_stack.addWidget(self.gl_widget)

        self.view_stack.setCurrentWidget(self.gl_widget)

    def show_video_stream(self):
        if self.gl_widget:
            self.gl_widget.cleanup()
            self.view_stack.removeWidget(self.gl_widget)
            self.gl_widget.deleteLater()
            self.gl_widget = None

        if self.video_widget is None:
            self.video_widget = VideoGLWidget()
            self.view_stack.addWidget(self.video_widget)

        self.view_stack.setCurrentWidget(self.video_widget)

    def closeEvent(self, event):
        # if self.video_processor:
        #     self.video_processor.stop()
        if self.gl_widget:
            self.gl_widget.cleanup()
        event.accept()