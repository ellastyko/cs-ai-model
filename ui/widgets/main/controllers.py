import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QStackedWidget, QButtonGroup)
from PyQt5.QtCore import Qt
from ui.dispatcher import dispatcher

btnStyle = """
    QPushButton {
        width: 200px;
        background-color: #303030;
        color: white;
        padding: 5px;
        font-size: 12px;
        border-radius: 5px;
    }
    QPushButton:hover {
        background-color: #45a049;
    }
    QPushButton:checked {
        background-color: #2a82da;
    }
"""

class MainControllerWidget(QWidget):
    def __init__(self, main_widget):
        super().__init__()
        self.main_widget = main_widget
        self._init_ui()
        
    def _init_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Основные кнопки режимов
        self.mode_buttons_layout = QHBoxLayout()
        self.layout.addLayout(self.mode_buttons_layout)

        # Создаем группу для основных кнопок (работают как радио-кнопки)
        self.mode_button_group = QButtonGroup(self)
        self.mode_button_group.setExclusive(True)

        # Основные кнопки
        self.btn_3dmap = self._create_mode_button("3D Map", '3dmap')
        self.btn_videostream = self._create_mode_button("Video Stream", 'videostream')
        self.btn_live_mode = self._create_mode_button("Live mode", 'livemode')

        # Добавляем кнопки в группу и layout
        for i, btn in enumerate([self.btn_3dmap, self.btn_videostream, self.btn_live_mode]):
            self.mode_button_group.addButton(btn, i)
            self.mode_buttons_layout.addWidget(btn)

        # StackedWidget для второстепенных кнопок
        self.secondary_buttons_stack = QStackedWidget()
        self.layout.addWidget(self.secondary_buttons_stack)

        # Создаем страницы с кнопками для каждого режима
        self._create_3dmap_buttons()
        self._create_videostream_buttons()
        self._create_livemode_buttons()

        # Устанавливаем начальный режим
        self.btn_3dmap.setChecked(True)
        self._update_secondary_buttons('3dmap')

        # Подключаем обработчик изменения режима
        self.mode_button_group.buttonClicked.connect(self._on_mode_changed)
    
    def _create_mode_button(self, text, mode):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setStyleSheet(btnStyle)
        btn.mode = mode  # Сохраняем режим как свойство кнопки
        return btn
    
    def _create_3dmap_buttons(self):
        """Создает панель кнопок для режима 3D карты"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        
        buttons = [
            ("Default view", lambda: dispatcher.GLMAP_MODE.emit('default_map_view')),
            ("Zones", lambda: dispatcher.GLMAP_MODE.emit('zones')),
            ("Model visual test", lambda: dispatcher.GLMAP_MODE.emit('visual_test')),
            ("Screenshot density", lambda: dispatcher.GLMAP_MODE.emit('screenshot_density'))
        ]
        
        for text, handler in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet(btnStyle)
            btn.clicked.connect(handler)
            layout.addWidget(btn)
        
        self.secondary_buttons_stack.addWidget(panel)
    
    def _create_videostream_buttons(self):
        """Создает панель кнопок для режима видеопотока"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        
        buttons = [
            ("Default", lambda: dispatcher.VIDEOSTREAM_MODE.emit('default')),
            ("With Neuron Model", lambda: dispatcher.VIDEOSTREAM_MODE.emit('with_nmodel'))
        ]
        
        for text, handler in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet(btnStyle)
            btn.clicked.connect(handler)
            layout.addWidget(btn)
        
        self.secondary_buttons_stack.addWidget(panel)
    
    def _create_livemode_buttons(self):
        """Создает панель кнопок для live режима"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        
        buttons = [
            ("Sessions", lambda: dispatcher.LIVE_MODE.emit('sessions')),
            ("Logs", lambda: dispatcher.LIVE_MODE.emit('logs')),
        ]
        
        for text, handler in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet(btnStyle)
            btn.clicked.connect(handler)
            layout.addWidget(btn)
        
        self.secondary_buttons_stack.addWidget(panel)
    
    def _on_mode_changed(self, button):
        """Обработчик изменения основного режима"""
        mode = button.mode
        self._update_secondary_buttons(mode)
        
        # Обновляем главный виджет
        if mode == '3dmap':
            self.main_widget.show_3d_scene()
        elif mode == 'videostream':
            self.main_widget.show_video_stream()
        elif mode == 'livemode':
            self.main_widget.show_live_mode()
    
    def _update_secondary_buttons(self, mode):
        """Обновляет видимые второстепенные кнопки в соответствии с режимом"""
        if mode == '3dmap':
            self.secondary_buttons_stack.setCurrentIndex(0)
        elif mode == 'videostream':
            self.secondary_buttons_stack.setCurrentIndex(1)
        elif mode == 'livemode':
            self.secondary_buttons_stack.setCurrentIndex(2)