from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import sys

class TabButtonLayout(QWidget):
    def __init__(self):
        super().__init__()

        # Font setup
        font = QFont()
        font.setPointSize(10)

        # Create labels
        label1 = QLabel("Temperature: 33.1°C")
        label2 = QLabel("Humidity: 33.1%")
        label3 = QLabel("CO2: 33.1 PPM")
        label4 = QLabel("Water Percentage: 33.1%")
        label5 = QLabel("Water Level: 5")

        for label in [label1, label2, label3, label4, label5]:
            label.setFont(font)
            label.setAlignment(Qt.AlignCenter)

        # Arrange labels in cross shape
        grid = QGridLayout()
        grid.addWidget(label1, 0, 0)
        grid.addWidget(label2, 0, 2)
        grid.addWidget(label3, 1, 1)
        grid.addWidget(label4, 2, 0)
        grid.addWidget(label5, 2, 2)

        # Create two buttons (like tabs)
        button1 = QPushButton("Home")
        button2 = QPushButton("Logs")

        button1.setFont(QFont("Arial", 13))
        button2.setFont(QFont("Arial", 13))

        button1.setMinimumHeight(50)
        button2.setMinimumHeight(50)

        # Layout for the buttons at bottom
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(button1)
        bottom_layout.addWidget(button2)

        # Combine everything in a vertical layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(grid)
        main_layout.addStretch(1)  # Push buttons to bottom
        main_layout.addLayout(bottom_layout)

        self.setLayout(main_layout)
        self.setWindowTitle("Mushapp")
        self.showFullScreen()

    # Allow closing with ESC key
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TabButtonLayout()
    sys.exit(app.exec_())
