import os, torch
from ui.widgets.base import BaseGLWidget
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt, QPoint
from OpenGL.GL import *
from OpenGL.GLU import *
from utils.colors import parse_to_rgba
from ai.location.utils.dataset import parse_filename
from PIL import Image
from utils.models import ModelManager
from ui.dispatcher import dispatcher
from utils.map import MapManager
from utils.config import ConfigManager

class GLWidget(BaseGLWidget):
    VISUAL_TEST_DIR = 'ai/location/dataset/visualtest'
    REAL_TEST_DIR = 'ai/location/dataset/realtest'
    DATASET_TYPE = 'train'

    to_display = ['objects']

    objects_3d    = []
    zone_polygons = []

    dots = []
    connections = []
    selected_dot = None
    hovered_dot = None
    selected_dot = None  
    info_text = ""

    def __init__(self, parent=None):
        super().__init__(parent)

        dispatcher.GLMAP_MODE.connect(self.set_mode)
        dispatcher.map_changed.connect(self.map_changed)

        self.upload_map(ConfigManager.get('last_opened_map') or MapManager.get_available_maps()[0])

        self.set_objects()

    def set_mode(self, mode):
        if mode == 'default_map_view':
            self.set_objects()
        elif mode == 'zones':
            self.set_zones()
        elif mode == 'visual_test':
            self.visualtest()
        elif mode == 'screenshot_density':
            self.visualiseScreenshots()
    
    def map_changed(self, mapname):
        # Map change handler
        if self.currentMap != mapname or self.mapdata is None:
            self.upload_map(mapname)
        
        self.set_map()
    
    def upload_map(self, mapname):
        # Set map data
        self.currentMap, self.mapdata = mapname, MapManager.get_map(mapname)
        self.set_viewpoint()

    def set_map(self):
        # Clear old data
        self.set_viewpoint()
        self.clear_3d_objects()
        self.clear_dots_data()

        if 'objects' in self.to_display:
            self.set_objects()
        
        if 'zones' in self.to_display:
            self.set_zones()
    
    def set_viewpoint(self):
        # Update map viewpoint
        view = self.mapdata['view']
        self.camera_pos = view['camera']['position']
        self.rotate_x, self.rotate_z = view['rotation']['x'], view['rotation']['z']
        self.zoom = view['camera']['zoom']

    def set_objects(self, groups = '*'):
        # Set 3D objects that has xyz & width, length, height params
        objects = self.mapdata['objects']

        for oname in objects:
            color = objects[oname]['color']
            elements = objects[oname]['elements']

            # Filter object groups
            if oname not in groups and groups != '*':
                continue

            for el in elements:
                self.objects_3d.append(((el['x'], el['y'], el['z']), (el['width'], el['length'], el['height']), color))

    def set_zones(self):
        # Fill data 
        self.clear_dots_data()
        self.clear_3d_objects()
        self.clear_zone_polygons()

        self.zone_polygons = []
    
    def clear_dots_data(self):
        # Reset all dots and connections
        self.dots = []
        self.connections = []
        self.dots_data = []
        self.selected_dot = None
        self.hovered_dot = None
        self.selected_dot = None  
        self.info_text = ""

    def clear_3d_objects(self):
        self.objects_3d = []
    
    def clear_zone_polygons(self):
        self.zone_polygons = []

    def visualtest(self):
        self.clear_dots_data()

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
        dir = f'ai/location/dataset/{self.DATASET_TYPE}/{self.currentMap}'

        # Собираем все изображения
        for filename in os.listdir(dir):
            if filename.endswith(".jpg"):
                metadata = parse_filename(filename)

                data = {'value': f"{metadata['x']} {metadata['y']} {metadata['z']}", 'imgpath': f"{dir}/{filename}"}
    
                self.dots.append(self.create_dot((metadata['x'], metadata['y'], metadata['z']), color='red', radius=5, data=data))
        
        self.update()

    def drawElements(self):
        # Отрисовка призм
        for center, size, color in self.objects_3d:
            self.draw_prism(center, size, color)

        # Отрисовка соединений между кружочками
        self.draw_connections()

        # Отрисовка сфер
        self.draw_dots()
        
        # Отрисовка информации о выделенной точке
        self.draw_selection_info()

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

    def handle_dot_selection(self, event):
        # Преобразуем координаты мыши в координаты OpenGL
        viewport   = glGetIntegerv(GL_VIEWPORT)
        modelview  = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        
        y = viewport[3] - event.y()  # Инвертируем Y
        win_x, win_y = event.x(), y
        
        # Находим ближайший кружочек
        closest_dot = None
        min_dist = float('inf')
        
        for i, (pos, _, radius, _) in enumerate(self.dots):
            # Преобразуем мировые координаты в экранные
            screen_pos = gluProject(pos[0], pos[1], pos[2], modelview, projection, viewport)
            
            if screen_pos:
                dist = ((screen_pos[0] - win_x) ** 2 + (screen_pos[1] - win_y) ** 2) ** 0.5
                
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
        
        screen_pos = gluProject(pos[0], pos[1], pos[2], modelview, projection, viewport)
        
        if not screen_pos:
            return
            
        # Получаем глубину кружочка
        depth = screen_pos[2]
        
        # Преобразуем новые экранные координаты в мировые
        new_win_x = event.x()
        new_win_y = viewport[3] - event.y()  # Инвертируем Y
        
        new_pos = gluUnProject(new_win_x, new_win_y, depth, modelview, projection, viewport)
        
        if new_pos:
            # Обновляем позицию кружочка
            color, radius, selected = self.dots[self.selected_dot][1:]
            self.dots[self.selected_dot] = (list(new_pos), color, radius, selected)
            self.update()
