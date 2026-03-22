import serial
import sys

# Adjust the port for your system:
# Windows: 'COM3', 'COM4', etc.
# Mac: '/dev/tty.usbmodem*' or '/dev/cu.usbmodem*'
# Linux: '/dev/ttyACM0' or '/dev/ttyUSB0'

PORT = 'COM7'  # Change this to match your port
BAUD_RATE = 115200
RECORDING_SIZE = 176400

try:
    ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
    print(f"Connected to {PORT}")
    
    # Wait for START signal
    while True:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line == "START":
            print("Recording started...")
            break
    
    # Collect audio data
    audio_data = bytearray()
    
    while len(audio_data) < RECORDING_SIZE:
        chunk = ser.read(RECORDING_SIZE - len(audio_data))
        if chunk:
            audio_data.extend(chunk)
            print(f"Received {len(audio_data)}/{RECORDING_SIZE} bytes", end='\r')
    
    # Save to file
    with open('recording.raw', 'wb') as f:
        f.write(audio_data)
    
    print(f"\nSaved {len(audio_data)} bytes to recording.raw")
    
    ser.close()

except serial.SerialException as e:
    print(f"Error: {e}")
    print("\nAvailable ports:")
    import serial.tools.list_ports
    ports = serial.tools.list_ports.comports()
    for port in ports:
        print(f"  {port.device}")
except KeyboardInterrupt:
    print("\nInterrupted by user")
    ser.close()