import serial.tools.list_ports
import time

def list_serial_ports():
    return [port.device for port in serial.tools.list_ports.comports()]

known_ports = set(list_serial_ports())

print("Monitoring serial ports. Press Ctrl+C to stop.")

try:
    while True:
        current_ports = set(list_serial_ports())
        print("current_ports: ", current_ports)
        # Detect new ports
        new_ports = current_ports - known_ports
        for port in new_ports:
            print(f"🔌 Device plugged in: {port}")

        # Detect removed ports
        removed_ports = known_ports - current_ports
        for port in removed_ports:
            print(f"❌ Device unplugged: {port}")

        known_ports = current_ports
        time.sleep(1)

except KeyboardInterrupt:
    print("\nStopped.")

