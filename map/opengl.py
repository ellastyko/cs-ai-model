import pygame
import numpy as np
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from pygame import freetype  # Для отображения текста

class PrismRenderer:
    def __init__(self):
        pygame.init()
        self.display = (1200, 800)
        pygame.display.set_mode(self.display, DOUBLEBUF | OPENGL)

        # Инициализация шрифта для текста
        freetype.init()
        self.font = freetype.SysFont('Arial', 20)

         # Параметры камеры
        self.camera_pos = [500, 800, 1500]  # Хороший обзорный ракурс
        self.rotate_x, self.rotate_y = 45, 270  # Наклон для 3D обзора
        self.zoom = -5200
        
        # Параметры управления
        self.mouse_dragging = False
        self.last_mouse_pos = (0, 0)
        
        # Настройка проекции
        glMatrixMode(GL_PROJECTION)
        gluPerspective(45, (self.display[0] / self.display[1]), 0.1, 50000.0)
        glMatrixMode(GL_MODELVIEW)
        glTranslatef(*self.camera_pos)
        
        # Настройки OpenGL
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0.53, 0.81, 0.98, 1.0)  # Небо голубого цвета

    def generate_prism_vertices(self, center, width, height, depth):
        """Генерация вершин призмы по центру и размерам"""
        w, h, d = width/2, height/2, depth/2
        x, y, z = center
        
        return [
            [x + w, y - h, z - d],  # 0
            [x + w, y + h, z - d],  # 1
            [x - w, y + h, z - d],  # 2
            [x - w, y - h, z - d],  # 3
            [x + w, y - h, z + d],  # 4
            [x + w, y + h, z + d],  # 5
            [x - w, y - h, z + d],  # 6
            [x - w, y + h, z + d]   # 7
        ]
    
    def draw_prism(self, vertices, color):
        """Отрисовка одной призмы"""
        surfaces = (
            (0, 1, 2, 3),  # задняя грань
            (4, 5, 7, 6),  # передняя грань
            (0, 4, 6, 3),  # нижняя грань
            (1, 5, 7, 2),  # верхняя грань
            (0, 1, 5, 4),  # правая грань
            (3, 2, 7, 6)   # левая грань
        )
        
        glBegin(GL_QUADS)
        glColor4fv(color)
        for surface in surfaces:
            for vertex in surface:
                glVertex3fv(vertices[vertex])
        glEnd()
        
        # # Отрисовка ребер (опционально)
        edges = (
            (0, 1), (0, 3), (0, 4),
            (2, 1), (2, 3), (2, 7),
            (6, 3), (6, 4), (6, 7),
            (5, 1), (5, 4), (5, 7)
        )
        
        glBegin(GL_LINES)
        glColor4f(0, 0, 0, 1)
        for edge in edges:
            for vertex in edge:
                glVertex3fv(vertices[vertex])
        glEnd()
    
    def draw_text(self, text, x, y, z, color=(1,1,1)):
        """Отрисовка текста в 3D пространстве"""
        glPushMatrix()
        glTranslatef(x, y, z)
        glRasterPos3f(0, 0, 0)
        text_surface, _ = self.font.render(text, color)
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        glDrawPixels(text_surface.get_width(), text_surface.get_height(), 
                    GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        glPopMatrix()

    def draw_hud_info(self):
        """Информация на экране"""
        texts = [
            f"Camera: X={self.camera_pos[0]:.0f} Y={self.camera_pos[1]:.0f} Z={self.camera_pos[2]:.0f}",
            f"Rotation: X={self.rotate_x:.1f}° Y={self.rotate_y:.1f}°",
            "Оси: X(красная) Y(зелёная) Z(синяя)",
            "Controls: LMB - вращение, Wheel - масштаб"
        ]
        for i, text in enumerate(texts):
            self.draw_text_2d(text, 10, 30 + i*30)

    def draw_text_2d(self, text, x, y, color=(0,0,0)):
        """Отрисовка 2D текста на экране"""
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, self.display[0], self.display[1], 0)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        text_surface, _ = self.font.render(text, color)
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        
        glRasterPos2d(x, y)
        glDrawPixels(text_surface.get_width(), text_surface.get_height(), 
                    GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    def draw_hud(self):
        """Отрисовка информационной панели"""
        # Получаем текущие параметры камеры
        camera_info = [
            f"Camera Position: X={self.camera_pos[0]:.1f}, Y={self.camera_pos[1]:.1f}, Z={self.camera_pos[2]:.1f}",
            f"Rotation: X={self.rotate_x:.1f}°, Y={self.rotate_y:.1f}°",
            f"Zoom: {self.zoom:.1f}",
            f"Controls: LMB - rotate, Wheel - zoom"
        ]
        
        # Отрисовываем каждую строку
        for i, line in enumerate(camera_info):
            self.draw_text_2d(line, 10, 30 + i * 30)


    def draw_axes(self, length=1000):
        """Отрисовка осей координат"""
        glBegin(GL_LINES)
        # Ось X (красная)
        glColor3f(1, 0, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(length, 0, 0)
        # Ось Y (зелёная)
        glColor3f(0, 1, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, length, 0)
        # Ось Z (синяя)
        glColor3f(0, 0, 1)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, length)
        glEnd()
        
        # Подписи осей
        self.draw_text("X", length+20, 0, 0, (1,0,0))
        self.draw_text("Y", 0, length+20, 0, (0,1,0))
        self.draw_text("Z", 0, 0, length+20, (0,0,1))
    
    def generate_test_prisms(self):
        """Создаем тестовые призмы для демонстрации"""
        return [
            # ((x, y, z), (width, height, depth), (r, g, b, a)),
            ((0, -100, 0), (6000, 10, 7000), (0.2, 0.5, 0.8, 0.8)),  # Море

            ((342, 0, 2384), (336, 15, 377), (1, 0, 0, 1)),  
            ((622, 0, 2153), (380, 15, 434), (1, 0, 0, 1))  ,

            ((605, 126, 2351), (222, 261, 482), (1, 0, 0, 1)),  
            # ((605, 2351, 126), (222, 261, 482), (1, 0, 0, 1))  
        ]
    
    def handle_events(self):
        """Обновленная обработка событий с отслеживанием позиции камеры"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Левая кнопка
                    self.mouse_dragging = True
                    self.last_mouse_pos = event.pos
                elif event.button == 4:  # Колесо вверх
                    self.zoom += 50
                    self.camera_pos[2] += 50
                elif event.button == 5:  # Колесо вниз
                    self.zoom -= 50
                    self.camera_pos[2] -= 50
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.mouse_dragging = False
            
            elif event.type == pygame.MOUSEMOTION:
                if self.mouse_dragging:
                    x, y = event.pos
                    dx, dy = x - self.last_mouse_pos[0], y - self.last_mouse_pos[1]
                    self.last_mouse_pos = (x, y)
                    self.rotate_x += dy * 0.5
                    self.rotate_y += dx * 0.5
        
        return True
    
    def render(self, prisms_data):
        """Основная функция рендеринга"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0, 0, self.zoom)
        glRotatef(self.rotate_x, 1, 0, 0)
        glRotatef(self.rotate_y, 0, 1, 0)

        # Отрисовка осей координат
        self.draw_axes(1500)  # Длина осей 500 единиц
        
        # Отрисовка призм
        for center, size, color in prisms_data:
            vertices = self.generate_prism_vertices(center, *size)
            self.draw_prism(vertices, color)
        
        # Отрисовка HUD
        self.draw_hud()
        
        pygame.display.flip()
        pygame.time.wait(10)
    
    def run(self):
        """Главный цикл приложения"""
        prisms_data = self.generate_test_prisms()
        
        clock = pygame.time.Clock()
        running = True
        while running:
            running = self.handle_events()
            self.render(prisms_data)
            clock.tick(60)
        
        pygame.quit()