import os
from PyQt5.QtOpenGL import QGLWidget
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QFrame
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
from ui.widgets.gl import GLWidget, MapControllerWidget

class MainWidget(QWidget): 
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.glWidget             = GLWidget()
        self.mapControllerWidget  = MapControllerWidget(self.glWidget)
        layout.addWidget(self.mapControllerWidget, stretch=1)
        layout.addWidget(self.glWidget, stretch=9)