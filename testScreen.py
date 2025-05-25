import sys
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

class FullScreenApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.FramelessWindowHint |    # No borders
            Qt.WindowStaysOnTopHint |   # Stay above taskbar
            Qt.X11BypassWindowManagerHint  # Bypass window manager to avoid taskbar
        )

        self.showFullScreen()  # Fit screen

        # Example content
        layout = QVBoxLayout()
        label = QLabel("Hello LCD 3.5\" Screen!", self)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FullScreenApp()
    sys.exit(app.exec_())
