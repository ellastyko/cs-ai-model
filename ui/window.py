from PyQt5.QtWidgets import QMainWindow, QHBoxLayout, QWidget
from ui.widgets.sidebar import SidebarWidget
from ui.widgets.main import MainWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FARM AI")
        self.setStyleSheet("background-color: #212121;")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(600, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout()
        central_widget.setLayout(layout)

        self.mainWidget     = MainWidget()
        self.sidebarWidget  = SidebarWidget()
        layout.addWidget(self.mainWidget, stretch=7)
        layout.addWidget(self.sidebarWidget, stretch=3)
