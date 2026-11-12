import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23', timeout=10)

check_script = """
import os
os.environ["JETSON_MODEL_NAME"] = "JETSON_ORIN_NANO"
import Jetson.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
print("=== Current GPIO.BOARD Pin States ===")
for p in [12, 16, 18, 22, 23, 32, 36]:
    try:
        # read current direction / value
        val = GPIO.gpio_function(p)
        print(f"Pin {p} mode: {val}")
    except Exception as e:
        print(f"Pin {p}: {e}")
"""

stdin, stdout, stderr = ssh.exec_command(f"/home/om/venv/bin/python -c '{check_script}'")
print(stdout.read().decode('utf-8', 'replace'))
print(stderr.read().decode('utf-8', 'replace'))

ssh.close()

