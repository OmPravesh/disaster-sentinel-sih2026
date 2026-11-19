import time
from jetson_config import get_jetson_ssh

ssh, ip = get_jetson_ssh()
print(f"Connected to Jetson at {ip}")

# Stop sentinel.service during test
ssh.exec_command("echo gtaomp23 | sudo -S systemctl stop sentinel.service")
time.sleep(1)

test_script = """
import spidev
import Jetson.GPIO as GPIO
import time

# 1. Reset SX1278
print("Setting up GPIO...")
GPIO.setmode(GPIO.BOARD)
RST_PIN = 22
DIO0_PIN = 7

try:
    GPIO.setup(RST_PIN, GPIO.OUT, initial=GPIO.HIGH)
    time.sleep(0.05)
    print("Pulling RST LOW (Pin 22)...")
    GPIO.output(RST_PIN, GPIO.LOW)
    time.sleep(0.02)
    print("Releasing RST HIGH (Pin 22)...")
    GPIO.output(RST_PIN, GPIO.HIGH)
    time.sleep(0.05)
except Exception as e:
    print(f"GPIO Error: {e}")

# 2. Test SPI at 500 kHz and 1 MHz
for speed in [250000, 500000, 1000000]:
    for mode in [0, 1]:
        spi = spidev.SpiDev()
        spi.open(0, 0)
        spi.mode = mode
        spi.max_speed_hz = speed
        v = spi.xfer2([0x42 & 0x7F, 0x00])[1]
        op = spi.xfer2([0x01 & 0x7F, 0x00])[1]
        spi.close()
        print(f"Speed={speed:7d} Mode={mode}: Version=0x{v:02X} (Expected: 0x12) OpMode=0x{op:02X}")

# 3. Read DIO0 Pin 7 state
try:
    GPIO.setup(DIO0_PIN, GPIO.IN)
    dio = GPIO.input(DIO0_PIN)
    print(f"DIO0 Pin 7 State: {dio}")
except Exception as e:
    print(f"DIO0 read error: {e}")

GPIO.cleanup()
"""

sftp = ssh.open_sftp()
with sftp.file("/tmp/diag_sx1278.py", "w") as f:
    f.write(test_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("/home/om/venv/bin/python /tmp/diag_sx1278.py")
print("=== DIAGNOSTIC OUTPUT ===")
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print("ERR:", err)

# Restart sentinel.service
ssh.exec_command("echo gtaomp23 | sudo -S systemctl start sentinel.service")
ssh.close()

