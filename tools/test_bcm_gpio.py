import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23', timeout=10)

test_code = """
import os
os.environ['JETSON_MODEL_NAME'] = 'JETSON_ORIN_NANO'
import Jetson.GPIO as GPIO

print('Testing BCM pins on Jetson Orin Nano:')
GPIO.setmode(GPIO.BCM)
for p in [12, 16, 18, 23]:
    try:
        GPIO.setup(p, GPIO.OUT)
        print(f'BCM Pin {p}: VALID')
    except Exception as e:
        print(f'BCM Pin {p}: INVALID ({e})')
GPIO.cleanup()
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_bcm.py', 'w') as f:
    f.write(test_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("echo gtaomp23 | sudo -S /home/om/venv/bin/python /tmp/test_bcm.py")
print(stdout.read().decode('utf-8', 'replace'))
print(stderr.read().decode('utf-8', 'replace'))
ssh.close()
