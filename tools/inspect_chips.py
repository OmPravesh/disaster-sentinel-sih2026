import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23', timeout=10)

stdin, stdout, stderr = ssh.exec_command("""
/home/om/venv/bin/python - << 'EOF'
import os
os.environ["JETSON_MODEL_NAME"] = "JETSON_ORIN_NANO"
import Jetson.GPIO as GPIO
data = GPIO.gpio_pin_data.get_data()
ch = data[2]['BOARD'][12]
print("Pin 12 vars:", vars(ch))
ch16 = data[2]['BOARD'][16]
print("Pin 16 vars:", vars(ch16))
EOF
""")

print(stdout.read().decode('utf-8', 'replace'))
print(stderr.read().decode('utf-8', 'replace'))
ssh.close()
