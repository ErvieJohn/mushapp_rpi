from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QTimer

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

class TabButtonLayout(QWidget):
    def __init__(self):
        super().__init__()

        # INITIATION
        self.init = True

        # Font setup
        font = QFont()
        font.setPointSize(13)

        # Create labels
        self.label1 = QLabel("Temperature: <b>0°C</b>")
        self.label2 = QLabel("Humidity: <b>0%</b>")
        self.label3 = QLabel("CO2: <b>0 PPM</b>")
        self.label4 = QLabel("Water Percentage: <b>0%</b>")
        self.label5 = QLabel("Water Level: <b>0</b>")

        self.loading = QLabel("Initializing...")
        fontLoading = QFont()
        fontLoading.setPointSize(16)
        self.loading.setFont(fontLoading)
        self.loading.setAlignment(Qt.AlignCenter)
        
        for label in [self.label1, self.label2, self.label3, self.label4, self.label5]:
            label.setFont(font)
            label.setAlignment(Qt.AlignCenter)
            label.hide()

        # Arrange labels in cross shape
        grid = QGridLayout()
        grid.addWidget(self.label1, 0, 0)
        grid.addWidget(self.label2, 0, 2)
        grid.addWidget(self.label3, 1, 1)
        grid.addWidget(self.label4, 2, 0)
        grid.addWidget(self.label5, 2, 2)
        grid.addWidget(self.loading, 3, 1)

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

        self.initializing()

        if not self.init:
            self.loading.hide()
            for label in [self.label1, self.label2, self.label3, self.label4, self.label5]:
                label.show()

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

        self.LOG_FILENAME = datetime.now().strftime('/home/admin/Desktop/main/logs/%d_%m_%Y_logfile.log') # %H_%M_%S_logfile.log')

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
            else:
                # Fan OFF
                self.ser.write(("fanL" + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF FAN.'))

            # Change arduino relay heater state
            if(self.oldHeaterState):
                # Heater ON
                self.ser.write(('heaterH' + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON HEATER.'))
            else:
                # Heater OFF
                self.ser.write(('heaterL' + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF HEATER.'))

            if(self.oldFan2State):
                # Fan ON
                self.ser.write(("fan2H" + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON FAN2.'))
                # print("turning on FAN!")
            else:
                # Fan OFF
                self.ser.write(("fan2L" + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF FAN2.'))

            # Change arduino relay heater state
            if(self.oldHumidifierState):
                # Heater ON
                self.ser.write(('humidifierH' + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON HUMIDIFIER.'))
            else:
                # Heater OFF
                self.ser.write(('humidifierL' + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF HUMIDIFIER.'))

            # Change arduino relay heater state
            if(self.oldAutoState):
                # Heater ON
                self.ser.write(('auto' + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON AUTOMATIC.'))
                self.ref.update({'auto': True})
            else:
                # Heater OFF
                self.ser.write(('manual' + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF AUTOMATIC.'))

            if(self.oldWaterPumpState):
                # Fan ON
                self.ser.write(("waterPumpH" + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON WATER PUMP.'))
                # print("turning on FAN!")
            else:
                # Fan OFF
                self.ser.write(("waterPumpL" + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF WATER PUMP.'))

            if(self.oldPeltierState):
                # Fan ON
                self.ser.write(("peltierH" + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON PELTIER.'))
                # print("turning on FAN!")
            else:
                # Fan OFF
                self.ser.write(("peltierL" + '\n').encode())
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF PELTIER.'))
            
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
            self.ser = serial.Serial(serial_port, self.baud_rate, timeout=1)
            self.arduino_connected = True
            
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Arduino plugged in: {port}.'))
            print(f"Arduino plugged in: {port}")
            
            self.ser.write(("auto" + '\n').encode())
            self.ref.update({'auto': True})
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON AUTOMATIC.'))
            
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
                    else:
                        # Fan OFF
                        self.ser.write(("fanL" + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF FAN.'))
                        # print("turning off FAN!")

                if(self.currHeaterState != self.oldHeaterState):
                    # update state
                    self.oldHeaterState = self.currHeaterState

                    print("Heater state changed: ", self.currHeaterState)

                    # Change arduino relay heater state
                    if(self.currHeaterState):
                        # Heater ON
                        self.ser.write(('heaterH' + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON HEATER.'))
                    else:
                        # Heater OFF
                        self.ser.write(('heaterL' + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF HEATER.'))

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
                    else:
                        # Fan OFF
                        self.ser.write(("fan2L" + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF FAN2.'))
                        # print("turning off FAN!")

                if(self.currHumidifierState != self.oldHumidifierState):
                    # update state
                    self.oldHumidifierState = self.currHumidifierState

                    print("Humidifier state changed: ", self.currHumidifierState)

                    # Change arduino relay heater state
                    if(self.currHumidifierState):
                        # Humidifier ON
                        self.ser.write(('humidifierH' + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON HUMIDIFIER.'))
                    else:
                        # Humidifier OFF
                        self.ser.write(('humidifierL' + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF HUMIDIFIER.'))

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
                    else:
                        # Auto OFF
                        self.ser.write(("manual" + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF AUTOMATIC.'))
                        # print("turning off FAN!")

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
                    else:
                        # Fan OFF
                        self.ser.write(("waterPumpL" + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning WATER PUMP.'))
                        # print("turning off FAN!")

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
                    else:
                        # Fan OFF
                        self.ser.write(("peltierL" + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF PELTIERN.'))
                        # print("turning off FAN!")

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

                    self.label1.setText("Temperature: <b>{}°C</b>".format(self.jsonData["temperature"]))
                    self.label2.setText("Humidity: <b>{}%</b>".format(self.jsonData["humidity"]))
                    self.label3.setText("CO2: <b>{} PPM</b>".format(self.jsonData["co2ppm"]))
                    self.label4.setText("Water Percentage: <b>{}%</b>".format(self.jsonData["waterLevel"]/19 * 100))
                    self.label5.setText("Water Level: <b>{}</b>".format(self.jsonData["waterLevel"]))

                    if self.check_internet(): # if there is an internet connection
                        try:
                            ref.update({"temp":self.jsonData["temperature"]})
                            ref.update({"humid":self.jsonData["humidity"]})
                            ref.update({"water":self.jsonData["waterLevel"]})
                            ref.update({"co2":self.jsonData["co2ppm"]})

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
                    logging.error(datetime.now().strftime('%m-%d-%Y %H:%M:%S Error: {data}'.format(data=data)))
                    print("Error:", data)
            except serial.serialutil.SerialException as e:
                print(f"SerialException caught: {e}")
                # You might want to mark Arduino as disconnected here
                #arduino_connected = False
                self.ser.close()


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

    # Allow closing with ESC key
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TabButtonLayout()
    sys.exit(app.exec_())
