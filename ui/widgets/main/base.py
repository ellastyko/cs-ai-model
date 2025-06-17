import os
from PyQt5.QtOpenGL import QGLWidget
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QFrame, QStackedLayout
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QObject
from PyQt5.QtGui import QPixmap
from OpenGL.GL import *
from OpenGL.GLU import *
from utils.colors import parse_to_rgba
from ai.location.utils.dataset import parse_filename
from PyQt5.QtWidgets import QPushButton, QLabel
import torch
from PIL import Image
from transformers import ViTImageProcessor
from utils.models import ModelManager
from utils.helpers import open_image, delete_image
from .gl import GLWidget
from .videostream import VideoGLWidget
from .controllers import MainControllerWidget
import cv2

class Grabber:
    device = None
    cap_size_set = False

    def obs_vc_init(self, capture_device = 0):
        self.device = cv2.VideoCapture(capture_device)

    def set_cap_size(self, w, h):
        self.device.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self.device.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
    
    def release(self):
        self.device.release()

    def get_frame(self, grab_area):
        """
        Return last frame.
        :return: numpy array
        """
        if not self.cap_size_set:
            self.set_cap_size(grab_area['width'], grab_area['height'])
            self.cap_size_set = True

        ret, frame = self.device.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        return frame
    
class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.controller = MainControllerWidget(self)
        self.view_stack = QStackedLayout()

        layout.addWidget(self.controller, stretch=1)
        layout.addLayout(self.view_stack, stretch=9)

        self.gl_widget = None
        self.video_widget = None

        # Default view
        self.show_3d_scene()

    def show_3d_scene(self):
        if self.video_widget:
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
            grabber = Grabber()
            self.video_widget = VideoGLWidget(grabber)
            self.view_stack.addWidget(self.video_widget)

        self.view_stack.setCurrentWidget(self.video_widget)

    def show_live_mode(self):
        if self.gl_widget:
            self.gl_widget.cleanup()
            self.view_stack.removeWidget(self.gl_widget)
            self.gl_widget.deleteLater()
            self.gl_widget = None

        if self.video_widget is None:
            grabber = Grabber()
            self.video_widget = VideoGLWidget(grabber)
            self.view_stack.addWidget(self.video_widget)

        self.view_stack.setCurrentWidget(self.video_widget)

    def closeEvent(self, event):
        if self.video_widget:
            self.video_widget.closeEvent(event)
        if self.gl_widget:
            self.gl_widget.cleanup()
        event.accept()