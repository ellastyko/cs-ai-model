from PyQt5.QtWidgets import QMainWindow, QHBoxLayout, QWidget
from ui.widgets import GLWidget, InfoWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FARM AI")
        self.setStyleSheet("background-color: #212121;")
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout()
        central_widget.setLayout(layout)

        self.glWidget   = GLWidget()
        self.infoWidget  = InfoWidget()
        layout.addWidget(self.glWidget, stretch=7)
        layout.addWidget(self.infoWidget, stretch=3)
