import os
from PyQt5.QtOpenGL import QGLWidget
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt, QPoint
from OpenGL.GL import *
from OpenGL.GLU import *
from utils.colors import parse_to_rgba
from location.utils.dataset import parse_filename
import torch
from PIL import Image
from transformers import ViTImageProcessor
from utils.models import ModelManager
from ui.dispatcher import dispatcher
from utils import map
from utils.config import ConfigManager

class GLWidget(QGLWidget):
    VISUAL_TEST_DIR = 'location/dataset/visualtest'
    REAL_TEST_DIR = 'location/dataset/realtest'
    DATASET_TYPE = 'train'

    def __init__(self, parent=None):
        super().__init__(parent)

        dispatcher.map_mode.connect(self.set_mode)
        dispatcher.map_changed.connect(self.upload_map)

        self.upload_map(ConfigManager.get('last_opened_map') or ModelManager.list()[-1])
        # Загрузка и подготовка изображения
        self.processor = ViTImageProcessor.from_pretrained("google/vit-base-patch16-224")
        self.last_pos = QPoint()
    
    def _init_ui(self):
        self.setStyleSheet("""
            border-radius: 5px;
            background-color: #303030;
            color: white;
        """)

    def set_mode(self, mode):
        if mode == 'default_map_view':
            self.upload_map(self.currentMap)
        elif mode == 'visual_test':
            self.visualtest()
        elif mode == 'screenshot_density':
            self.visualiseScreenshots()
    
    def upload_map(self, mapname):
        self.currentMap = mapname

        mapdata = map.get_map_resources(self.currentMap)

        view = mapdata['view']

        self.camera_pos = view['camera']['position']
        self.rotate_x, self.rotate_z = view['rotation']['x'], view['rotation']['z']
        self.zoom = view['camera']['zoom']

        groups = mapdata['groups']

        self.clearElements()
        self.clearMap()

        self.selected_dot = None
        self.hovered_dot = None
        self.info_text = ""
        self.selected_dot = None  # Индекс выбранного кружочка
        self.drag_start_pos = None  # Начальная позиция при перетаскивании

        for group_name in groups:
            color = groups[group_name]['color']
            elements = groups[group_name]['elements']

            for el in elements:
                self.prisms.append(((el['x'], el['y'], el['z']), (el['width'], el['length'], el['height']), color))
        
        self.update()

    def predictCoordinates(self, img_path):
        self.model, _ = ModelManager.getCurrentModel()

        # Predict coordinates with image
        image = Image.open(img_path)

        inputs = self.processor(images=image, return_tensors="pt")

        with torch.no_grad():
            pixel_values = inputs["pixel_values"].to("cuda")
            outputs = self.model({"pixel_values": pixel_values})
            predicted_coords = outputs.squeeze().tolist()

            return predicted_coords[0], predicted_coords[1], predicted_coords[2], predicted_coords[3], predicted_coords[4]
    
    def clearElements(self):
        # Reset all dots and connections
        self.dots = []
        self.connections = []
        self.dots_data = []

    def clearMap(self,):
        # remove polygons
        self.prisms = []

    def visualtest(self):
        self.clearElements()

        root_dir = f'{self.VISUAL_TEST_DIR}/{self.currentMap}'

        if os.path.exists(root_dir) is False:
            QMessageBox.critical(None, "Ошибка", f"Отсутвует директория с папкой {self.currentMap} по пути {root_dir}")
            return

        for filename in os.listdir(root_dir):
            if filename.lower().endswith(".jpg"):
                expected = parse_filename(filename)
                x, y, z, pitch, yaw = self.predictCoordinates(f"{root_dir}/{filename}")

                length = len(self.dots)

                expected_pos = f"{expected['x']} {expected['y']} {expected['z']}"
                real_pos = f"{x:.0f} {y:.0f} {z:.0f}"
                
                general_data = {'imgpath': f"{root_dir}/{filename}"}

                expected_dot = self.create_dot(
                    (expected['x'], expected['y'], expected['z']), 
                    color='green', 
                    radius=20, 
                    data={**{'value': expected_pos}, **general_data}
                )

                real_dot = self.create_dot(
                    (x, y, z), 
                    color='red', 
                    radius=20, 
                    data={**{'value': real_pos}, **general_data}
                )

                self.dots.append(expected_dot)
                self.dots.append(real_dot)

                self.connections.append([length, length + 1, (0.0, 0.0, 1.0, 1.0)])
        self.update()

    def visualiseScreenshots(self):
        dir = f'location/dataset/{self.DATASET_TYPE}/{self.currentMap}'

        # Собираем все изображения
        for filename in os.listdir(dir):
            if filename.endswith(".jpg"):
                metadata = parse_filename(filename)

                data = {'value': f"{metadata['x']} {metadata['y']} {metadata['z']}", 'imgpath': f"{dir}/{filename}"}
    
                self.dots.append(self.create_dot((metadata['x'], metadata['y'], metadata['z']), color='red', radius=5, data=data))
        
        self.update()

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
        self.draw_axes(1500)

        # Отрисовка призм
        for center, size, color in self.prisms:
            self.draw_prism(center, size, color)

        # Отрисовка соединений между кружочками
        self.draw_connections()

        # Отрисовка сфер
        self.draw_dots()
        
        # Отрисовка информации о выделенной точке
        self.draw_selection_info()
        # HUD
        self.draw_hud()

    def draw_dots(self):
        glDisable(GL_LIGHTING)
        
        # 1) Быстро рисуем все точки через GL_POINTS
        glPointSize(3.0)  # размер точек (можно варьировать)
        glBegin(GL_POINTS)
        for i, dot in enumerate(self.dots):
            color = parse_to_rgba(dot["color"])
            glColor4fv(color)
            pos = dot["position"]
            glVertex3f(*pos)
        glEnd()
        
        # 2) Выделяем выбранную точку более сложной геометрией
        if self.selected_dot is not None and len(self.dots) > self.selected_dot:
            dot = self.dots[self.selected_dot]
            pos = dot["position"]
            radius = dot["radius"]
            glPushMatrix()
            glTranslatef(*pos)
            glColor4f(1.0, 1.0, 0.0, 0.5)  # желтая полупрозрачная подсветка
            self.draw_sphere(radius * 1.5, 8, 8)  # сфера с низкой детализацией
            glPopMatrix()
        
        # 3) Подсветка при наведении (если нужно)
        if self.hovered_dot is not None and self.hovered_dot != self.selected_dot and len(self.dots) > self.hovered_dot:
            dot = self.dots[self.hovered_dot]
            pos = dot["position"]
            radius = dot["radius"]
            glPushMatrix()
            glTranslatef(*pos)
            glColor4f(1.0, 1.0, 1.0, 0.3)  # белая подсветка
            self.draw_sphere(radius * 1.3, 8, 8)
            glPopMatrix()
        
        glEnable(GL_LIGHTING)

    def draw_selection_info(self):
        if self.selected_dot is not None and len(self.dots) > self.selected_dot:
            dot = self.dots[self.selected_dot]

            dot_data = dot['data']

            if 'imgpath' in dot_data:
                dispatcher.title_changed.emit(dot_data['value'])
                dispatcher.image_changed.emit(dot_data['imgpath'])

            info = self.format_dot_info(dot)
            
            # Получаем экранные координаты точки
            viewport = glGetIntegerv(GL_VIEWPORT)
            modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
            projection = glGetDoublev(GL_PROJECTION_MATRIX)
            
            screen_pos = gluProject(dot["position"][0], dot["position"][1], dot["position"][2], modelview, projection, viewport)
            
            if screen_pos:
                x, y = int(screen_pos[0]), int(viewport[3] - screen_pos[1])
                self.renderText(x + 15, y - 15, info)

    def format_dot_info(self, dot):
        """Форматирует информацию о точке для отображения"""
        info = []
        if "name" in dot["data"]:
            info.append(f"Название: {dot['data']['name']}")
        if "type" in dot["data"]:
            info.append(f"Тип: {dot['data']['type']}")
        if "value" in dot["data"]:
            info.append(f"Значение: {dot['data']['value']}")
        return "\n".join(info)
    
    def draw_connections(self):
        glDisable(GL_LIGHTING)
        glBegin(GL_LINES)
        for dot1_idx, dot2_idx, color in self.connections:
            if dot1_idx < len(self.dots) and dot2_idx < len(self.dots):
                pos1 = self.dots[dot1_idx]['position']
                pos2 = self.dots[dot2_idx]['position']
                glColor4fv(color)
                glVertex3fv(pos1)
                glVertex3fv(pos2)
        glEnd()
        glEnable(GL_LIGHTING)

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

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            # Снимаем выделение со всех точек
            for dot in self.dots:
                dot["selected"] = False
            self.selected_dot = None
            
            # Проверяем, была ли нажата точка
            dot_index = self.find_dot_at_position(event.pos())
            if dot_index is not None:
                self.dots[dot_index]["selected"] = True
                self.selected_dot = dot_index
                self.update()
        
        self.last_pos = event.pos()

    def mouseMoveEvent(self, event):
        # Обновляем hover-эффект
        prev_hover = self.hovered_dot
        self.hovered_dot = self.find_dot_at_position(event.pos())
        
        if prev_hover != self.hovered_dot:
            self.update()

        if event.buttons() == Qt.LeftButton:
            dx = event.x() - self.last_pos.x()
            dz = event.y() - self.last_pos.y()
            self.rotate_z += dx * 0.5
            self.rotate_x += dz * 0.5
            self.last_pos = event.pos()
            self.update()

    def find_dot_at_position(self, pos):
        """Находит точку по экранным координатам"""
        viewport = glGetIntegerv(GL_VIEWPORT)
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        
        y = viewport[3] - pos.y()
        
        for i, dot in enumerate(self.dots):
            screen_pos = gluProject(dot["position"][0], dot["position"][1], dot["position"][2],
                                  modelview, projection, viewport)
            if screen_pos:
                dist = ((screen_pos[0] - pos.x()) ** 2 + 
                        (screen_pos[1] - y) ** 2) ** 0.5
                if dist < dot["radius"] * 2:  # Увеличиваем зону клика
                    return i
        return None

    def create_dot(self, position, color, radius, data=None):
        """Создает новую точку с дополнительными данными"""
        if data is None:
            data = {}
        return {
            "position": list(position),
            "color": color,
            "radius": radius,
            "selected": False,
            "data": data
        }
    
    def wheelEvent(self, event):
        self.zoom += event.angleDelta().y() * 0.2
        self.update()

    def handle_dot_selection(self, event):
        # Преобразуем координаты мыши в координаты OpenGL
        viewport = glGetIntegerv(GL_VIEWPORT)
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        
        y = viewport[3] - event.y()  # Инвертируем Y
        win_x, win_y = event.x(), y
        
        # Находим ближайший кружочек
        closest_dot = None
        min_dist = float('inf')
        
        for i, (pos, _, radius, _) in enumerate(self.dots):
            # Преобразуем мировые координаты в экранные
            screen_pos = gluProject(pos[0], pos[1], pos[2],
                                  modelview, projection, viewport)
            
            if screen_pos:
                dist = ((screen_pos[0] - win_x) ** 2 + 
                        (screen_pos[1] - win_y) ** 2) ** 0.5
                
                if dist < radius and dist < min_dist:
                    min_dist = dist
                    closest_dot = i
        
        # Если нашли кружочек - выделяем его
        if closest_dot is not None:
            # Снимаем выделение с предыдущего
            if self.selected_dot is not None:
                pos, color, radius, _ = self.dots[self.selected_dot]
                self.dots[self.selected_dot] = (pos, color, radius, False)
            
            # Выделяем новый
            pos, color, radius, _ = self.dots[closest_dot]
            self.dots[closest_dot] = (pos, color, radius, True)
            self.selected_dot = closest_dot
            self.drag_start_pos = event.pos()
        else:
            # Если кликнули в пустое место - снимаем выделение
            if self.selected_dot is not None:
                pos, color, radius, _ = self.dots[self.selected_dot]
                self.dots[self.selected_dot] = (pos, color, radius, False)
                self.selected_dot = None
        
        self.update()

    def move_selected_dot(self, event):
        if self.selected_dot is None:
            return
            
        # Получаем текущую позицию кружочка
        pos = self.dots[self.selected_dot]['position']
        
        # Преобразуем мировые координаты в экранные
        viewport = glGetIntegerv(GL_VIEWPORT)
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        
        screen_pos = gluProject(pos[0], pos[1], pos[2],
                              modelview, projection, viewport)
        
        if not screen_pos:
            return
            
        # Получаем глубину кружочка
        depth = screen_pos[2]
        
        # Преобразуем новые экранные координаты в мировые
        new_win_x = event.x()
        new_win_y = viewport[3] - event.y()  # Инвертируем Y
        
        new_pos = gluUnProject(new_win_x, new_win_y, depth,
                             modelview, projection, viewport)
        
        if new_pos:
            # Обновляем позицию кружочка
            color, radius, selected = self.dots[self.selected_dot][1:]
            self.dots[self.selected_dot] = (list(new_pos), color, radius, selected)
            self.update()

    def cleanup(self):
        self.makeCurrent()
        # Очисти буферы, текстуры, выделенную память
        self.doneCurrent()