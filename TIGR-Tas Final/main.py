"""main.py — TIGR-Tas v3 with v4 GUI. Entry point."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore    import Qt, QCoreApplication
from PyQt5.QtGui     import QFont

from gui.main_window import MainWindow
from gui.styles      import STYLESHEET


def main():
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps,    True)
    app = QApplication(sys.argv)
    app.setApplicationName("TIGR-Tas Prediction System")
    app.setApplicationVersion("3.0.0")
    app.setStyleSheet(STYLESHEET)
    app.setFont(QFont("Segoe UI", 13))
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
