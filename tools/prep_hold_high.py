import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23', timeout=10)

test_code = """
import os
os.environ["JETSON_MODEL_NAME"] = "JETSON_ORIN_NANO"
import Jetson.GPIO as GPIO
import time

# Stop sentinel.service so we can do a 100% direct hardware test!
os.system("echo gtaomp23 | sudo -S systemctl stop sentinel.service")

GPIO.setmode(GPIO.BOARD)
GPIO.setup(12, GPIO.OUT)

print("FORCE DRIVING PIN 12 TO HIGH (3.3V)...")
GPIO.output(12, GPIO.HIGH)

# Keep it HIGH for 60 seconds so user can measure with multimeter!
print("Pin 12 is now HIGH for 60 seconds! Measuring...")
for i in range(12):
    val = GPIO.input(12)
    print(f"Time {i*5}s: readback={val}")
    time.sleep(5)

GPIO.output(12, GPIO.LOW)
GPIO.cleanup()
print("Pin 12 set back to LOW.")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/hold_pin12_high.py', 'w') as f:
    f.write(test_code)
sftp.close()

ssh.close()
print("Created /tmp/hold_pin12_high.py")

