from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, 
    QSizePolicy, QPlainTextEdit, QDialog, QProgressBar, QFrame
)
from PyQt5.QtGui import QFont, QIcon, QPainter, QColor, QBrush, QPen, QMovie, QPixmap
from PyQt5.QtCore import Qt, QTimer, QRectF, pyqtSignal, QRect, QThread, pyqtSignal, QSize

import serial
import time
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import db
import requests # for checking the internet
import logging
from datetime import datetime
import sys
import serial.tools.list_ports

########### Database Connect #############
import pymysql

# Background task executed in separate thread
class WorkerThread(QThread):
    finished = pyqtSignal()
    def __init__(self, sleep_time):
        super().__init__()
        self.sleep_time = sleep_time

    def run(self):
        time.sleep(self.sleep_time)  # Simulate a long-running task
        self.finished.emit()

class SpinnerWithCircle(QLabel):
    def __init__(self, gif_path, size=64, parent=None):
        super().__init__(parent)
        self.size = size
        self.setFixedSize(size, size)

        self.movie = QMovie(gif_path)
        self.movie.setScaledSize(QSize(size, size))
        self.setMovie(self.movie)
        self.setAlignment(Qt.AlignCenter)
        self.movie.start()

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        pen_width = 2
        pen = QPen(Qt.white, pen_width)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate bounding box for circle centered in widget
        offset = pen_width / 2
        diameter = self.size - pen_width
        circle_rect = QRectF(offset, offset, diameter, diameter)
        painter.drawEllipse(circle_rect)

class LoadingOverlay(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFrameShape(QFrame.NoFrame)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        self.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 128);
            }
        """)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        self.spinner_label = SpinnerWithCircle("images/mushloading64.gif", 64)
        layout.addWidget(self.spinner_label)

        self.setLayout(layout)
        self.hide()

    def paintEvent(self, event):
        super().paintEvent(event)
        # Draw circle border
        painter = QPainter(self)
        pen = QPen(Qt.black, 3)  # Green border, 3px thick
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing)
        radius = min(self.width(), self.height()) - 3
        painter.drawEllipse(1, 1, radius, radius)

    def resizeEvent(self, event):
        self.resize(self.parent().size())
        # Center spinner_label explicitly
        self.spinner_label.setGeometry(QRect(
            int((self.width() - 64) / 2),
            int((self.height() - 64) / 2),
            64,
            64
        ))

class MySwitch(QPushButton):
    def __init__(self, parent = None):
        super().__init__(parent)
        print('init')
        self.setCheckable(True)
        self.setMinimumWidth(66)
        self.setMinimumHeight(22)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def paintEvent(self, event):
        label = "ON" if self.isChecked() else "OFF"
        bg_color = Qt.green if self.isChecked() else Qt.red

        radius = 10
        width = 32
        center = self.rect().center()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(center)
        painter.setBrush(QColor(0,0,0))

        pen = QPen(Qt.black)
        pen.setWidth(2)
        painter.setPen(pen)

        painter.drawRoundedRect(QRect(-width, -radius, 2*width, 2*radius), radius, radius)
        painter.setBrush(QBrush(bg_color))
        sw_rect = QRect(-radius, -radius, width + radius, 2*radius)
        if not self.isChecked():
            sw_rect.moveLeft(-width)
        painter.drawRoundedRect(sw_rect, radius, radius)
        painter.drawText(sw_rect, Qt.AlignCenter, label)

class TabButtonLayout(QWidget):
    def __init__(self):
        super().__init__()
        
        # INITIATION
        self.bg = QPixmap("images/bg2.png")

        self.loading_overlay = LoadingOverlay(self)
        self.init = True

        self.isHome = True

        # Font setup
        font = QFont()
        font.setPointSize(10)

        # Create labels
        self.label0 = QLabel("<b>HOME</b>")
        self.label1 = QLabel('<b><span style="color:black;">Temperature: 0°C</span></b>')
        self.label2 = QLabel('<b><span style="color:black;">Humidity: 0%</span></b>')
        self.label3 = QLabel('<b><span style="color:black;">CO2: 0 PPM</span></b>')
        self.label4 = QLabel('<b><span style="color:black;">Water Percentage: 0%</span></b>')
        self.label5 = QLabel('<b><span style="color:black;">Water Level: 0</span></b>')

        self.label6 = QLabel('<b><span style="color:black;">Automatic: </span></b>')
        self.label7 = QLabel('<b><span style="color:black;">Fan: </span></b>')
        self.label8 = QLabel('<b><span style="color:black;">Fan2: </span></b>')
        self.label9 = QLabel('<b><span style="color:black;">Heater: </span></b>')
        self.label10 = QLabel('<b><span style="color:black;">Humidifier: </span></b>')
        self.label11 = QLabel('<b><span style="color:black;">Peltier: </span></b>')
        self.label12 = QLabel('<b><span style="color:black;">Water Pump: </span></b>')

        # self.loading = QLabel("Initializing...")
        # fontLoading = QFont()
        # fontLoading.setPointSize(16)
        # self.loading.setFont(fontLoading)
        # self.loading.setAlignment(Qt.AlignCenter)

        self.label0.setFont(QFont("", 16))
        self.label0.setAlignment(Qt.AlignLeft)

        self.labels = [self.label1, self.label2, self.label4,  self.label3, self.label5]
        
        # self.label7, self.label8, self.label9, self.label10, self.label11, self.label12
        for label in self.labels:
            #label.setFont(font)
            #label.setAlignment(Qt.AlignLeft)
            #label.setMaximumWidth(130)
            #label.setMinimumWidth(130)
            label.hide()

        self.switchLabels = [self.label7, self.label8, self.label9, self.label10, self.label11, self.label12]

        for label in self.switchLabels:
            # label.setFont(font)
            label.setAlignment(Qt.AlignLeft)
            label.hide()

        # Switch Button
        
        self.switch1 = MySwitch()
        self.switch1.setChecked(True)
        self.switch1.toggled.connect(self.clicked_auto)
        self.switch2 = MySwitch()
        self.switch2.toggled.connect(self.clicked_fan1)
        self.switch3 = MySwitch()
        self.switch3.toggled.connect(self.clicked_fan2)
        self.switch4 = MySwitch()
        self.switch4.toggled.connect(self.clicked_heater)
        self.switch5 = MySwitch()
        self.switch5.toggled.connect(self.clicked_humid)
        self.switch6 = MySwitch()
        self.switch6.toggled.connect(self.clicked_peltier)
        self.switch7 = MySwitch()
        self.switch7.toggled.connect(self.clicked_waterPump)

        for switch in [self.switch2, self.switch3, self.switch4, self.switch5, self.switch6, self.switch7]:
            switch.setChecked(False)
            switch.hide()

        # Arrange labels in cross shape
        self.grid = QGridLayout()

        #self.grid.addWidget(self.label6, 1, 1)
        #self.grid.addWidget(self.switch1, 1, 2, Qt.AlignLeft)

        #self.grid.addWidget(self.label7, 2, 0)
        #self.grid.addWidget(self.switch2, 2, 1, Qt.AlignLeft)
        #self.grid.addWidget(self.label8, 2, 2)
        #self.grid.addWidget(self.switch3, 2, 3, Qt.AlignLeft)
        
        # self.grid.addWidget(self.label9, 3, 0)
        # self.grid.addWidget(self.switch4, 3, 1, Qt.AlignLeft)
        # self.grid.addWidget(self.label10, 3, 2)
        # self.grid.addWidget(self.switch5, 3, 3, Qt.AlignLeft)

        # self.grid.addWidget(self.label11, 4, 0)
        # self.grid.addWidget(self.switch6, 4, 1, Qt.AlignLeft)
        # self.grid.addWidget(self.label12, 4, 2)
        # self.grid.addWidget(self.switch7, 4, 3, Qt.AlignLeft)
        
        # FOR VALUES
        self.grid.addWidget(self.label1, 6, 0)
        self.grid.addWidget(self.label2, 6, 2, Qt.AlignLeft)
        self.grid.addWidget(self.label3, 7, 1)
        self.grid.addWidget(self.label4, 8, 0, Qt.AlignLeft)
        self.grid.addWidget(self.label5, 8, 2)
        # self.grid.addWidget(self.loading, 7, 1, Qt.AlignLeft)

        # Create two buttons (like tabs)
        self.button1 = QPushButton("Home")
        self.button1.setDisabled(True)
        self.button2 = QPushButton("Logs")

        self.button1.setStyleSheet("""
            QPushButton {
                background-color: lightgray;
                color: black;
                border: 1px solid #ccc;
                padding: 5px;
            }
            QPushButton:pressed {
                background-color: #a3d2ca;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                color: #888;
                border: 1px solid #aaa;
            }
        """)

        self.button2.setStyleSheet("""
            QPushButton {
                background-color: lightgray;
                color: black;
                border: 1px solid #ccc;
                padding: 5px;
            }
            QPushButton:pressed {
                background-color: #a3d2ca;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                color: #888;
                border: 1px solid #aaa;
            }
        """)

        self.button1.clicked.connect(self.clicked_home)
        self.button2.clicked.connect(self.clicked_logs)

        self.button1.setChecked(True)

        fontBtn = QFont("Arial", 13)
        fontBtn.setBold(True)
        self.button1.setFont(fontBtn)
        self.button2.setFont(fontBtn)

        self.button1.setIcon(QIcon("images/home.png"))
        self.button2.setIcon(QIcon("images/logs.png"))

        self.button1.setMinimumHeight(50)
        self.button2.setMinimumHeight(50)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.label0)

        autoLayout = QHBoxLayout()
        autoLayout.addWidget(self.label6)
        autoLayout.addWidget(self.switch1)
        autoLayout.setAlignment(Qt.AlignHCenter)

        # Left column: label7 + switch2, label9 + switch4, label11 + switch6
        leftColumnLayout = QVBoxLayout()
        leftColumnLayout.addLayout(self._makeSwitchRow(self.label7, self.switch2))
        leftColumnLayout.addLayout(self._makeSwitchRow(self.label9, self.switch4))
        leftColumnLayout.addLayout(self._makeSwitchRow(self.label11, self.switch6))

        # Right column: label8 + switch3, label10 + switch5, label12 + switch7
        rightColumnLayout = QVBoxLayout()
        rightColumnLayout.addLayout(self._makeSwitchRow(self.label8, self.switch3))
        rightColumnLayout.addLayout(self._makeSwitchRow(self.label10, self.switch5))
        rightColumnLayout.addLayout(self._makeSwitchRow(self.label12, self.switch7))

        # Main layout: horizontal, holds both columns
        switchesLayout = QHBoxLayout()
        switchesLayout.addStretch(1)
        switchesLayout.addLayout(leftColumnLayout)
        switchesLayout.addStretch(1)
        switchesLayout.addLayout(rightColumnLayout)
        switchesLayout.addStretch(1)

        # Layout for the buttons at bottom
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.button1)
        bottom_layout.addWidget(self.button2)

        self.button1.show()
        self.button2.show()

        self.logLayout = QVBoxLayout()
        self.log_display = QPlainTextEdit()
        self.log_display.setReadOnly(True)
        self.logLayout.addWidget(self.log_display)
        self.log_display.hide()

        # Combine everything in a vertical layout
        self.main_layout = QVBoxLayout()
        self.main_layout.addLayout(top_layout)
        self.main_layout.addLayout(autoLayout)
        self.main_layout.addLayout(switchesLayout)
        self.main_layout.addLayout(self.grid)
        self.main_layout.addLayout(self.logLayout)
        self.main_layout.addStretch(1)  # Push buttons to bottom
        self.main_layout.addLayout(bottom_layout)

        self.setLayout(self.main_layout)
        self.setWindowTitle("Mushapp")
        self.setMaximumWidth(480)
        self.setMinimumWidth(480)
        self.showFullScreen()

        for i in range(self.logLayout.count()):
            item = self.logLayout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.hide()

        for i in range(self.grid.count()):
            item = self.grid.itemAt(i)
            widget = item.widget()
            if widget:
                widget.show()

        if self.switch1.isChecked():
            for switch in [self.switch2, self.switch3, self.switch4, self.switch5, self.switch6, self.switch7]:
                switch.setChecked(False)
                switch.hide()

            for label in self.switchLabels:
                label.hide()

        else:
            for switch in [self.switch2, self.switch3, self.switch4, self.switch5, self.switch6, self.switch7]:
                switch.setChecked(False)
                switch.show()

            for label in self.switchLabels:
                label.show()

        self.start_loading(4)
        self.initializing()
        
        # if not self.init:
        #     self.loading.hide()
        #     for label in self.labels:
        #         label.show()
        
        self.count = 0
        try:
            # Create QTimer
            self.timer = QTimer()
            self.timer.timeout.connect(self.update)  # Call this every second
            self.timer.start(1000)  # 1000 ms = 1 second

        except KeyboardInterrupt:
            # Close the serial port when the program is terminated
            self.ser.close()

            # database close connection
            self.cursor.close()
            self.connection.close()

    def initializing(self):
        self.connection = pymysql.connect(
            host="localhost",         # Replace with your host, e.g., "127.0.0.1" or server IP
            user="admin",     # Replace with your MariaDB username
            password="admin", # Replace with your MariaDB password
            database="mushapp_db", # Replace with your database name
            charset="utf8mb4",        # Character set for encoding
            cursorclass=pymysql.cursors.DictCursor  # Optional: Use dictionary cursor for better usability
        )

        self.cursor = self.connection.cursor()
        ##########################################

        self.last_pos = 0
        self.LOG_FILENAME = datetime.now().strftime('/home/admin/Desktop/main/logs/%d_%m_%Y_logfile.log') # %H_%M_%S_logfile.log')
        self.MAX_LINES = 500

        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        #logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)
        logging.basicConfig(filename=self.LOG_FILENAME,level=logging.INFO)
        logging.info('Forecasting Job Started...')
        logging.debug('mushapp method started...')

        self.check_internet()

        ########## Finding Serial Port ##############
        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Connecting to Arduino Serial Port...'))
        print("Connecting to Arduino Serial Port...")

        self.known_ports = set(self.list_serial_ports())

        self.serial_port = self.find_available_port()
        while self.serial_port is None:
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Error: No Serial Port Available.'))
            print("Error: No Serial Port Available.")
            sys.exit("No Serial Port Available.")

            # Wait for a moment
            time.sleep(1)

            self.serial_port = self.find_available_port()

        # Define the baud rate
        self.baud_rate = 9600

        # Open the serial port
        self.ser = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
        self.arduino_connected = True

        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Connected to Arduino Serial Port.'))
        print("Done.")
        ########## END Of Finding Serial Port ##############

        self.cred = credentials.Certificate("/home/admin/Desktop/main/key.json")
        self.initialized = False

        try:
            # Initial Value
            self.oldFanState = False
            self.oldHeaterState = False

            self.oldFan2State = False
            self.oldHumidifierState = False

            self.oldWaterPumpState = False

            self.oldAutoState = True

            self.oldPeltierState = False

            if self.check_internet():
                self.ref = self.connectToFirebase()

                # Get the data
                self.oldData = self.ref.get()
                self.oldFanState = self.oldData["fan"]
                self.oldHeaterState = self.oldData["heater"]

                self.oldFan2State = self.oldData["fan2"]
                self.oldHumidifierState = self.oldData["humidifier"]

                self.oldWaterPumpState = self.oldData["waterPump"]

                #oldAutoState = oldData["auto"]
                self.oldAutoState = True

                self.oldPeltierState = self.oldData["peltier"]

            self.oldDateTime = datetime.now()

            # First Run change current state
            # Change arduino relay fan state
            if(self.oldFanState):
                # Fan ON
                self.ser.write(("fanH" + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON FAN.'))
                # print("turning on FAN!")

                self.switch2.setChecked(True)
            else:
                # Fan OFF
                self.ser.write(("fanL" + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF FAN.'))
                self.switch2.setChecked(False)

            # Change arduino relay heater state
            if(self.oldHeaterState):
                # Heater ON
                self.ser.write(('heaterH' + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON HEATER.'))
                self.switch4.setChecked(True)
            else:
                # Heater OFF
                self.ser.write(('heaterL' + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF HEATER.'))
                self.switch4.setChecked(False)

            if(self.oldFan2State):
                # Fan ON
                self.ser.write(("fan2H" + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON FAN2.'))
                # print("turning on FAN!")
                self.switch3.setChecked(True)
            else:
                # Fan OFF
                self.ser.write(("fan2L" + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF FAN2.'))
                self.switch3.setChecked(False)

            # Change arduino relay heater state
            if(self.oldHumidifierState):
                # Heater ON
                self.ser.write(('humidifierH' + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON HUMIDIFIER.'))
                self.switch5.setChecked(True)
            else:
                # Heater OFF
                self.ser.write(('humidifierL' + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF HUMIDIFIER.'))
                self.switch5.setChecked(False)

            # Change arduino relay heater state
            if(self.oldAutoState):
                # Heater ON
                self.ser.write(('auto' + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON AUTOMATIC.'))

                try:
                    self.ref.update({'auto': True})
                except Exception as e:
                    # Handle the error (you can log it or take alternative actions)
                    print(f"Failed to update Firebase: {str(e)}")

                self.switch1.setChecked(True)

                for switch in [self.switch2, self.switch3, self.switch4, self.switch5, self.switch6, self.switch7]:
                    switch.setChecked(False)
                    switch.hide()

                for label in self.switchLabels:
                    label.hide()
            else:
                # Heater OFF
                self.ser.write(('manual' + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF AUTOMATIC.'))
                self.switch1.setChecked(False)

                for switch in [self.switch2, self.switch3, self.switch4, self.switch5, self.switch6, self.switch7]:
                    switch.setChecked(False)
                    switch.show()

                for label in self.switchLabels:
                    label.show()

            if(self.oldWaterPumpState):
                # Fan ON
                self.ser.write(("waterPumpH" + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON WATER PUMP.'))
                # print("turning on FAN!")
                self.switch7.setChecked(True)
                
            else:
                # Fan OFF
                self.ser.write(("waterPumpL" + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF WATER PUMP.'))
                self.switch7.setChecked(False)

            if(self.oldPeltierState):
                # Fan ON
                self.ser.write(("peltierH" + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON PELTIER.'))
                # print("turning on FAN!")
                self.switch6.setChecked(True)

            else:
                # Fan OFF
                self.ser.write(("peltierL" + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF PELTIER.'))
                self.switch6.setChecked(False)
            
            self.init = False

        except KeyboardInterrupt:
            # Close the serial port when the program is terminated
            self.ser.close()

            # database close connection
            self.cursor.close()
            self.connection.close()

    def update(self):
        # print("Function called every second: ", self.count)
        # self.label1.setText("Temperature: <b>{}</b>".format(self.count))
        # self.count += 1

        # for detection of plugged/unplugged arduino port
        self.current_ports = set(self.list_serial_ports())
        
        # Detect new ports
        self.new_ports = self.current_ports - self.known_ports
        for port in self.new_ports:
            self.serial_port = self.find_available_port()
            while self.serial_port is None:
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Error: No Serial Port Available.'))
                print("Error: No Serial Port Available.")
                sys.exit("No Serial Port Available.")

                # Wait for a moment
                time.sleep(1)

                self.serial_port = self.find_available_port()
            #if (serial_port is None):

            # Define the baud rate
            self.baud_rate = 9600

            # Open the serial port
            self.ser = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
            self.arduino_connected = True
            
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Arduino plugged in: {port}.'))
            print(f"Arduino plugged in: {port}")
            
            self.ser.write(("auto" + '\n').encode())
            try:
                self.ref.update({'auto': True})

            except Exception as e:
                # Handle the error (you can log it or take alternative actions)
                print(f"Failed to update Firebase: {str(e)}")
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON AUTOMATIC.'))
            for switch in [self.switch2, self.switch3, self.switch4, self.switch5, self.switch6, self.switch7]:
                switch.setChecked(False)
                switch.hide()

            for label in self.switchLabels:
                label.hide()

        # Detect removed ports
        self.removed_ports = self.known_ports - self.current_ports
        for port in self.removed_ports:
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Arduino unplugged: {port}.'))
            print(f"Arduino unplugged: {port}")
            
            self.serial_port = None
            self.arduino_connected = False
            self.ser.close()
            
        self.known_ports = self.current_ports

        if self.arduino_connected:
            #try:
            if self.check_internet():
                ref = self.connectToFirebase()

                # Get the data
                self.currData = self.ref.get()
                self.currFanState = self.currData["fan"]
                self.currHeaterState = self.currData["heater"]

                self.currFan2State = self.currData["fan2"]
                self.currHumidifierState = self.currData["humidifier"]

                self.currWaterPumpState = self.currData["waterPump"]

                self.currAutoState = self.currData["auto"]

                self.currPeltierState = self.currData["peltier"]

                if(self.currFanState != self.oldFanState):
                    # update state
                    self.oldFanState = self.currFanState

                    print("Fan state changed: ", self.currFanState)

                    # Change arduino relay fan state
                    if(self.currFanState):
                        # Fan ON
                        self.ser.write(("fanH" + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON FAN.'))
                        # print("turning on FAN!")
                        self.switch2.setChecked(True)
                    else:
                        # Fan OFF
                        self.ser.write(("fanL" + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF FAN.'))
                        # print("turning off FAN!")
                        self.switch2.setChecked(False)

                if(self.currHeaterState != self.oldHeaterState):
                    # update state
                    self.oldHeaterState = self.currHeaterState

                    print("Heater state changed: ", self.currHeaterState)

                    # Change arduino relay heater state
                    if(self.currHeaterState):
                        # Heater ON
                        self.ser.write(('heaterH' + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON HEATER.'))
                        self.switch4.setChecked(True)
                    else:
                        # Heater OFF
                        self.ser.write(('heaterL' + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF HEATER.'))
                        self.switch4.setChecked(False)

                if(self.currFan2State != self.oldFan2State):
                    # update state
                    self.oldFan2State = self.currFan2State

                    print("Fan2 state changed: ", self.currFan2State)

                    # Change arduino relay fan state
                    if(self.currFan2State):
                        # Fan ON
                        self.ser.write(("fan2H" + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON FAN2.'))
                        # print("turning on FAN!")
                        self.switch3.setChecked(True)
                    else:
                        # Fan OFF
                        self.ser.write(("fan2L" + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF FAN2.'))
                        # print("turning off FAN!")
                        self.switch3.setChecked(False)

                if(self.currHumidifierState != self.oldHumidifierState):
                    # update state
                    self.oldHumidifierState = self.currHumidifierState

                    print("Humidifier state changed: ", self.currHumidifierState)

                    # Change arduino relay heater state
                    if(self.currHumidifierState):
                        # Humidifier ON
                        self.ser.write(('humidifierH' + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON HUMIDIFIER.'))
                        self.switch5.setChecked(True)
                    else:
                        # Humidifier OFF
                        self.ser.write(('humidifierL' + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF HUMIDIFIER.'))
                        self.switch5.setChecked(False)

                if(self.currAutoState != self.oldAutoState):
                    # update state
                    self.oldAutoState = self.currAutoState

                    print("Auto state changed: ", self.currAutoState)

                    # Change arduino relay fan state
                    if(self.currAutoState):
                        # Auto ON
                        self.ser.write(("auto" + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON AUTOMATIC.'))
                        # print("turning on FAN!")
                        self.switch1.setChecked(True)
                        for switch in [self.switch2, self.switch3, self.switch4, self.switch5, self.switch6, self.switch7]:
                            switch.setChecked(False)
                            switch.hide()

                        for label in self.switchLabels:
                            label.hide()
                    else:
                        # Auto OFF
                        self.ser.write(("manual" + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF AUTOMATIC.'))
                        # print("turning off FAN!")
                        self.switch1.setChecked(False)
                        for switch in [self.switch2, self.switch3, self.switch4, self.switch5, self.switch6, self.switch7]:
                            switch.setChecked(False)
                            switch.hide()

                        for label in self.switchLabels:
                            label.hide()

                if(self.currWaterPumpState != self.oldWaterPumpState):
                    # update state
                    self.oldWaterPumpState = self.currWaterPumpState

                    print("Water Pump state changed: ", self.currWaterPumpState)

                    # Change arduino relay fan state
                    if(self.currWaterPumpState):
                        # Fan ON
                        self.ser.write(("waterPumpH" + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON WATER PUMP.'))
                        # print("turning on FAN!")
                        self.switch7.setChecked(True)
                    else:
                        # Fan OFF
                        self.ser.write(("waterPumpL" + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning WATER PUMP.'))
                        # print("turning off FAN!")
                        self.switch7.setChecked(False)

                if(self.currPeltierState != self.oldPeltierState):
                    # update state
                    self.oldPeltierState = self.currPeltierState

                    print("Peltier state changed: ", self.currPeltierState)

                    # Change arduino relay fan state
                    if(self.currPeltierState):
                        # Fan ON
                        self.ser.write(("peltierH" + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON PELTIER.'))
                        # print("turning on FAN!")
                        self.switch6.setChecked(True)
                    else:
                        # Fan OFF
                        self.ser.write(("peltierL" + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF PELTIERN.'))
                        # print("turning off FAN!")
                        self.switch6.setChecked(False)

            # Read a line of data from the serial port
            try:
                self.data = self.ser.readline().decode('utf-8', errors='ignore').strip()
                
                if(self.data[slice(10)] == "JSON data:"):
                    try:
                        self.jsonData = json.loads(self.data[10:None])
                    except Exception as e:
                        logging.error(datetime.now().strftime('%m-%d-%Y %H:%M:%S Unexpected error: {str(e)}'))
                        print(f"Unexpected error: {str(e)}")
                        self.jsonData = {"temperature": 0, "humidity": 0, "waterLevel": 0, "co2ppm": 0}

                    logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Data Collected: {data}'.format(data=self.jsonData)))
                    print(self.jsonData)

                    # update the firebase realtime database
                    # update the temp
                    logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Sending data to firebase realtime database...'))
                    print("Sending data to firebase realtime database...")

                    fTemp = float(self.jsonData["temperature"])
                    iHumid = int(self.jsonData["humidity"])
                    iCo2 = int(self.jsonData["co2ppm"])
                    iWater = int(self.jsonData["waterLevel"])
                    fWater = self.jsonData["waterLevel"]/19 * 100

                    self.label1.setText('<b><span style="color:black;">Temperature: </span><span style="color:{};">{}°C</span></b>'.format(
                        "green" if fTemp >= 20 and fTemp <= 30 
                        else "orange" if fTemp <= 19 else "red", self.jsonData["temperature"]))
                    self.label2.setText('<b><span style="color:black;">Humidity: </span><span style="color:{};">{} %</span></b>'.format(
                        "green" if  iHumid >= 70 and iHumid <=85 else "red", self.jsonData["humidity"]))
                    self.label3.setText('<b><span style="color:black;">CO2: </span><span style="color:{};">{} PPM</span></b>'.format(
                        "green" if iCo2 >= 400 and iCo2 <= 1000 else "red", self.jsonData["co2ppm"]))
                    self.label4.setText('<b><span style="color:black;">Water Percentage: </span><span style="color:{};">{:.1f} %</span></b>'.format(
                        "red" if fWater < 1 or fWater > 100 else "green", fWater))
                    self.label5.setText('<b><span style="color:black;">Water Level: </span><span style="color:{};">{}</span></b>'.format(
                        "red" if iWater == 0 or iWater >= 20 else "green", self.jsonData["waterLevel"]))

                    if self.check_internet(): # if there is an internet connection
                        try:
                            self.ref.update({"temp":self.jsonData["temperature"]})
                            self.ref.update({"humid":self.jsonData["humidity"]})
                            self.ref.update({"water":self.jsonData["waterLevel"]})
                            self.ref.update({"co2":self.jsonData["co2ppm"]})

                            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Data has been sent to firebase realtime database.'))
                            print("Data has been sent to firebase realtime database.")

                        except Exception as e:
                            # Handle the error (you can log it or take alternative actions)
                            print(f"Failed to update Firebase: {str(e)}")


                    else:
                        logging.error(datetime.now().strftime('%m-%d-%Y %H:%M:%S No Internet Connection. Can\'t send the data to irebase realtime database.'))
                        print("No Internet Connection. Can\'t send the data to irebase realtime database.")

                        # Wait for a moment
                        # time.sleep(1)
                    ###### Saving to local database #######
                    self.timeDiff = datetime.now() - self.oldDateTime

                    # saved only per minute
                    if(self.timeDiff.total_seconds() > 60):
                        self.insert_query = """
                            INSERT INTO data (co2, humidity, temperature, water_lvl)
                            VALUES (%s, %s, %s, %s)
                        """
                        data = (self.jsonData["co2ppm"], self.jsonData["humidity"], self.jsonData["temperature"], self.jsonData["waterLevel"])

                        try:
                            self.cursor.execute(self.insert_query, data)
                            self.connection.commit()  # Commit changes to the database
                            # print(f"Inserted {cursor.rowcount} row(s) successfully.")

                            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Data has been saved to local database.'))
                            print("Data has been saved to local database.")

                            self.oldDateTime = datetime.now()

                        except pymysql.MySQLError as err:
                            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Database Error: {err}'))
                            print(f"Database Error: {err}")
                    ####################################

                else:
                    logging.error(datetime.now().strftime('%m-%d-%Y %H:%M:%S Error: {data}'.format(data=self.data)))
                    print("Error:", self.data)
            except serial.serialutil.SerialException as e:
                print(f"SerialException caught: {e}")
                # You might want to mark Arduino as disconnected here
                #arduino_connected = False
                self.ser.close()

            try:
                with open(self.LOG_FILENAME, "r") as f:
                    f.seek(self.last_pos)
                    new_data = f.read()
                    self.last_pos = f.tell()

                if new_data:
                    # Append and limit to last MAX_LINES
                    current_text = self.log_display.toPlainText().splitlines()
                    new_lines = new_data.splitlines()
                    all_lines = current_text + new_lines
                    all_lines = all_lines[-self.MAX_LINES:]

                    self.log_display.setPlainText("\n".join(all_lines))
                    self.log_display.verticalScrollBar().setValue(
                        self.log_display.verticalScrollBar().maximum()
                    )
            except Exception as e:
                # Optionally print/log the error, but don't crash the app
                print(f"Error reading log file: {e}")
                return

    def connectToFirebase(self):
        ########## Checking Firebase ##############
        if(not self.initialized):
            try:
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Connecting to Firebase Realtime Database...'))
                print("Connecting to Firebase Realtime Database...")

                # Initialize Firebase Admin SDK with your service account credentials
                firebase_admin.initialize_app(self.cred, {
                    'databaseURL': 'https://mushapp-c0311-default-rtdb.firebaseio.com/'
                })
                self.initialized = True

                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Connected to Firebase Realtime Database.'))
                print("Done.")
            except Exception as e:
                print(f"Unexpected error: {str(e)}")
        # Reference to the specific path in the Firebase Realtime Database

        return db.reference('/')
        ########## Checking Firebase ##############

    def find_available_port(self):
        # List all available ports
        serial_port = list(serial.tools.list_ports.comports())
        for port in serial_port:
            # You can add criteria to select a specific port if needed
            print(f"Found port: {port.device}")
            return port.device
        return None

    def list_serial_ports(self):
        return [port.device for port in serial.tools.list_ports.comports()]

    def check_internet(self):
        try:
            requests.get("https://www.google.com")
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Connected to Internet.'))
            return True
        except requests.ConnectionError:
            logging.error(datetime.now().strftime('%m-%d-%Y %H:%M:%S Error Connecting to Internet.'))
            return False

    def clicked_auto(self):
        self.start_loading()

        if self.switch1.isChecked():
            for switch in [self.switch2, self.switch3, self.switch4, self.switch5, self.switch6, self.switch7]:
                switch.setChecked(False)
                switch.hide()

            for label in self.switchLabels:
                label.hide()

            self.ser.write(('auto' + '\n').encode())
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON AUTOMATIC.'))

        else:
            for switch in [self.switch2, self.switch3, self.switch4, self.switch5, self.switch6, self.switch7]:
                switch.setChecked(False)
                switch.show()

            for label in self.switchLabels:
                label.show()

            self.ser.write(('manual' + '\n').encode())
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF AUTOMATIC.'))
        
        self.oldAutoState = self.switch1.isChecked()
        self.currAutoState = self.switch1.isChecked()

        if self.check_internet(): # if there is an internet connection
            try:
                self.ref.update({"auto": self.switch1.isChecked()})
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Data has been sent to firebase realtime database.'))
                print("Data has been sent to firebase realtime database.")

            except Exception as e:
                # Handle the error (you can log it or take alternative actions)
                logging.info(datetime.now().strftime(f'%m-%d-%Y %H:%M:%S Failed to update Firebase: {str(e)}'))
                print(f"Failed to update Firebase: {str(e)}")

        # self.switch1.setChecked(not self.switch1.isChecked())

    def clicked_fan1(self):
        self.start_loading()
        # Change arduino relay fan state
        if(self.switch2.isChecked()):
            # Fan ON
            self.ser.write(("fanH" + '\n').encode())
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON FAN.'))
            # print("turning on FAN!")
            
        else:
            # Fan OFF
            self.ser.write(("fanL" + '\n').encode())
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF FAN.'))
            # print("turning off FAN!")

        self.oldFanState = self.switch2.isChecked()
        self.currFanState = self.switch2.isChecked()

        if self.check_internet(): # if there is an internet connection
            try:
                self.ref.update({"fan": self.switch2.isChecked()})
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Data has been sent to firebase realtime database.'))
                print("Data has been sent to firebase realtime database.")

            except Exception as e:
                # Handle the error (you can log it or take alternative actions)
                logging.info(datetime.now().strftime(f'%m-%d-%Y %H:%M:%S Failed to update Firebase: {str(e)}'))
                print(f"Failed to update Firebase: {str(e)}")

        # self.switch2.setChecked(not self.switch2.isChecked())

    def clicked_fan2(self):
        self.start_loading()
        if(self.switch3.isChecked()):
            # Fan ON
            self.ser.write(("fan2H" + '\n').encode())
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON FAN2.'))
            # print("turning on FAN!")
            
        else:
            # Fan OFF
            self.ser.write(("fan2L" + '\n').encode())
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF FAN2.'))
            # print("turning off FAN!")

        self.oldFan2State = self.switch3.isChecked()
        self.currFan2State = self.switch3.isChecked()

        if self.check_internet(): # if there is an internet connection
            try:
                self.ref.update({"fan2": self.switch3.isChecked()})
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Data has been sent to firebase realtime database.'))
                print("Data has been sent to firebase realtime database.")

            except Exception as e:
                # Handle the error (you can log it or take alternative actions)
                logging.info(datetime.now().strftime(f'%m-%d-%Y %H:%M:%S Failed to update Firebase: {str(e)}'))
                print(f"Failed to update Firebase: {str(e)}")

        # self.switch3.setChecked(not self.switch3.isChecked())
    
    def clicked_heater(self):
        self.start_loading()
        # Change arduino relay heater state
        if(self.switch4.isChecked()):
            # Heater ON
            self.ser.write(('heaterH' + '\n').encode())
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON HEATER.'))
        else:
            # Heater OFF
            self.ser.write(('heaterL' + '\n').encode())
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF HEATER.'))
  
        self.oldHeaterState = self.switch4.isChecked()
        self.currHeaterState = self.switch4.isChecked()

        if self.check_internet(): # if there is an internet connection
            try:
                self.ref.update({"heater": self.switch4.isChecked()})
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Data has been sent to firebase realtime database.'))
                print("Data has been sent to firebase realtime database.")

            except Exception as e:
                # Handle the error (you can log it or take alternative actions)
                logging.info(datetime.now().strftime(f'%m-%d-%Y %H:%M:%S Failed to update Firebase: {str(e)}'))
                print(f"Failed to update Firebase: {str(e)}")

        # self.switch4.setChecked(not self.switch4.isChecked())

    def clicked_humid(self):
        self.start_loading()
        if(self.switch5.isChecked()):
            # Humidifier ON
            self.ser.write(('humidifierH' + '\n').encode())
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON HUMIDIFIER.'))
        else:
            # Humidifier OFF
            self.ser.write(('humidifierL' + '\n').encode())
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF HUMIDIFIER.'))

        self.oldHumidifierState = self.switch5.isChecked()
        self.currHumidifierState = self.switch5.isChecked()

        if self.check_internet(): # if there is an internet connection
            try:
                self.ref.update({"humidifier": self.switch5.isChecked()})
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Data has been sent to firebase realtime database.'))
                print("Data has been sent to firebase realtime database.")

            except Exception as e:
                # Handle the error (you can log it or take alternative actions)
                logging.info(datetime.now().strftime(f'%m-%d-%Y %H:%M:%S Failed to update Firebase: {str(e)}'))
                print(f"Failed to update Firebase: {str(e)}")

        # self.switch5.setChecked(not self.switch5.isChecked())

    def clicked_peltier(self):
        self.start_loading()
        if(self.switch6.isChecked()):
            # Peltier ON
            self.ser.write(('peltierH' + '\n').encode())
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON PELTIER.'))
        else:
            # Peltier OFF
            self.ser.write(('peltierL' + '\n').encode())
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF PELTIER.'))

        self.oldPeltierState = self.switch6.isChecked()
        self.currPeltierState = self.switch6.isChecked()

        if self.check_internet(): # if there is an internet connection
            try:
                self.ref.update({"peltier": self.switch6.isChecked()})
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Data has been sent to firebase realtime database.'))
                print("Data has been sent to firebase realtime database.")

            except Exception as e:
                # Handle the error (you can log it or take alternative actions)
                logging.info(datetime.now().strftime(f'%m-%d-%Y %H:%M:%S Failed to update Firebase: {str(e)}'))
                print(f"Failed to update Firebase: {str(e)}")

        # self.switch6.setChecked(not self.switch6.isChecked())

    def clicked_waterPump(self):
        self.start_loading()
        if(self.switch7.isChecked()):
            # WATER PUMP ON
            self.ser.write(('waterPumpH' + '\n').encode())
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON WATER PUMP.'))
        else:
            # WATER PUMP OFF
            self.ser.write(('waterPumpL' + '\n').encode())
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF WATER PUMP.'))

        self.oldWaterPumpState = self.switch7.isChecked()
        self.currWaterPumpState = self.switch7.isChecked()

        if self.check_internet(): # if there is an internet connection
            try:
                self.ref.update({"waterPump": self.switch7.isChecked()})
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Data has been sent to firebase realtime database.'))
                print("Data has been sent to firebase realtime database.")

            except Exception as e:
                # Handle the error (you can log it or take alternative actions)
                logging.info(datetime.now().strftime(f'%m-%d-%Y %H:%M:%S Failed to update Firebase: {str(e)}'))
                print(f"Failed to update Firebase: {str(e)}")

        # self.switch7.setChecked(not self.switch7.isChecked())

    def _makeSwitchRow(self, label, switch):
        layout = QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(switch)
        layout.setAlignment(Qt.AlignRight)
        return layout

    def clicked_home(self):
        self.start_loading()
        self.label0.setText("<b>HOME</b>")
        self.button1.setDisabled(True)
        self.button2.setDisabled(False) 

        for i in range(self.logLayout.count()):
            item = self.logLayout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.hide()

        for i in range(self.grid.count()):
            item = self.grid.itemAt(i)
            widget = item.widget()
            if widget:
                widget.show()

        self.switch1.show()
        self.label6.show()
        if self.switch1.isChecked():
            for switch in [self.switch2, self.switch3, self.switch4, self.switch5, self.switch6, self.switch7]:
                switch.setChecked(False)
                switch.hide()

            for label in self.switchLabels:
                label.hide()

        else:
            for switch in [self.switch2, self.switch3, self.switch4, self.switch5, self.switch6, self.switch7]:
                switch.setChecked(False)
                switch.show()

            for label in self.switchLabels:
                label.show()

    def clicked_logs(self):
        self.start_loading()
        self.label0.setText("<b>LOGS</b>")
        self.button2.setDisabled(True)
        self.button1.setDisabled(False)

        for i in range(self.grid.count()):
            item = self.grid.itemAt(i)
            widget = item.widget()
            if widget:
                widget.hide()

        for i in range(self.logLayout.count()):
            item = self.logLayout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.show()

        self.switch1.hide()
        for switch in [self.switch2, self.switch3, self.switch4, self.switch5, self.switch6, self.switch7]:
            switch.setChecked(False)
            switch.hide()

        for label in self.switchLabels + [self.label6]:
            label.hide()
    
    def start_loading(self, time=1):
        self.loading_overlay.resize(self.size())  # Ensure overlay fits window
        self.loading_overlay.show()
        self.loading_overlay.raise_()
        self.loading_overlay.repaint()  # Force immediate repaint

        self.thread = WorkerThread(time)
        self.thread.finished.connect(self.finish_loading)
        self.thread.start()

    def finish_loading(self):
        self.loading_overlay.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.bg)

    # Allow closing with ESC key
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TabButtonLayout()
    sys.exit(app.exec_())
