import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23', timeout=10)

test_code = """
import os
os.environ["JETSON_MODEL_NAME"] = "JETSON_ORIN_NANO"
import Jetson.GPIO as GPIO

# In Jetson.GPIO, if another process has exported the pin, we can read its sysfs value!
try:
    with open('/sys/class/gpio/PR.00/value', 'r') as f:
        print('PR.00 (Pin 12) sysfs value:', f.read().strip())
except Exception as e:
    print('sysfs read error:', e)
"""

stdin, stdout, stderr = ssh.exec_command(f"/home/om/venv/bin/python -c \"{test_code}\"")
print(stdout.read().decode('utf-8', 'replace'))
print(stderr.read().decode('utf-8', 'replace'))

ssh.close()
