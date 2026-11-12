import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23', timeout=10)

test_code = """
import os
os.environ["JETSON_MODEL_NAME"] = "JETSON_ORIN_NANO"
import Jetson.GPIO as GPIO
import time

print("Initializing all buzzer and strobe candidate pins on 40-pin header...")
GPIO.setmode(GPIO.BOARD)

# Candidate pins:
# 12 (BCM 18 - Buzzer standard)
# 32 (BCM 12 - Buzzer alt)
# 16 (BCM 23 - Strobe standard)
# 36 (BCM 16 - Strobe alt)
pins = [12, 16, 32, 36]

for p in pins:
    try:
        GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)
        print(f"Pin {p} setup OK as OUTPUT LOW")
    except Exception as e:
        print(f"Pin {p} setup error: {e}")

print("\\n[TEST 1] Driving Pin 12 AND Pin 32 HIGH (BUZZER PINS) for 3 seconds...")
GPIO.output(12, GPIO.HIGH)
GPIO.output(32, GPIO.HIGH)
time.sleep(3)
GPIO.output(12, GPIO.LOW)
GPIO.output(32, GPIO.LOW)
print("Buzzer pins returned to LOW.")

time.sleep(1)

print("\\n[TEST 2] Driving Pin 16 AND Pin 36 HIGH (STROBE PINS - Active High) for 3 seconds...")
GPIO.output(16, GPIO.HIGH)
GPIO.output(36, GPIO.HIGH)
time.sleep(3)
GPIO.output(16, GPIO.LOW)
GPIO.output(36, GPIO.LOW)
print("Strobe pins returned to LOW.")

time.sleep(1)

print("\\n[TEST 3] Driving Pin 16 AND Pin 36 LOW (STROBE PINS - Active Low Relay test) for 3 seconds...")
# In active-low, HIGH is off, LOW is ON
GPIO.output(16, GPIO.HIGH)
GPIO.output(36, GPIO.HIGH)
time.sleep(0.5)
print(">>> Sending LOW (Triggering Active-Low Relay)...")
GPIO.output(16, GPIO.LOW)
GPIO.output(36, GPIO.LOW)
time.sleep(3)
GPIO.output(16, GPIO.HIGH)
GPIO.output(36, GPIO.HIGH)
print("Relay test complete.")

GPIO.cleanup()
print("\\nAll tests done.")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_all_pins.py', 'w') as f:
    f.write(test_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("echo gtaomp23 | sudo -S /home/om/venv/bin/python /tmp/test_all_pins.py")
for line in iter(stdout.readline, ""):
    print(line, end="")

ssh.close()

