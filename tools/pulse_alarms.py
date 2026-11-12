import paramiko
import time
import sys

print("==================================================")
print("  DISASTER SENTINEL — JETSON HARDWARE ALARM TEST")
print("==================================================")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23', timeout=10)

test_script = """
import os
os.environ['JETSON_MODEL_NAME'] = 'JETSON_ORIN_NANO'
import Jetson.GPIO as GPIO
import time

print('[1/2] Testing Physical 40-Pin Header: Pin 12 (Buzzer) & Pin 16 (Relay/Strobe)...')
GPIO.setmode(GPIO.BOARD)

# Setup Pin 12 and Pin 16
GPIO.setup(12, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(16, GPIO.OUT, initial=GPIO.LOW)

print('  >>> Turning BUZZER (Physical Pin 12) ON for 2 seconds...')
GPIO.output(12, GPIO.HIGH)
time.sleep(2)
GPIO.output(12, GPIO.LOW)
print('  >>> Buzzer OFF.')

time.sleep(0.5)

print('  >>> Turning STROBE / RELAY (Physical Pin 16) ON for 3 seconds...')
GPIO.output(16, GPIO.HIGH)
time.sleep(3)
GPIO.output(16, GPIO.LOW)
print('  >>> Strobe / Relay OFF.')

GPIO.cleanup()

print('\\n[2/2] Testing BCM mode: BCM 12 (Physical Pin 32) & BCM 16 (Physical Pin 36)...')
GPIO.setmode(GPIO.BCM)
GPIO.setup(12, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(16, GPIO.OUT, initial=GPIO.LOW)

print('  >>> Pulsing BCM 12 (Pin 32) ON for 1.5 seconds...')
GPIO.output(12, GPIO.HIGH)
time.sleep(1.5)
GPIO.output(12, GPIO.LOW)

print('  >>> Pulsing BCM 16 (Pin 36) ON for 1.5 seconds...')
GPIO.output(16, GPIO.HIGH)
time.sleep(1.5)
GPIO.output(16, GPIO.LOW)

GPIO.cleanup()
print('\\n✅ All Hardware Pin Pulses Completed Successfully!')
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/pulse_alarms.py', 'w') as f:
    f.write(test_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("echo gtaomp23 | sudo -S /home/om/venv/bin/python /tmp/pulse_alarms.py")
for line in iter(stdout.readline, ""):
    print(line, end="")

ssh.close()

