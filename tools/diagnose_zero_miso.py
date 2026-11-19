import time
from jetson_config import get_jetson_ssh

ssh, ip = get_jetson_ssh()
print(f"Connected to Jetson at {ip}")

# Stop sentinel.service
ssh.exec_command("echo gtaomp23 | sudo -S systemctl stop sentinel.service")
time.sleep(1)

test_code = r'''import spidev
import Jetson.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)
RST_PIN = 22
DIO0_PIN = 7
CS_PIN = 24

print("--- 1. Testing with RST explicitly HIGH (3.3V) ---")
try:
    GPIO.setup(RST_PIN, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.output(RST_PIN, GPIO.HIGH)
    time.sleep(0.05)
except Exception as e:
    print(f"GPIO RST error: {e}")

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 500000
spi.mode = 0

for i in range(5):
    v = spi.xfer2([0x42 & 0x7F, 0x00])[1]
    print(f"RST=HIGH -> Version (0x42): 0x{v:02X}")
    time.sleep(0.02)

print("--- 2. Pulsing RST: LOW for 10ms -> HIGH for 50ms ---")
GPIO.output(RST_PIN, GPIO.LOW)
time.sleep(0.02)
GPIO.output(RST_PIN, GPIO.HIGH)
time.sleep(0.05)

for i in range(5):
    v = spi.xfer2([0x42 & 0x7F, 0x00])[1]
    print(f"Post-Reset -> Version (0x42): 0x{v:02X}")
    time.sleep(0.02)

print("--- 3. Testing with Manual GPIO CS (Pin 24) ---")
spi.close()

try:
    GPIO.setup(CS_PIN, GPIO.OUT, initial=GPIO.HIGH)
    
    spi_no_cs = spidev.SpiDev()
    spi_no_cs.open(0, 0)
    spi_no_cs.no_cs = True
    spi_no_cs.max_speed_hz = 500000
    spi_no_cs.mode = 0
    
    GPIO.output(CS_PIN, GPIO.LOW)
    time.sleep(0.001)
    res = spi_no_cs.xfer2([0x42 & 0x7F, 0x00])
    GPIO.output(CS_PIN, GPIO.HIGH)
    print(f"Manual CS -> Version (0x42): 0x{res[1]:02X}")
    spi_no_cs.close()
except Exception as e:
    print(f"Manual CS error: {e}")

try:
    GPIO.setup(DIO0_PIN, GPIO.IN)
    print(f"DIO0 Pin 7 level: {GPIO.input(DIO0_PIN)}")
except Exception as e:
    print(f"DIO0 error: {e}")

GPIO.cleanup()
'''

sftp = ssh.open_sftp()
with sftp.file("/tmp/diag_zero.py", "w") as f:
    f.write(test_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("/home/om/venv/bin/python /tmp/diag_zero.py")
print("=== DIAGNOSTIC OUTPUT ===")
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print("ERR:", err)

# Restart sentinel.service
ssh.exec_command("echo gtaomp23 | sudo -S systemctl start sentinel.service")
ssh.close()
