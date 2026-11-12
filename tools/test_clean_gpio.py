import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23', timeout=10)

stdin, stdout, stderr = ssh.exec_command("echo gtaomp23 | sudo -S systemctl stop sentinel.service")
stdout.channel.recv_exit_status()
print("Stopped sentinel.service temporarily.")

test_code = """
import os
os.environ["JETSON_MODEL_NAME"] = "JETSON_ORIN_NANO"
import Jetson.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)

print("Attempting to setup Pin 12 (Buzzer) and Pin 16 (Strobe/Relay)...")
try:
    GPIO.setup(12, GPIO.OUT, initial=GPIO.LOW)
    print("SUCCESS: Pin 12 setup OK!")
except Exception as e:
    print(f"FAILED Pin 12: {e}")

try:
    GPIO.setup(16, GPIO.OUT, initial=GPIO.LOW)
    print("SUCCESS: Pin 16 setup OK!")
except Exception as e:
    print(f"FAILED Pin 16: {e}")

print("\\n[TEST 1] TURNING BUZZER (Pin 12) ON FOR 3 SECONDS...")
GPIO.output(12, GPIO.HIGH)
time.sleep(3)
GPIO.output(12, GPIO.LOW)
print("Buzzer OFF.")

print("\\n[TEST 2] TURNING STROBE RELAY (Pin 16) ON (HIGH) FOR 3 SECONDS...")
GPIO.output(16, GPIO.HIGH)
time.sleep(3)
GPIO.output(16, GPIO.LOW)
print("Strobe OFF.")

print("\\n[TEST 3] TESTING RELAY ACTIVE-LOW TRIGGER (LOW = ON) FOR 3 SECONDS...")
GPIO.output(16, GPIO.LOW)
time.sleep(3)
GPIO.output(16, GPIO.HIGH)
print("Active-low test done.")

GPIO.cleanup()
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_clean.py', 'w') as f:
    f.write(test_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("echo gtaomp23 | sudo -S /home/om/venv/bin/python /tmp/test_clean.py")
for line in iter(stdout.readline, ""):
    print(line, end="")

ssh.close()

