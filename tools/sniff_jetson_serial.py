import serial
import time
import glob

ports = glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")
print(f"Found ports: {ports}")

for port in ports:
    print(f"\n--- Checking {port} at 115200 baud ---")
    try:
        ser = serial.Serial(port, 115200, timeout=2.5)
        time.sleep(0.5)
        lines = []
        start = time.time()
        while time.time() - start < 3.0 and len(lines) < 6:
            line = ser.readline().decode('utf-8', 'replace').strip()
            if line:
                lines.append(line)
        ser.close()
        if lines:
            for l in lines:
                print(f"[{port}] {l}")
        else:
            print(f"[{port}] No data received within 3s")
    except Exception as e:
        print(f"[{port}] Error: {e}")

