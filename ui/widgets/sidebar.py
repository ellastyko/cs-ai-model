import os
from PyQt5.QtOpenGL import QGLWidget
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QFrame
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QObject
from PyQt5.QtGui import QPixmap
from utils import map
from utils.colors import parse_to_rgba
from location.utils.dataset import parse_filename
from PyQt5.QtWidgets import QPushButton, QLabel
import torch
from PIL import Image
from transformers import ViTImageProcessor
from utils.models import ModelManager
from utils.helpers import open_image, delete_image
from ui.dispatcher import dispatcher
from utils.config import ConfigManager

btnStyle = """
            QPushButton {
                background-color: #212121;
                color: white;
                padding: 5px;
                font-size: 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """
cboxStyle = """
            QComboBox {
                background-color: #303030;
                color: white;
                padding: 5px;
                font-size: 12px;
                border-radius: 3px;
            }
            QComboBox:!editable:on, QComboBox::drop-down:editable:on {
                color: white;
            }   
        """

class SidebarWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.locationPreveiwWidget = LocationPreviewWidget()
        self.settingsWidget        = SettingsWidget()
        self.sourceWidget           = SourceWidget()

        layout.addWidget(self.locationPreveiwWidget, stretch=3)
        layout.addWidget(self.settingsWidget, stretch=3)
        layout.addWidget(self.sourceWidget, stretch=4)


class SettingsWidget(QFrame):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        inner_layout = QVBoxLayout()

        self.setStyleSheet("""
            border-radius: 5px;
            background-color: #303030;
            color: white;
        """)

        # Создаем заголовок
        self.label_title = QLabel("Settings")
        self.label_title.setAlignment(Qt.AlignCenter)
        self.label_title.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            background-color: #212121; 
            padding: 5px;
            margin-bottom: 10px;
        """)

        self.cbox_model = QComboBox()
        self.cbox_map = QComboBox()

        for filename in ModelManager.list():
            self.cbox_model.addItem(filename)
        
        for mapname in map.get_map_list():
            self.cbox_map.addItem(mapname)

        nmodel = ConfigManager.get('neural_model')
        lomap  = ConfigManager.get('last_opened_map')

        if nmodel is None:
            nmodel = ModelManager.list()[-1] 
            ConfigManager.get('neural_model', nmodel)

        if lomap is None:
            lomap = map.get_map_list()[0]
            ConfigManager.get('last_opened_map', lomap)

        # Set default values
        self.cbox_model_update(nmodel)
        self.cbox_map_update(lomap)

        self.cbox_model.currentTextChanged.connect(self.cbox_model_update)
        self.cbox_map.currentTextChanged.connect(self.cbox_map_update)
        self.cbox_model.setStyleSheet(cboxStyle)
        self.cbox_map.setStyleSheet(cboxStyle)

        layout.addWidget(self.label_title)
        layout.addLayout(inner_layout)
        inner_layout.addWidget(self.cbox_model)
        inner_layout.addWidget(self.cbox_map)

    # Model change handler
    def cbox_model_update(self, value):
        ModelManager.switchModel(value)
        ConfigManager.get('neural_model', value)

    # Map change handler
    def cbox_map_update(self, value):
        dispatcher.map_changed.emit(value)
        ConfigManager.get('last_opened_map', value)

class SourceWidget(QFrame):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.setStyleSheet("""
            border-radius: 5px;
            background-color: #303030;
            color: white;
        """)

        # Создаем заголовок
        self.label_title = QLabel("Sources")
        self.label_title.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            background-color: #212121; 
            padding: 5px;
            margin-bottom: 10px;
        """)
        self.label_title.setAlignment(Qt.AlignCenter)

        self.add_source_btn = QPushButton("Add source")
        self.add_source_btn.setStyleSheet(btnStyle)
        self.add_source_btn.clicked.connect(self.on_add_source)

        layout.addWidget(self.label_title, 1)
        layout.addWidget(LobbyWidget(), 8)
        layout.addWidget(self.add_source_btn, 1)

    def on_add_source(self):
        pass

class LobbyWidget(QFrame):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.setStyleSheet("""
            border-radius: 5px;
            background-color: #212121;
            color: white;
        """)

class LocationPreviewWidget(QFrame):
    DEFAULT_IMG = 'assets/no-img.png'
    DEFAULT_TEXT = 'Coordinates'

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.current_image_path = None

        dispatcher.title_changed.connect(self.set_title)
        dispatcher.image_changed.connect(self.set_image)

            # Почему цвет фон добавился к двум  QLabel а не контейнеру. ПРостранство между QLabel не такого цвета как я указал для этого блока
        self.setStyleSheet("""
            border-radius: 5px;
            background-color: #303030; 
            color: white;
        """)

        # Создаем заголовок
        self.title_label = QLabel(self.DEFAULT_TEXT)
        self.title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            background-color: #212121; 
            padding: 5px;
            margin-bottom: 10px;
        """)
        self.title_label.setAlignment(Qt.AlignCenter)

        # Создаем виджет для изображения
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("margin: 5px; padding: 5px; background-color: #212121;")
        self.reset_to_default()

        btn_layout = QHBoxLayout()

        self.delete_image_btn = QPushButton('Delete')
        self.show_image_btn = QPushButton('Show image')

        self.delete_image_btn.clicked.connect(self.on_delete_image)
        self.show_image_btn.clicked.connect(self.on_show_image)

        self.delete_image_btn.setStyleSheet(btnStyle)
        self.show_image_btn.setStyleSheet(btnStyle)

        layout.addWidget(self.title_label)
        layout.addWidget(self.image_label)
        layout.addLayout(btn_layout)
        btn_layout.addWidget(self.show_image_btn)
        btn_layout.addWidget(self.delete_image_btn)

        # Добавляем растягивающий элемент для правильного позиционирования
        layout.addStretch()
    
    def on_show_image(self):
        open_image(self.current_image_path)

    def on_delete_image(self):
        delete_image(self.current_image_path)
        self.reset_to_default()

    def set_title(self, text: str):
        """Установка текста заголовка"""
        self.title_label.setText(text)

    def reset_to_default(self): 
        self.current_image_path = None
        self.title_label.setText(self.DEFAULT_TEXT)
        self.set_image(self.DEFAULT_IMG, False)

    def set_image(self, image_path: str, save_as_current = True):
        """Загрузка и отображение изображения"""
        if save_as_current is True:
            self.current_image_path = image_path

        pixmap = QPixmap(image_path)
        
        # Масштабируем изображение, сохраняя пропорции
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                300, 200,  # Ширина, высота
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.setText("Изображение не найдено")
