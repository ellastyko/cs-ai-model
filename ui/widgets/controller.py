import os
from PyQt5.QtOpenGL import QGLWidget
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QFrame, QMessageBox
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
from ui.dispatcher import dispatcher
from utils import map

btnStyle = """
            QPushButton {
                min-width: 220px;
                background-color: #303030;
                color: white;
                padding: 5px;
                font-size: 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """

class MapControllerWidget(QWidget):
    _mode = '3dmap'

    def __init__(self, main_widget):
        super().__init__()
        self.main_widget = main_widget
        self._init_ui()
        
    def _init_ui(self):
        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        main_layout_line = QHBoxLayout()
        secondary_layout_line = QHBoxLayout()

        vlayout.addLayout(main_layout_line)
        vlayout.addLayout(secondary_layout_line)

        self.btn_3dmap = QPushButton("3D Map")
        self.btn_videostream = QPushButton("Video Stream")
        self.btn_live_mode = QPushButton("Live mode")
        self.btn_default_map_view = QPushButton("Default view")
        self.btn_visual_test = QPushButton("Model visual test")
        self.btn_screenshot_density = QPushButton("Screenshot density")

        # Event handlers
        self.btn_3dmap.clicked.connect(lambda: self.set_mode('3dmap'))
        self.btn_videostream.clicked.connect(lambda: self.set_mode('videostream'))
        self.btn_live_mode.clicked.connect(lambda: self.set_mode('livemode'))
        self.btn_default_map_view.clicked.connect(lambda: dispatcher.map_mode.emit('default_map_view'))
        self.btn_visual_test.clicked.connect(lambda: dispatcher.map_mode.emit('visual_test'))
        self.btn_screenshot_density.clicked.connect(lambda: dispatcher.map_mode.emit('screenshot_density'))

        # Активный стиль
        self.active_style = "background-color: #2a82da;"

        # Stylesheet
        self.btn_3dmap.setStyleSheet(btnStyle)
        self.btn_videostream.setStyleSheet(btnStyle)
        self.btn_live_mode.setStyleSheet(btnStyle)
        self.btn_default_map_view.setStyleSheet(btnStyle)
        self.btn_visual_test.setStyleSheet(btnStyle)
        self.btn_screenshot_density.setStyleSheet(btnStyle)

        main_layout_line.setAlignment(Qt.AlignLeft | Qt.AlignTop) 
        main_layout_line.addWidget(self.btn_3dmap)
        main_layout_line.addWidget(self.btn_videostream)
        main_layout_line.addWidget(self.btn_live_mode)

        secondary_layout_line.addWidget(self.btn_default_map_view)
        secondary_layout_line.addWidget(self.btn_visual_test)
        secondary_layout_line.addWidget(self.btn_screenshot_density)
    
    def set_mode(self, mode):
        if mode == '3dmap':
            self.main_widget.show_3d_scene()
        elif mode == 'videostream':
            self.main_widget.show_video_stream()
        elif mode == 'livemode':
            pass
        
        self._mode = mode