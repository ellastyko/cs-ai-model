import sys
from PyQt5.QtWidgets import QApplication
from ui.window import MainWindow

if __name__ == "__main__":
    print(sys.argv[1])
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())