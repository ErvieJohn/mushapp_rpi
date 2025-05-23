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

connection = pymysql.connect(
    host="localhost",         # Replace with your host, e.g., "127.0.0.1" or server IP
    user="admin",     # Replace with your MariaDB username
    password="admin", # Replace with your MariaDB password
    database="mushapp_db", # Replace with your database name
    charset="utf8mb4",        # Character set for encoding
    cursorclass=pymysql.cursors.DictCursor  # Optional: Use dictionary cursor for better usability
)

cursor = connection.cursor()
##########################################


LOG_FILENAME = datetime.now().strftime('/home/admin/Desktop/main/logs/%d_%m_%Y_logfile.log') # %H_%M_%S_logfile.log')

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
#logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)
logging.basicConfig(filename=LOG_FILENAME,level=logging.INFO)
logging.info('Forecasting Job Started...')
logging.debug('mushapp method started...')
########### CHECKING INTERNET ###############
# logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Checking Internet Connection...'))
# print("Checking Internet Connection...")

def check_internet():
    try:
        requests.get("https://www.google.com")
        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Connected to Internet.'))
        return True
    except requests.ConnectionError:
        logging.error(datetime.now().strftime('%m-%d-%Y %H:%M:%S Error Connecting to Internet.'))
        return False


# if check_internet():
#     logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Checking Internet Connection again...'))
#     print("Checking Internet Connection again...")

#     print("Connected to Internet.")
########### CHECKING INTERNET ###############

########## Finding Serial Port ##############
logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Connecting to Arduino Serial Port...'))
print("Connecting to Arduino Serial Port...")

def list_serial_ports():
    return [port.device for port in serial.tools.list_ports.comports()]

known_ports = set(list_serial_ports())


def find_available_port():
    # List all available ports
    serial_port = list(serial.tools.list_ports.comports())
    for port in serial_port:
        # You can add criteria to select a specific port if needed
        print(f"Found port: {port.device}")
        return port.device
    return None

# Define the serial port
# serial_port = '/dev/ttyUSB0'  # Change this to match your Arduino's serial port
#serial_port = '/dev/ttyACM0'
#serial_port = '/dev/ttyAMA0'

serial_port = find_available_port()
while serial_port is None:
    logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Error: No Serial Port Available.'))
    print("Error: No Serial Port Available.")
    sys.exit("No Serial Port Available.")

    # Wait for a moment
    time.sleep(1)

    serial_port = find_available_port()
#if (serial_port is None):

# Define the baud rate
baud_rate = 9600

# Open the serial port
ser = serial.Serial(serial_port, baud_rate, timeout=1)
arduino_connected = True

logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Connected to Arduino Serial Port.'))
print("Done.")
########## Finding Serial Port ##############

cred = credentials.Certificate("/home/admin/Desktop/main/key.json")
initialized = False
def connectToFirebase():
    global initialized
    ########## Checking Firebase ##############
    if(not initialized):
        try:
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Connecting to Firebase Realtime Database...'))
            print("Connecting to Firebase Realtime Database...")

            # Initialize Firebase Admin SDK with your service account credentials
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://mushapp-c0311-default-rtdb.firebaseio.com/'
            })
            initialized = True

            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Connected to Firebase Realtime Database.'))
            print("Done.")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
    # Reference to the specific path in the Firebase Realtime Database

    return db.reference('/')
    ########## Checking Firebase ##############


try:
    # Initial Value
    oldFanState = False
    oldHeaterState = False

    oldFan2State = False
    oldHumidifierState = False

    oldWaterPumpState = False

    oldAutoState = True

    oldPeltierState = False

    if check_internet():
        ref = connectToFirebase()

        # Get the data
        oldData = ref.get()
        oldFanState = oldData["fan"]
        oldHeaterState = oldData["heater"]

        oldFan2State = oldData["fan2"]
        oldHumidifierState = oldData["humidifier"]

        oldWaterPumpState = oldData["waterPump"]

        #oldAutoState = oldData["auto"]
        oldAutoState = True

        oldPeltierState = oldData["peltier"]

    oldDateTime = datetime.now()

    # First Run change current state
    # Change arduino relay fan state
    if(oldFanState):
        # Fan ON
        ser.write(("fanH" + '\n').encode())
        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON FAN.'))
        # print("turning on FAN!")
    else:
        # Fan OFF
        ser.write(("fanL" + '\n').encode())
        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF FAN.'))

    # Change arduino relay heater state
    if(oldHeaterState):
        # Heater ON
        ser.write(('heaterH' + '\n').encode())
        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON HEATER.'))
    else:
        # Heater OFF
        ser.write(('heaterL' + '\n').encode())
        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF HEATER.'))

    if(oldFan2State):
        # Fan ON
        ser.write(("fan2H" + '\n').encode())
        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON FAN2.'))
        # print("turning on FAN!")
    else:
        # Fan OFF
        ser.write(("fan2L" + '\n').encode())
        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF FAN2.'))

    # Change arduino relay heater state
    if(oldHumidifierState):
        # Heater ON
        ser.write(('humidifierH' + '\n').encode())
        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON HUMIDIFIER.'))
    else:
        # Heater OFF
        ser.write(('humidifierL' + '\n').encode())
        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF HUMIDIFIER.'))

    # Change arduino relay heater state
    if(oldAutoState):
        # Heater ON
        ser.write(('auto' + '\n').encode())
        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON AUTOMATIC.'))
        ref.update({'auto': True})
    else:
        # Heater OFF
        ser.write(('manual' + '\n').encode())
        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF AUTOMATIC.'))

    if(oldWaterPumpState):
        # Fan ON
        ser.write(("waterPumpH" + '\n').encode())
        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON WATER PUMP.'))
        # print("turning on FAN!")
    else:
        # Fan OFF
        ser.write(("waterPumpL" + '\n').encode())
        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF WATER PUMP.'))

    if(oldPeltierState):
        # Fan ON
        ser.write(("peltierH" + '\n').encode())
        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON PELTIER.'))
        # print("turning on FAN!")
    else:
        # Fan OFF
        ser.write(("peltierL" + '\n').encode())
        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF PELTIER.'))

    while True:
        # for detection of plugged/unplugged arduino port
        current_ports = set(list_serial_ports())

        # Detect new ports
        new_ports = current_ports - known_ports
        for port in new_ports:
            serial_port = find_available_port()
            while serial_port is None:
                logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Error: No Serial Port Available.'))
                print("Error: No Serial Port Available.")
                sys.exit("No Serial Port Available.")

                # Wait for a moment
                time.sleep(1)

                serial_port = find_available_port()
            #if (serial_port is None):

            # Define the baud rate
            baud_rate = 9600

            # Open the serial port
            ser = serial.Serial(serial_port, baud_rate, timeout=1)
            arduino_connected = True
            
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Arduino plugged in: {port}.'))
            print(f"Arduino plugged in: {port}")
            
            ser.write(("auto" + '\n').encode())
            ref.update({'auto': True})
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON AUTOMATIC.'))
            
        # Detect removed ports
        removed_ports = known_ports - current_ports
        for port in removed_ports:
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Arduino unplugged: {port}.'))
            print(f"Arduino unplugged: {port}")
            
            serial_port = None
            arduino_connected = False
            ser.close()
            
        known_ports = current_ports

        if arduino_connected:
            #try:
            if check_internet():
                ref = connectToFirebase()

                # Get the data
                currData = ref.get()
                currFanState = currData["fan"]
                currHeaterState = currData["heater"]

                currFan2State = currData["fan2"]
                currHumidifierState = currData["humidifier"]

                currWaterPumpState = currData["waterPump"]

                currAutoState = currData["auto"]

                currPeltierState = currData["peltier"]

                if(currFanState != oldFanState):
                    # update state
                    oldFanState = currFanState

                    print("Fan state changed: ", currFanState)

                    # Change arduino relay fan state
                    if(currFanState):
                        # Fan ON
                        ser.write(("fanH" + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON FAN.'))
                        # print("turning on FAN!")
                    else:
                        # Fan OFF
                        ser.write(("fanL" + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF FAN.'))
                        # print("turning off FAN!")

                if(currHeaterState != oldHeaterState):
                    # update state
                    oldHeaterState = currHeaterState

                    print("Heater state changed: ", currHeaterState)

                    # Change arduino relay heater state
                    if(currHeaterState):
                        # Heater ON
                        ser.write(('heaterH' + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON HEATER.'))
                    else:
                        # Heater OFF
                        ser.write(('heaterL' + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF HEATER.'))

                if(currFan2State != oldFan2State):
                    # update state
                    oldFan2State = currFan2State

                    print("Fan2 state changed: ", currFan2State)

                    # Change arduino relay fan state
                    if(currFan2State):
                        # Fan ON
                        ser.write(("fan2H" + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON FAN2.'))
                        # print("turning on FAN!")
                    else:
                        # Fan OFF
                        ser.write(("fan2L" + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF FAN2.'))
                        # print("turning off FAN!")

                if(currHumidifierState != oldHumidifierState):
                    # update state
                    oldHumidifierState = currHumidifierState

                    print("Humidifier state changed: ", currHumidifierState)

                    # Change arduino relay heater state
                    if(currHumidifierState):
                        # Humidifier ON
                        ser.write(('humidifierH' + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON HUMIDIFIER.'))
                    else:
                        # Humidifier OFF
                        ser.write(('humidifierL' + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF HUMIDIFIER.'))

                if(currAutoState != oldAutoState):
                    # update state
                    oldAutoState = currAutoState

                    print("Auto state changed: ", currAutoState)

                    # Change arduino relay fan state
                    if(currAutoState):
                        # Auto ON
                        ser.write(("auto" + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON AUTOMATIC.'))
                        # print("turning on FAN!")
                    else:
                        # Auto OFF
                        ser.write(("manual" + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF AUTOMATIC.'))
                        # print("turning off FAN!")

                if(currWaterPumpState != oldWaterPumpState):
                    # update state
                    oldWaterPumpState = currWaterPumpState

                    print("Water Pump state changed: ", currWaterPumpState)

                    # Change arduino relay fan state
                    if(currWaterPumpState):
                        # Fan ON
                        ser.write(("waterPumpH" + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON WATER PUMP.'))
                        # print("turning on FAN!")
                    else:
                        # Fan OFF
                        ser.write(("waterPumpL" + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning WATER PUMP.'))
                        # print("turning off FAN!")

                if(currPeltierState != oldPeltierState):
                    # update state
                    oldPeltierState = currPeltierState

                    print("Peltier state changed: ", currPeltierState)

                    # Change arduino relay fan state
                    if(currPeltierState):
                        # Fan ON
                        ser.write(("peltierH" + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning ON PELTIER.'))
                        # print("turning on FAN!")
                    else:
                        # Fan OFF
                        ser.write(("peltierL" + '\n').encode())
                        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Turning OFF PELTIERN.'))
                        # print("turning off FAN!")

            # Read a line of data from the serial port
            try:
                data = ser.readline().decode('utf-8', errors='ignore').strip()
                
                if(data[slice(10)] == "JSON data:"):
                    try:
                        jsonData = json.loads(data[10:None])
                    except Exception as e:
                        logging.error(datetime.now().strftime('%m-%d-%Y %H:%M:%S Unexpected error: {str(e)}'))
                        print(f"Unexpected error: {str(e)}")
                        jsonData = {"temperature": 0, "humidity": 0, "waterLevel": 0, "co2ppm": 0}

                    logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Data Collected: {data}'.format(data=jsonData)))
                    print(jsonData)

                    # update the firebase realtime database
                    # update the temp
                    logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Sending data to firebase realtime database...'))
                    print("Sending data to firebase realtime database...")

                    if check_internet(): # if there is an internet connection
                        try:
                            ref.update({"temp":jsonData["temperature"]})
                            ref.update({"humid":jsonData["humidity"]})
                            ref.update({"water":jsonData["waterLevel"]})
                            ref.update({"co2":jsonData["co2ppm"]})

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
                    timeDiff = datetime.now() - oldDateTime

                    # saved only per minute
                    if(timeDiff.total_seconds() > 60):
                        insert_query = """
                            INSERT INTO data (co2, humidity, temperature, water_lvl)
                            VALUES (%s, %s, %s, %s)
                        """
                        data = (jsonData["co2ppm"], jsonData["humidity"], jsonData["temperature"], jsonData["waterLevel"])

                        try:
                            cursor.execute(insert_query, data)
                            connection.commit()  # Commit changes to the database
                            # print(f"Inserted {cursor.rowcount} row(s) successfully.")

                            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Data has been saved to local database.'))
                            print("Data has been saved to local database.")

                            oldDateTime = datetime.now()

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
                ser.close()
            
            
                
        # Wait for a moment
        time.sleep(1)

except KeyboardInterrupt:
    # Close the serial port when the program is terminated
    ser.close()

    # database close connection
    cursor.close()
    connection.close()
