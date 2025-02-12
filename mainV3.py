import serial
import time
import json
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
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)    
logging.info('Forecasting Job Started...')
logging.debug('mushapp method started...')


########## Finding Serial Port ##############
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

logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Connected to Arduino Serial Port.'))
print("Done.")
########## Finding Serial Port ##############

try:
    oldDateTime = datetime.now()
    
    while True:
        # Read a line of data from the serial port
        data = ser.readline().decode().strip()
        
        if(data[slice(10)] == "JSON data:"):
            jsonData = json.loads(data[10:None])
            
            # logging.info(datetime.now().strftime('%m-%d-%Y %H:%M:%S Data Collected: {data}'.format(data=jsonData)))
            print(jsonData)
    
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
                
        # Wait for a moment
        time.sleep(1)
    
except KeyboardInterrupt:
    # Close the serial port when the program is terminated
    ser.close()

    # database close connection
    cursor.close()
    connection.close()
