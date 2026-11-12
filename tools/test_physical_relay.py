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

GPIO.setmode(GPIO.BOARD)

GPIO.setup(12, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(16, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(32, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(36, GPIO.OUT, initial=GPIO.LOW)

print(">>> [TEST A] Setting Buzzer (Pin 12 & 32) HIGH for 4 seconds...")
GPIO.output(12, GPIO.HIGH)
GPIO.output(32, GPIO.HIGH)
time.sleep(4)
GPIO.output(12, GPIO.LOW)
GPIO.output(32, GPIO.LOW)
print(">>> Buzzer test finished.")

time.sleep(1)

print(">>> [TEST B] Setting Strobe Relay (Pin 16 & 36) HIGH (Active-HIGH trigger) for 4 seconds...")
GPIO.output(16, GPIO.HIGH)
GPIO.output(36, GPIO.HIGH)
time.sleep(4)
GPIO.output(16, GPIO.LOW)
GPIO.output(36, GPIO.LOW)
print(">>> Strobe HIGH test finished.")

time.sleep(1)

print(">>> [TEST C] Setting Strobe Relay (Pin 16 & 36) LOW (Active-LOW trigger) for 4 seconds...")
GPIO.output(16, GPIO.HIGH)
GPIO.output(36, GPIO.HIGH)
time.sleep(0.5)
GPIO.output(16, GPIO.LOW)
GPIO.output(36, GPIO.LOW)
time.sleep(4)
GPIO.output(16, GPIO.HIGH)
GPIO.output(36, GPIO.HIGH)
print(">>> Strobe LOW test finished.")

GPIO.cleanup()
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_relay_live.py', 'w') as f:
    f.write(test_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("echo gtaomp23 | sudo -S /home/om/venv/bin/python /tmp/test_relay_live.py")
for line in iter(stdout.readline, ""):
    print(line, end="")

ssh.close()

