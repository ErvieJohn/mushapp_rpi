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

LOG_FILENAME = datetime.now().strftime('/home/admin/Desktop/main/logs/%d_%m_%Y_logfile.log') # %H_%M_%S_logfile.log')

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)    
logging.info('Forecasting Job Started...')
logging.debug('mushapp method started...')

logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Connecting to Arduino Serial Port...'))
print("Connecting to Arduino Serial Port...")

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
if (serial_port is None):
    logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Error: No Serial Port Available.'))
    print("Error: No Serial Port Available.")
    sys.exit("No Serial Port Available.")


# Define the baud rate
baud_rate = 9600

# Open the serial port
ser = serial.Serial(serial_port, baud_rate, timeout=1)

logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Connected to Arduino Serial Port.'))
print("Done.")

logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Connecting to Firebase Realtime Database...'))
print("Connecting to Firebase Realtime Database...")
# Initialize Firebase Admin SDK with your service account credentials
cred = credentials.Certificate("/home/admin/Desktop/main/key.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://mushapp-c0311-default-rtdb.firebaseio.com/'
})

# Reference to the specific path in the Firebase Realtime Database
ref = db.reference('/')

logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Connected to Firebase Realtime Database.'))
print("Done.")

def check_internet():
    try:
        requests.get("https://www.google.com")
        logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Connected to Internet.'))
        return True
    except requests.ConnectionError:
        logging.error(datetime.now().strftime('%m-%d-%Y %H:%M:%S Error Connecting to Internet.'))
        return False

try:
    # Get the data
    oldData = ref.get()
    oldFanState = oldData["fan"]
    oldHeaterState = oldData["heater"]
    
    while True:
        # Get the data
        currData = ref.get()
        currFanState = currData["fan"]
        currHeaterState = currData["heater"]
        
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
                
        # Read a line of data from the serial port
        data = ser.readline().decode().strip()
    
        if(data[slice(10)] == "JSON data:"):
            jsonData = json.loads(data[10:None])
            
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Data Collected: {data}'.format(data=jsonData)))
            print(jsonData)
            
            # update the firebase realtime database
            # update the temp
            logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Sending data to firebase realtime database...'))
            print("Sending data to firebase realtime database...")
            while True:
                if check_internet(): # if there is an internet connection
                    ref.update({"temp":jsonData["temperature"]})
                    ref.update({"humid":jsonData["humidity"]})
                    ref.update({"water":jsonData["waterLevel"]})
                    ref.update({"co2":jsonData["co2ppm"]})
                    
                    logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Data has been sent to firebase realtime database.'))
                    print("Data has been sent to firebase realtime database.")
                   
                    # to stop the loop for checking the internet
                    break
                
                else:
                    logging.error(datetime.now().strftime('%m-%d-%Y %H:%M:%S No Internet Connection.'))
                    print("No Internet Connection")
            
                # Wait for a moment
                time.sleep(1)
        else:
            logging.error(datetime.now().strftime('%m-%d-%Y %H:%M:%S Error: {data}'.format(data=data)))
            print("Error:", data)
                
        # Wait for a moment
        time.sleep(1)
        
except KeyboardInterrupt:
    # Close the serial port when the program is terminated
    ser.close()
