import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23', timeout=10)

test_code = """
import os
os.environ["JETSON_MODEL_NAME"] = "JETSON_ORIN_NANO"
import Jetson.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)

GPIO.setup(16, GPIO.OUT)
GPIO.output(16, GPIO.HIGH)
val_high = GPIO.input(16)
print("Pin 16 output HIGH -> input reads:", val_high)

GPIO.output(16, GPIO.LOW)
val_low = GPIO.input(16)
print("Pin 16 output LOW -> input reads:", val_low)

GPIO.cleanup()
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_pin16_readback.py', 'w') as f:
    f.write(test_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("echo gtaomp23 | sudo -S /home/om/venv/bin/python /tmp/test_pin16_readback.py")
print(stdout.read().decode('utf-8', 'replace'))
print(stderr.read().decode('utf-8', 'replace'))

ssh.close()

