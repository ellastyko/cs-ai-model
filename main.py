import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtOpenGL import QGLWidget
from PyQt5.QtCore import Qt, QPoint
from OpenGL.GL import *
from OpenGL.GLU import *
from map.map import Map 


class GLWidget(QGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        map = Map()
        mapdata = map.resources('cs_italy')

        view = mapdata['view']

        self.camera_pos = view['camera']['position']
        self.rotate_x, self.rotate_y = view['rotation']['x'], view['rotation']['y']
        self.zoom = view['camera']['zoom']

        groups = mapdata['groups']

        self.prisms = []

        for group_name in groups:
            color = groups[group_name]['color']
            elements = groups[group_name]['elements']

            for el in elements:
                center = (el['x'], el['z'], el['y'])
                size   = (el['width'], el['height'], el['length'])

                self.prisms.append((center, size, color))

        self.last_pos = QPoint()

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
        glRotatef(self.rotate_y, 0, 1, 0)

        # Источник света
        glLightfv(GL_LIGHT0, GL_POSITION, [5, 10, 5, 1])

        # Оси координат
        self.draw_axes(1500)

        # Отрисовка призм
        for center, size, color in self.prisms:
            self.draw_prism(center, size, color)

        # HUD
        self.draw_hud()

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
        self.renderText(10, 20, f"Rotation: X={self.rotate_x:.1f}° Y={self.rotate_y:.1f}°")
        self.renderText(10, 40, f"Zoom: Z={self.zoom:.1f}°")
        self.renderText(10, 60, "Controls: LMB - rotate, Wheel - zoom")

    def mousePressEvent(self, event):
        self.last_pos = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            dx = event.x() - self.last_pos.x()
            dy = event.y() - self.last_pos.y()
            self.rotate_y += dx * 0.5
            self.rotate_x += dy * 0.5
            self.last_pos = event.pos()
            self.update()

    def wheelEvent(self, event):
        self.zoom += event.angleDelta().y() * 0.2
        self.update()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FARM AI")
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        # right_widget = QWidget()
        self.setCentralWidget(central_widget)
        # self.setCentralWidget(right_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        self.glWidget = GLWidget()
        layout.addWidget(self.glWidget)
        layout.addWidget(self.glWidget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())