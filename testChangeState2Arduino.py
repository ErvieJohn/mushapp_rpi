import serial
import time

# Replace 'COM3' with your Arduino's port
arduino = serial.Serial(port='/dev/ttyACM0', baudrate=9600, timeout=1)

def send_command(command):
    """
    Send a string command to the Arduino.
    :param command: Command string, e.g., 'fanH' for HIGH, 'fanL' for LOW
    """
    try:
        arduino.write((command + '\n').encode())  # Send command with newline
        time.sleep(0.1)                           # Small delay for processing
        response = arduino.readline().decode('utf-8').strip()  # Read response
        print(f"Arduino Response: {response}")
    except Exception as e:
        print(f"Error sending command: {e}")

# Example usage
if __name__ == "__main__":
    time.sleep(2)  # Wait for the connection to establish
    print("Turning Fan ON")
    send_command('fanH')  # Turn Fan ON (HIGH)
    time.sleep(2)
    print("Turning Fan OFF")
    send_command('fanL')  # Turn Fan OFF (LOW)
