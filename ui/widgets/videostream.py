from pygrabber.dshow_graph import FilterGraph
from utils.win32 import WinHelper
from utils.cv2 import round_to_multiple
from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtCore import QTimer, QRect
from PyQt5.QtGui import QImage, QPainter
from configurator import config
import logging

def get_game_windows_rect():
    try:
        game_window_rect = list(WinHelper.GetWindowRect(config["grabber"]["window_title"], (8, 30, 16, 39)))
    except Exception as e:
        logging.error(f'Cannot grab window rect with name "{config["grabber"]["window_title"]}"')
        logging.error(e)

    return game_window_rect

# === QOpenGLWidget for displaying frames ===
class VideoGLWidget(QOpenGLWidget):
    def __init__(self, grabber):
        super().__init__()
        self.grabber = grabber
        self.frame = None

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30) 
        graph = FilterGraph()

        self.grabber.obs_vc_init(graph.get_input_devices().index(config["grabber"]["obs_vc_device_name"]))

        self.game_window_rect = get_game_windows_rect()

        # assure that width & height of capture area is multiple of 32
        if (int(self.game_window_rect[2]) % 32 != 0 or int(self.game_window_rect[3]) % 32 != 0):
            print("Width and/or Height of capture area must be multiply of 32")
            print("Width is", int(self.game_window_rect[2]), ", closest multiple of 32 is", round_to_multiple(int(self.game_window_rect[2]), 32))
            print("Height is", int(self.game_window_rect[3]), ", closest multiple of 32 is", round_to_multiple(int(self.game_window_rect[3]), 32))

            self.game_window_rect[2] = round_to_multiple(int(self.game_window_rect[2]), 32)
            self.game_window_rect[3] = round_to_multiple(int(self.game_window_rect[3]), 32)
            print("Width & Height was updated accordingly")

    def update_frame(self):
        self.frame = self.grabber.get_frame({
            "left": int(self.game_window_rect[0]),
            "top": int(self.game_window_rect[1]), 
            "width": int(self.game_window_rect[2]), 
            "height": int(self.game_window_rect[3])
        })

        if self.frame is None:
            return

        # === PLACE FOR NEURAL NETWORK PROCESSING ===
        # frame = self.run_neural_network(frame)

        self.update()

    def paintGL(self):
        if self.frame is not None:
            widget_width = self.width()
            widget_height = self.height()

            h, w, _ = self.frame.shape
            img = QImage(self.frame.data, w, h, QImage.Format_RGB888)

            # Вычисление масштаба с сохранением пропорций
            scale = min(widget_width / w, widget_height / h)
            scaled_width = int(w * scale)
            scaled_height = int(h * scale)

            # Центрирование
            x = (widget_width - scaled_width) // 2
            y = (widget_height - scaled_height) // 2

            # Отрисовка изображения
            painter = QPainter(self)
            painter.drawImage(
                QRect(x, y, scaled_width, scaled_height),
                img.scaled(scaled_width, scaled_height, aspectRatioMode=1) 
            )
            painter.end()

    def run_neural_network(self, frame):
        # TODO: вставь сюда свою обработку нейросетью (OpenCV, Torch, TensorFlow и т.д.)
        return frame

    def closeEvent(self, event):
        self.grabber.release()
        super().closeEvent(event)
