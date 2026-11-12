import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23', timeout=10)

test_code = """
import os
os.environ["JETSON_MODEL_NAME"] = "JETSON_ORIN_NANO"
import Jetson.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)

# Stop sentinel.service to test in complete isolation
os.system("echo gtaomp23 | sudo -S systemctl stop sentinel.service")

GPIO.setup(12, GPIO.OUT)
GPIO.output(12, GPIO.HIGH)
val_high = GPIO.input(12)
print("Pin 12 output HIGH -> input reads:", val_high)

GPIO.output(12, GPIO.LOW)
val_low = GPIO.input(12)
print("Pin 12 output LOW -> input reads:", val_low)

GPIO.cleanup()
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_pin12_readback.py', 'w') as f:
    f.write(test_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("echo gtaomp23 | sudo -S /home/om/venv/bin/python /tmp/test_pin12_readback.py")
print(stdout.read().decode('utf-8', 'replace'))
print(stderr.read().decode('utf-8', 'replace'))

ssh.close()

