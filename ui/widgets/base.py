import os
from PyQt5.QtOpenGL import QGLWidget
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt, QPoint
from OpenGL.GL import *
from OpenGL.GLU import *
from utils.colors import parse_to_rgba
from ai.location.utils.dataset import parse_filename
import torch
from PIL import Image
from utils.models import ModelManager
from ui.dispatcher import dispatcher
from utils.map import MapManager
from utils.config import ConfigManager

class BaseGLWidget(QGLWidget):
    zoom = 0
    rotate_x = 0
    rotate_z = 0

    AXES = True
    HUD  = True

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        # Загрузка и подготовка изображения
        self.last_pos = QPoint()
    
    def _init_ui(self):
        self.setStyleSheet("""
            border-radius: 5px;
            background-color: #303030;
            color: white;
        """)

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0.53, 0.81, 0.98, 1.0)

        # Освещение
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, [1, 1, 1, 0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.2, 0.2, 0.2, 1])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [1, 1, 1, 1])

        glMaterialfv(GL_FRONT, GL_AMBIENT, [0.2, 0.2, 0.2, 1])
        glMaterialfv(GL_FRONT, GL_DIFFUSE, [0.8, 0.8, 0.8, 1])
        glMaterialfv(GL_FRONT, GL_SPECULAR, [1, 1, 1, 1])
        glMaterialf(GL_FRONT, GL_SHININESS, 50)
        glEnable(GL_COLOR_MATERIAL)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w / h, 0.1, 50000.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Управление камерой
        glTranslatef(0, 0, self.zoom)
        glRotatef(self.rotate_x, 1, 0, 0)
        glRotatef(self.rotate_z, 0, 0, 1)

        # Источник света
        glLightfv(GL_LIGHT0, GL_POSITION, [5, 10, 5, 1])

        # Оси координат
        if self.AXES is True:
            self.draw_axes(1500)

        self.drawElements()

        # HUD
        if self.HUD is True:
            self.draw_hud()
            
    @override
    def drawElements(self):
        pass

    def draw_sphere(self, radius, slices, stacks):
        quadric = gluNewQuadric()
        gluSphere(quadric, radius, slices, stacks)
        gluDeleteQuadric(quadric)

    def draw_prism(self, center, size, color):
        w, h, d = size[0] / 2, size[1] / 2, size[2] / 2
        x, y, z = center

        vertices = [
            [x + w, y - h, z - d], [x + w, y + h, z - d], [x - w, y + h, z - d], [x - w, y - h, z - d],
            [x + w, y - h, z + d], [x + w, y + h, z + d], [x - w, y - h, z + d], [x - w, y + h, z + d]
        ]

        glBegin(GL_QUADS)
        glColor4fv(color)

        # Грани с нормалями
        faces = [
            ([0, 1, 2, 3], [0, 0, 1]),  # Передняя
            ([4, 5, 7, 6], [0, 0, -1]),  # Задняя
            ([0, 1, 5, 4], [0, 1, 0]),  # Верхняя
            ([3, 2, 7, 6], [0, -1, 0]),  # Нижняя
            ([0, 3, 6, 4], [-1, 0, 0]),  # Левая
            ([1, 2, 7, 5], [1, 0, 0])  # Правая
        ]

        for indices, normal in faces:
            glNormal3fv(normal)
            for idx in indices:
                glVertex3fv(vertices[idx])
        glEnd()

    def draw_axes(self, length):
        glBegin(GL_LINES)
        glColor3f(1, 0, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(length, 0, 0)  # X
        glColor3f(0, 1, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, length, 0)  # Y
        glColor3f(0, 0, 1)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, length)  # Z
        glEnd()

    def draw_hud(self):
        self.renderText(10, 20, f"Rotation: X={self.rotate_x:.1f}° Y={self.rotate_z:.1f}°")
        self.renderText(10, 40, f"Zoom: Z={self.zoom:.1f}°")
        self.renderText(10, 60, "Controls: LMB - rotate, Wheel - zoom")

    def wheelEvent(self, event):
        self.zoom += event.angleDelta().y() * 0.2
        self.update()

    def cleanup(self):
        self.makeCurrent()
        # Очисти буферы, текстуры, выделенную память
        self.doneCurrent()