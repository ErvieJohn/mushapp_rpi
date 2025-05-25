from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QTimer
import sys

class TabButtonLayout(QWidget):
    def __init__(self):
        super().__init__()

        # Font setup
        font = QFont()
        font.setPointSize(13)

        # Create labels
        self.label1 = QLabel("Temperature: <b>33.1°C</b>")
        self.label2 = QLabel("Humidity: <b>33.1%</b>")
        self.label3 = QLabel("CO2: <b>33.1 PPM</b>")
        self.label4 = QLabel("Water Percentage: <b>33.1%</b>")
        self.label5 = QLabel("Water Level: <b>5</b>")

        for label in [self.label1, self.label2, self.label3, self.label4, self.label5]:
            label.setFont(font)
            label.setAlignment(Qt.AlignCenter)

        # Arrange labels in cross shape
        grid = QGridLayout()
        grid.addWidget(self.label1, 0, 0)
        grid.addWidget(self.label2, 0, 2)
        grid.addWidget(self.label3, 1, 1)
        grid.addWidget(self.label4, 2, 0)
        grid.addWidget(self.label5, 2, 2)

        # Create two buttons (like tabs)
        
        
        button1 = QPushButton("Home")
        button2 = QPushButton("Logs")
        
        fontBtn = QFont("Arial", 13)
        fontBtn.setBold(True)
        button1.setFont(fontBtn)
        button2.setFont(fontBtn)

        button1.setIcon(QIcon("images/home.png"))
        button2.setIcon(QIcon("images/logs.png"))

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

        # Create QTimer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)  # Call this every second
        self.timer.start(1000)  # 1000 ms = 1 second

        self.count = 0

    def update(self):
        print("Function called every second: ", self.count)
        self.label1.setText("Temperature: <b>{}</b>".format(self.count))
        self.count += 1

    # Allow closing with ESC key
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TabButtonLayout()
    sys.exit(app.exec_())
